"""Defensive Semantic Scholar client with anonymous access and bounded caching."""
from collections import OrderedDict
import threading
import time
from urllib.parse import quote

import requests
from app.core.config import settings

FIELDS = "paperId,title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount,referenceCount,fieldsOfStudy,publicationDate"

class SemanticScholarError(RuntimeError): pass
class SemanticScholarNotFound(SemanticScholarError): pass
class RateLimitedError(SemanticScholarError): pass
class AuthenticationRequiredError(SemanticScholarError): pass
class UpstreamUnavailableError(SemanticScholarError): pass
class UpstreamTimeoutError(SemanticScholarError): pass
class InvalidUpstreamResponseError(SemanticScholarError): pass

def normalize_doi(value):
    if not value: return None
    value=str(value).strip().lower()
    for prefix in ("https://doi.org/","http://doi.org/","doi:"):
        if value.startswith(prefix): value=value[len(prefix):]
    return value or None
def normalize_title(value): return " ".join(str(value or "").split())
def normalize_paper(raw):
    raw=raw if isinstance(raw,dict) else {}; ids=raw.get("externalIds") if isinstance(raw.get("externalIds"),dict) else {}; authors=raw.get("authors") if isinstance(raw.get("authors"),list) else []; pdf=raw.get("openAccessPdf") if isinstance(raw.get("openAccessPdf"),dict) else {}
    return {"provider":"semantic_scholar","external_id":str(raw.get("paperId") or ""),"title":normalize_title(raw.get("title")),"abstract":raw.get("abstract") if isinstance(raw.get("abstract"),str) else None,"authors":[{"author_id":str(a.get("authorId")) if a.get("authorId") is not None else None,"name":str(a.get("name") or "")} for a in authors if isinstance(a,dict)],"year":raw.get("year") if isinstance(raw.get("year"),int) else None,"venue":raw.get("venue") if isinstance(raw.get("venue"),str) and raw.get("venue") else None,"doi":normalize_doi(ids.get("DOI")),"arxiv_id":str(ids.get("ArXiv")) if ids.get("ArXiv") else None,"external_url":raw.get("url") if isinstance(raw.get("url"),str) else None,"pdf_url":pdf.get("url") if isinstance(pdf.get("url"),str) else None,"citation_count":raw.get("citationCount") if isinstance(raw.get("citationCount"),int) else 0,"reference_count":raw.get("referenceCount") if isinstance(raw.get("referenceCount"),int) else 0,"fields_of_study":[str(x) for x in (raw.get("fieldsOfStudy") or []) if isinstance(x,str)],"publication_date":raw.get("publicationDate") if isinstance(raw.get("publicationDate"),str) else None,"is_open_access":bool(pdf.get("url")),"is_imported":False,"local_paper_id":None}

