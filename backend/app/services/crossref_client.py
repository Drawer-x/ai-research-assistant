"""Canonical, rate-limited Crossref Public REST API client."""
from collections import OrderedDict
from html import unescape
from html.parser import HTMLParser
import threading
import time
from urllib.parse import quote

import requests
from app.core.config import settings

SELECT = "DOI,title,abstract,author,published-print,published-online,published,issued,created,container-title,event,URL,link,is-referenced-by-count,references-count,reference,license,subject,type"

class CrossrefError(RuntimeError): pass
class CrossrefNotFound(CrossrefError): pass
class RateLimitedError(CrossrefError): pass
class UpstreamUnavailableError(CrossrefError): pass
class UpstreamTimeoutError(CrossrefError): pass
class InvalidUpstreamResponseError(CrossrefError): pass

def canonicalize_doi(value):
    value = str(value or "").strip()
    lower = value.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "https://dx.doi.org/", "doi:"):
        if lower.startswith(prefix): value = value[len(prefix):].strip(); break
    return value.lower() or None

normalize_doi = canonicalize_doi
def normalize_title(value): return " ".join(str(value or "").split())

class _Text(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self, data): self.parts.append(data)

def _plain_text(value):
    if not isinstance(value, str): return None
    parser=_Text()
    try: parser.feed(unescape(value)); parser.close()
    except Exception: return None
    text=normalize_title(" ".join(parser.parts))
    return text or None

def _date(raw):
    for key in ("published-print","published-online","published","issued","created"):
        value=raw.get(key)
        parts=value.get("date-parts") if isinstance(value,dict) else None
        part=parts[0] if isinstance(parts,list) and parts and isinstance(parts[0],list) else []
        if part and isinstance(part[0],int):
            return "-".join([f"{part[0]:04d}"] + ([f"{part[1]:02d}"] if len(part)>1 else []) + ([f"{part[2]:02d}"] if len(part)>2 else []))
    return None

def _is_oa(raw):
    licenses=raw.get("license") if isinstance(raw.get("license"),list) else []
    urls=" ".join(str(x.get("URL") or "").lower() for x in licenses if isinstance(x,dict))
    if any(x in urls for x in ("creativecommons.org/", "open-access", "free-to-read")): return True
    return any(isinstance(x,dict) and str(x.get("intended-application","")).lower() in {"text-mining","similarity-checking"} and "creativecommons.org/" in str(x.get("URL","")).lower() for x in licenses)

def normalize_crossref_work(raw):
    raw=raw if isinstance(raw,dict) else {}; doi=canonicalize_doi(raw.get("DOI"))
    titles=raw.get("title") if isinstance(raw.get("title"),list) else []
    authors=[]
    for a in raw.get("author",[]) if isinstance(raw.get("author"),list) else []:
        if not isinstance(a,dict): continue
        name=normalize_title(" ".join(x for x in (str(a.get("given") or ""),str(a.get("family") or a.get("name") or "")) if x))
        if name: authors.append({"author_id":str(a.get("ORCID") or "").removeprefix("https://orcid.org/") or None,"name":name})
    venue=((raw.get("container-title") or [None])[0] if isinstance(raw.get("container-title"),list) else None) or ((raw.get("event") or {}).get("name") if isinstance(raw.get("event"),dict) else None)
    links=raw.get("link") if isinstance(raw.get("link"),list) else []
    pdf=next((x.get("URL") for x in links if isinstance(x,dict) and str(x.get("content-type","")).lower()=="application/pdf" and x.get("URL")),None)
    pubdate=_date(raw); refs=raw.get("reference") if isinstance(raw.get("reference"),list) else []
    subjects=raw.get("subject") if isinstance(raw.get("subject"),list) else []
    count=raw.get("reference-count",raw.get("references-count"))
    return {"provider":"crossref","external_id":doi or "","title":normalize_title(titles[0] if titles else "") or "Untitled","abstract":_plain_text(raw.get("abstract")),"authors":authors,"year":int(pubdate[:4]) if pubdate else None,"venue":normalize_title(venue) or None,"doi":doi,"arxiv_id":None,"external_url":raw.get("URL") if isinstance(raw.get("URL"),str) else (f"https://doi.org/{doi}" if doi else None),"pdf_url":pdf,"citation_count":raw.get("is-referenced-by-count") if isinstance(raw.get("is-referenced-by-count"),int) else 0,"reference_count":count if isinstance(count,int) else len(refs),"fields_of_study":[str(x) for x in subjects if isinstance(x,str)],"publication_date":pubdate,"is_open_access":_is_oa(raw),"is_imported":False,"local_paper_id":None}

