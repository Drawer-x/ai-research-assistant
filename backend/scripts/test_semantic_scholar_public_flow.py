"""Live application-level anonymous Semantic Scholar flow; never prints secrets or papers."""
import argparse,time,uuid
import requests

p=argparse.ArgumentParser();p.add_argument("--base-url",default="http://127.0.0.1:8769");p.add_argument("--request-timeout",type=float,default=120);a=p.parse_args();base=a.base_url.rstrip("/");timeout=a.request_timeout
def call(method,path,session=None,**kwargs):
    r=(session or requests).request(method,base+path,timeout=timeout,**kwargs)
    try:body=r.json()
    except ValueError:raise AssertionError(f"{path}: non-json HTTP {r.status_code}")
    if r.status_code>=400:raise AssertionError(f"{path}: HTTP {r.status_code}, code={body.get('code')}")
    return body.get("data")
def user():
    suffix=uuid.uuid4().hex[:12];s=requests.Session();call("POST","/api/auth/register",s,json={"username":"s2_"+suffix,"email":"s2_"+suffix+"@example.com","password":"SafePass123!"});login=call("POST","/api/auth/login",s,json={"username":"s2_"+suffix,"password":"SafePass123!"});s.headers["Authorization"]="Bearer "+login["token"];return s
try:
    owner=user();other=user();result=call("GET","/api/discovery/search",owner,params={"query":"machine learning","page_size":3});items=result["items"]
    if not items or not items[0].get("external_id"):raise AssertionError("search returned no real external id")
    eid=items[0]["external_id"];detail=call("GET","/api/discovery/papers/"+requests.utils.quote(eid,safe=""),owner)
    if detail.get("external_id")!=eid:raise AssertionError("detail id mismatch")
    imported=call("POST","/api/discovery/import",owner,json={"provider":"semantic_scholar","external_id":eid});pid=imported["paper_id"]
    again=call("GET","/api/discovery/search",owner,params={"query":"machine learning","page_size":3})
    if not next((x for x in again["items"] if x["external_id"]==eid and x["is_imported"]),None):raise AssertionError("import status missing")
    if not call("POST","/api/discovery/import",owner,json={"provider":"semantic_scholar","external_id":eid})["already_imported"]:raise AssertionError("duplicate import not detected")
    bypaper=call("POST","/api/recommendations/by-paper",owner,json={"paper_id":pid,"limit":3});topic=call("POST","/api/recommendations/by-topic",owner,json={"topic":"machine learning","limit":3});library=call("POST","/api/recommendations/for-library",owner,json={"paper_ids":[pid],"limit":3})
    for name,rows in (("by-paper",bypaper),("by-topic",topic),("for-library",library)):
        if not rows or any(not x["paper"].get("external_id") for x in rows):raise AssertionError(name+" returned no real candidates")
    graph=call("GET","/api/graph/enhanced",owner,params={"paper_ids":pid,"include_external":True});
    for kind in ("references","citations","recommendation"):
        expanded=call("POST","/api/graph/expand",owner,json={"node_id":f"local:{pid}","expand_type":kind,"limit":3})
        if any(not n.get("external_id") for n in expanded["nodes"]):raise AssertionError(kind+" node lacks external id")
    other_search=call("GET","/api/discovery/search",other,params={"query":"machine learning","page_size":3})
    if any(x.get("local_paper_id")==pid or x.get("is_imported") for x in other_search["items"] if x["external_id"]==eid):raise AssertionError("cross-user import leak")
    if call("GET","/api/recommendations",other)["items"]:raise AssertionError("cross-user recommendation leak")
except Exception as exc:
    print("SEMANTIC_SCHOLAR_PUBLIC_FLOW_BLOCKED");print(f"reason={type(exc).__name__}");print(f"detail={str(exc)[:200]}");raise SystemExit(1)
print("SEMANTIC_SCHOLAR_PUBLIC_FLOW_OK")
