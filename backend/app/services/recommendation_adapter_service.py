import math
def _fallback(candidates,limit):
    n=max(len(candidates),1); return {"items":[{"paper":p,"score":round(max(0,1-i/n),6),"reasons":["Ranked from Crossref metadata candidates"],"seed_paper_ids":[],"is_fallback":True} for i,p in enumerate(candidates[:limit])]}
def _call(name,args,candidates,limit):
    try:
        from app.services import recommendation_service as impl
        result=getattr(impl,name)(**args)
        if not isinstance(result,dict) or not isinstance(result.get("items"),list): raise ValueError
        for x in result["items"]:
            if not isinstance(x,dict) or not isinstance(x.get("paper"),dict) or not math.isfinite(float(x.get("score",0))): raise ValueError
        return result
    except (ImportError,AttributeError,TypeError,ValueError,RuntimeError): return _fallback(candidates,limit)
def recommend_by_paper(seed_paper,candidates,limit): return _call("recommend_by_paper",locals(),candidates,limit)
def recommend_for_library(seed_papers,candidates,negative_external_ids,limit): return _call("recommend_for_library",locals(),candidates,limit)
def recommend_by_topic(topic,candidates,year_from,year_to,limit): return _call("recommend_by_topic",locals(),candidates,limit)
