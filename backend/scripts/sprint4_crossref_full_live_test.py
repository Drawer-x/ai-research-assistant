"""Bounded Sprint 4 live integration through the FastAPI HTTP boundary."""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, uuid
from pathlib import Path
from urllib.parse import quote
import fitz, requests

ROOT=Path(__file__).resolve().parents[1]; BASE="http://127.0.0.1:8769"

class API:
    def __init__(self): self.s=requests.Session()
    def call(self,method,path,expected=200,**kw):
        r=self.s.request(method,BASE+path,timeout=(10,180),**kw)
        try: body=r.json()
        except ValueError as exc: raise AssertionError(f"{path}: non-JSON HTTP {r.status_code}") from exc
        if r.status_code!=expected or body.get("code")!=expected: raise AssertionError(f"{path}: HTTP {r.status_code} code={body.get('code')} message={body.get('message')}")
        return body.get("data")
    def user(self,label):
        name=f"xrlive_{label}_{uuid.uuid4().hex[:10]}";password="Crossref-live-123456"
        self.call("POST","/api/auth/register",json={"username":name,"email":name+"@example.com","password":password})
        login=self.call("POST","/api/auth/login",json={"username":name,"password":password});self.s.headers["Authorization"]="Bearer "+login["token"]
        assert self.call("GET","/api/auth/me")["username"]==name

def pdf(path,title):
    d=fitz.open();p=d.new_page();p.insert_textbox(fitz.Rect(50,50,545,790),f"{title}\n\nRetrieval augmented generation uses embeddings, vector search, and grounded generation. Experiments compare retrieval methods and report evidence. References include foundational RAG research.",fontsize=11);d.set_metadata({"title":title,"author":"Integration Test"});d.save(path);d.close()

def validate_recs(items):
    assert items
    for row in items:
        p=row["paper"];assert p["provider"]=="crossref" and p["doi"] and 0<=row["score"]<=1 and row["reasons"] and row["is_fallback"] is False