class SemanticScholarClient:
    _lock=threading.Lock(); _last_request=0.0; _cache=OrderedDict(); _cache_max=256
    def __init__(self,session=None,anonymous=False): self.session=session or requests.Session(); self.anonymous=anonymous
    @classmethod
    def clear_cache(cls):
        with cls._lock: cls._cache.clear()
    def _build_headers(self,content_type=False):
        headers={"Accept":"application/json"}
        if content_type: headers["Content-Type"]="application/json"
        raw=None if self.anonymous else settings.s2_api_key
        key=str(raw).strip() if raw is not None else ""
        if key.casefold() not in {"","none","null"}: headers["x-api-key"]=key
        return headers
    @classmethod
    def _cached(cls,key):
        with cls._lock:
            entry=cls._cache.get(key)
            if not entry:return None
            expires,value=entry
            if expires<=time.monotonic():del cls._cache[key];return None
            cls._cache.move_to_end(key);return value
    @classmethod
    def _put_cache(cls,key,value,ttl):
        with cls._lock:
            cls._cache[key]=(time.monotonic()+ttl,value);cls._cache.move_to_end(key)
            while len(cls._cache)>cls._cache_max:cls._cache.popitem(last=False)
    def _request(self,method,base,path,params=None,json_body=None,cache_ttl=0):
        url=base.rstrip("/")+path; cache_key=(method,url,tuple(sorted((params or {}).items())),repr(json_body))
        if cache_ttl:
            cached=self._cached(cache_key)
            if cached is not None:return cached
        attempts=max(0,min(int(settings.s2_max_retries),1))+1
        for attempt in range(attempts):
            with self._lock:
                delay=float(settings.s2_min_request_interval_seconds)-(time.monotonic()-self._last_request)
                if delay>0:time.sleep(delay)
                self.__class__._last_request=time.monotonic()
            try: response=self.session.request(method,url,params=params,json=json_body,headers=self._build_headers(method=="POST"),timeout=(settings.s2_connect_timeout_seconds,settings.s2_read_timeout_seconds))
            except requests.Timeout as exc:
                if attempt+1<attempts:continue
                raise UpstreamTimeoutError("External paper service timed out") from exc
            except requests.RequestException as exc:
                if attempt+1<attempts:continue
                raise UpstreamUnavailableError("External paper service unavailable") from exc
            status=response.status_code
            if status==404:raise SemanticScholarNotFound("External paper not found")
            if status in (401,403):raise AuthenticationRequiredError("Public endpoint currently requires authentication")
            if status==429:
                if attempt+1<attempts:
                    try:wait=min(max(float(response.headers.get("Retry-After","0")),0),5)
                    except ValueError:wait=0
                    if wait:time.sleep(wait)
                    continue
                raise RateLimitedError("External paper service rate limited")
            if status in (500,502,503,504):
                if attempt+1<attempts:continue
                raise UpstreamUnavailableError("External paper service unavailable")
            if status>=400:raise SemanticScholarError("External paper request failed")
            try:data=response.json()
            except (ValueError,TypeError) as exc:raise InvalidUpstreamResponseError("Invalid external paper response") from exc
            if not isinstance(data,(dict,list)):raise InvalidUpstreamResponseError("Invalid external paper response")
            if cache_ttl:self._put_cache(cache_key,data,cache_ttl)
            return data
        raise UpstreamUnavailableError("External paper service unavailable")
    def search_papers(self,query,year_from=None,year_to=None,open_access=None,page=1,page_size=20):
        query=normalize_title(query)
        if not query:raise ValueError("query must not be empty")
        if page<1 or not 1<=page_size<=100:raise ValueError("invalid pagination")
        params={"query":query,"offset":(page-1)*page_size,"limit":page_size,"fields":FIELDS}
        if year_from or year_to:params["year"]=f"{year_from or ''}-{year_to or ''}"
        if open_access is not None:params["openAccessPdf"]=str(open_access).lower()
        data=self._request("GET",settings.s2_graph_base_url,"/paper/search",params,cache_ttl=300)
        items=[normalize_paper(x) for x in data.get("data",[]) if isinstance(x,dict)];total=data.get("total") if isinstance(data.get("total"),int) else len(items)
        return {"items":items,"page":page,"page_size":page_size,"total":total,"has_more":page*page_size<total}
    def get_paper(self,external_id):return normalize_paper(self._request("GET",settings.s2_graph_base_url,"/paper/"+quote(str(external_id),safe=""),{"fields":FIELDS},cache_ttl=1800))
    def resolve_paper_id(self,title,doi=None):
        if doi:
            try:return self.get_paper("DOI:"+normalize_doi(doi))["external_id"] or None
            except SemanticScholarNotFound:pass
        result=self.search_papers(normalize_title(title),page_size=5);wanted=normalize_title(title).casefold();return next((p["external_id"] for p in result["items"] if p["title"].casefold()==wanted),None)
    def get_recommendations_for_paper(self,external_id,limit=20):
        data=self._request("GET",settings.s2_recommendations_base_url,"/papers/forpaper/"+quote(str(external_id),safe=""),{"limit":limit,"fields":FIELDS},cache_ttl=300)
        return [normalize_paper(x) for x in data.get("recommendedPapers",[]) if isinstance(x,dict)]
    def get_recommendations_for_seeds(self,positive_ids,negative_ids,limit=20):
        data=self._request("POST",settings.s2_recommendations_base_url,"/papers",{"limit":limit,"fields":FIELDS},{"positivePaperIds":positive_ids,"negativePaperIds":negative_ids},cache_ttl=300)
        return [normalize_paper(x) for x in data.get("recommendedPapers",[]) if isinstance(x,dict)]
    def _links(self,external_id,kind,limit):
        data=self._request("GET",settings.s2_graph_base_url,"/paper/"+quote(str(external_id),safe="")+f"/{kind}",{"limit":limit,"fields":FIELDS},cache_ttl=900);key="citedPaper" if kind=="references" else "citingPaper";return [normalize_paper(x[key]) for x in data.get("data",[]) if isinstance(x,dict) and isinstance(x.get(key),dict)]
    def get_references(self,external_id,limit=100):return self._links(external_id,"references",limit)
    def get_citations(self,external_id,limit=100):return self._links(external_id,"citations",limit)