class CrossrefClient:
    _lock=threading.Lock(); _last_request=0.0; _cache=OrderedDict(); _cache_max=256
    def __init__(self,session=None): self.session=session or requests.Session()
    @classmethod
    def clear_cache(cls):
        with cls._lock: cls._cache.clear()
    def _headers(self):
        mail=str(settings.crossref_mailto or "").strip(); ua="AIResearchAssistant/1.0"+(f" (mailto:{mail})" if mail else "")
        return {"Accept":"application/json","User-Agent":ua}
    def _request(self,path,params=None,cache_ttl=None):
        params=dict(params or {}); mail=str(settings.crossref_mailto or "").strip()
        if mail: params["mailto"]=mail
        url=settings.crossref_base_url.rstrip("/")+path; key=(url,tuple(sorted(params.items()))); now=time.monotonic()
        with self._lock:
            cached=self._cache.get(key)
            if cached and cached[0]>now: return cached[1]
            if cached: del self._cache[key]
        attempts=max(0,min(int(settings.crossref_max_retries),5))+1
        for attempt in range(attempts):
            with self._lock:
                delay=float(settings.crossref_min_request_interval_seconds)-(time.monotonic()-self.__class__._last_request)
                if delay>0: time.sleep(delay)
                self.__class__._last_request=time.monotonic()
            try: response=self.session.get(url,params=params,headers=self._headers(),timeout=(settings.crossref_connect_timeout_seconds,settings.crossref_read_timeout_seconds))
            except requests.Timeout as exc:
                if attempt+1<attempts: continue
                raise UpstreamTimeoutError("Crossref timed out") from exc
            except requests.RequestException as exc:
                if attempt+1<attempts: continue
                raise UpstreamUnavailableError("Crossref unavailable") from exc
            if response.status_code==404: raise CrossrefNotFound("External paper not found")
            if response.status_code==429 or response.status_code>=500:
                if attempt+1<attempts:
                    try: time.sleep(min(max(float(response.headers.get("Retry-After","0")),0),5))
                    except ValueError: pass
                    continue
                if response.status_code==429: raise RateLimitedError("Crossref rate limited")
                raise UpstreamUnavailableError("Crossref unavailable")
            if response.status_code>=400: raise CrossrefError("Crossref request failed")
            try: data=response.json()
            except (ValueError,TypeError) as exc: raise InvalidUpstreamResponseError("Invalid Crossref response") from exc
            if not isinstance(data,dict) or not isinstance(data.get("message"),dict): raise InvalidUpstreamResponseError("Invalid Crossref response")
            ttl=settings.crossref_cache_ttl_seconds if cache_ttl is None else cache_ttl
            if ttl:
                with self._lock: self._cache[key]=(time.monotonic()+float(ttl),data)
            return data
        raise UpstreamUnavailableError("Crossref unavailable")
    def search_works(self,query,year_from=None,year_to=None,open_access=None,page=1,page_size=20):
        query=normalize_title(query)
        if not query or page<1 or not 1<=page_size<=100: raise ValueError("invalid search parameters")
        requested=min(100,page_size*3) if open_access is True else page_size
        params={"query.bibliographic":query,"rows":requested,"offset":(page-1)*page_size,"select":SELECT}
        filters=[]
        if year_from: filters.append(f"from-pub-date:{year_from}-01-01")
        if year_to: filters.append(f"until-pub-date:{year_to}-12-31")
        if filters: params["filter"]=",".join(filters)
        message=self._request("/works",params)["message"]; items=[normalize_crossref_work(x) for x in message.get("items",[]) if isinstance(x,dict)]
        items=[x for x in items if x["doi"]]
        if open_access is True: items=[x for x in items if x["is_open_access"]]
        items=items[:page_size]; total=message.get("total-results") if isinstance(message.get("total-results"),int) else len(items)
        return {"items":items,"page":page,"page_size":page_size,"total":total,"has_more":((page-1)*page_size+len(items))<total}
    search_papers=search_works
    def get_work(self,doi): return normalize_crossref_work(self._request("/works/"+quote(canonicalize_doi(doi) or "",safe=""))["message"])
    get_paper=get_work
    def get_references(self,doi,limit=100):
        raw=self._request("/works/"+quote(canonicalize_doi(doi) or "",safe=""))["message"]; seen=set(); out=[]
        for ref in raw.get("reference",[]) if isinstance(raw.get("reference"),list) else []:
            rd=canonicalize_doi(ref.get("DOI")) if isinstance(ref,dict) else None
            if rd and rd not in seen: seen.add(rd); out.append(rd)
            if len(out)>=limit: break
        resolved=[]
        for rd in out:
            try: resolved.append(self.get_work(rd))
            except CrossrefError: continue
        return resolved
    def resolve_paper_id(self,title,doi=None):
        if doi:
            try: return self.get_work(doi)["external_id"]
            except CrossrefNotFound: pass
        wanted=normalize_title(title).casefold(); result=self.search_works(title,page_size=5)
        return next((p["external_id"] for p in result["items"] if p["title"].casefold()==wanted),None)