def run():
    owner=API();owner.user("a");paper_ids=[]
    with tempfile.TemporaryDirectory(prefix="crossref-pdfs-") as td:
        for i in range(3):
            path=Path(td)/f"paper-{i}.pdf";pdf(path,f"RAG Integration Paper {i}")
            with path.open("rb") as f: paper_ids.append(owner.call("POST","/api/papers/upload",files={"file":(path.name,f,"application/pdf")})["paper_id"])
    papers=owner.call("GET","/api/papers");assert set(paper_ids)<={x["paper_id"] for x in papers}
    first=paper_ids[0];owner.call("GET",f"/api/papers/{first}");owner.call("PUT",f"/api/papers/{first}/status",json={"read_status":"rough_read"})
    tag=owner.call("POST","/api/tags",json={"name":"crossref-live"});owner.call("POST",f"/api/papers/{first}/tags",json={"tag_name":tag["name"]});assert owner.call("GET","/api/tags")
    summary=owner.call("POST",f"/api/papers/{first}/summary");assert summary["analysis_scope"]=="full_text" and summary["is_mock"] is False
    qa=owner.call("POST",f"/api/papers/{first}/qa",json={"question":"Does the paper use retrieval augmented generation?"})
    assert qa["analysis_scope"]=="full_text" and qa["is_mock"] is False, f"local QA fallback reason={qa.get('failure_reason')} evidence={qa.get('has_evidence')}"
    assert owner.call("GET",f"/api/papers/{first}/summaries") and owner.call("GET",f"/api/papers/{first}/qa-records")
    comp=owner.call("POST","/api/papers/compare",json={"paper_ids":paper_ids,"compare_dimensions":["problem","method","result"]});assert comp["is_mock"] is False and owner.call("GET","/api/papers/comparisons")

    search=owner.call("GET","/api/discovery/search",params={"query":"retrieval augmented generation","page_size":20});assert search["items"]
    seed=search["items"][0];assert seed["provider"]=="crossref" and seed["doi"] and "/" in seed["doi"]
    detail=owner.call("GET","/api/discovery/papers/"+quote(seed["doi"],safe="/"));assert detail["doi"]==seed["doi"]
    imported=owner.call("POST","/api/discovery/import",json={"provider":"crossref","external_id":seed["doi"]});seed_local=imported["paper_id"]
    duplicate=owner.call("POST","/api/discovery/import",json={"provider":"crossref","external_id":seed["doi"]});assert duplicate["already_imported"] is True and duplicate["paper_id"]==seed_local
    again=owner.call("GET","/api/discovery/search",params={"query":"retrieval augmented generation","page_size":20});marked=next(x for x in again["items"] if x["doi"]==seed["doi"]);assert marked["is_imported"] and marked["local_paper_id"]==seed_local

    abstract_paper=None
    for query_text in ("deep learning medical imaging","climate change biodiversity","machine learning healthcare"):
        result=owner.call("GET","/api/discovery/search",params={"query":query_text,"page_size":50})
        abstract_paper=next((x for x in result["items"] if x.get("abstract")),None)
        if abstract_paper: break
    assert abstract_paper, "bounded Crossref searches found no deposited abstract"
    abstract_import=owner.call("POST","/api/discovery/import",json={"provider":"crossref","external_id":abstract_paper["doi"]})
    external_summary=owner.call("POST",f"/api/papers/{abstract_import['paper_id']}/summary");assert external_summary["analysis_scope"]=="abstract_only" and external_summary["is_mock"] is False

    bypaper=owner.call("POST","/api/recommendations/by-paper",json={"paper_id":seed_local,"limit":5});validate_recs(bypaper)
    library=owner.call("POST","/api/recommendations/for-library",json={"paper_ids":[seed_local,abstract_import["paper_id"]],"limit":5});validate_recs(library)
    topic=owner.call("POST","/api/recommendations/by-topic",json={"topic":"retrieval augmented generation","limit":5});validate_recs(topic)
    history=owner.call("GET","/api/recommendations")["items"];assert history
    owner.call("PATCH",f"/api/recommendations/{history[0]['id']}/status",json={"status":"read_later"})
    if len(history)>1: owner.call("PATCH",f"/api/recommendations/{history[1]['id']}/status",json={"status":"not_interested"})
    rec_import=owner.call("POST",f"/api/recommendations/{history[0]['id']}/import");assert rec_import["paper_id"]

    graph=owner.call("GET","/api/graph/enhanced",params={"include_external":"true","max_nodes":50});ids={n["id"] for n in graph["nodes"]};assert ids and all(isinstance(x,str) for x in ids) and all(e["source"] in ids and e["target"] in ids for e in graph["edges"])
    for kind in ("recommendation","references","citations"):
        expanded=owner.call("POST","/api/graph/expand",json={"node_id":f"local:{seed_local}","expand_type":kind,"limit":3})
        if kind=="citations": assert expanded["meta"]["citation_scope"]=="known_records_only"
    owner.call("GET","/api/graph/enhanced",params={"relation_types":"recommended_from","min_weight":0.1,"include_external":"true","max_nodes":10})
    plan=owner.call("POST","/api/agent/research-plan",json={"research_topic":"RAG","research_goal":"review evidence","duration_weeks":2,"current_level":"undergraduate","paper_ids":paper_ids});assert plan["is_mock"] is False
    assert owner.call("GET","/api/agent/research-plans") and owner.call("GET",f"/api/agent/research-plans/{plan['plan_id']}")

    other=API();other.user("b");assert other.call("GET","/api/papers")==[] and other.call("GET","/api/tags")==[] and other.call("GET","/api/recommendations")["items"]==[] and other.call("GET","/api/agent/research-plans")==[]
    assert other.call("GET","/api/graph/enhanced")["nodes"]==[]
    second_import=other.call("POST","/api/discovery/import",json={"provider":"crossref","external_id":seed["doi"]});assert second_import["already_imported"] is False
    print("SPRINT4_CROSSREF_FULL_LIVE_OK")

def main():
    with tempfile.TemporaryDirectory(prefix="sprint4-crossref-live-",ignore_cleanup_errors=True) as td:
        env=os.environ.copy();env["DATABASE_URL"]="sqlite:///"+(Path(td)/"live.db").as_posix();env["UPLOAD_DIR"]=str(Path(td)/"uploads");env["VECTOR_DIR"]=str(Path(td)/"vector_db")
        process=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8769"],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    if requests.get(BASE+"/api/health",timeout=1).status_code==200: break
                except requests.RequestException: time.sleep(.25)
            else: raise AssertionError("FastAPI did not start")
            run()
        finally:
            process.terminate()
            try: process.wait(10)
            except subprocess.TimeoutExpired: process.kill();process.wait()

if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"SPRINT4_CROSSREF_FULL_LIVE_FAILED: {type(exc).__name__}: {exc}",file=sys.stderr);raise
