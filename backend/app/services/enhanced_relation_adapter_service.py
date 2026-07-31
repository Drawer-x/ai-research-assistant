def generate_enhanced_relations(local_papers,external_papers,recommendation_records,relation_types):
    try:
        from app.services.enhanced_relation_service import generate_enhanced_relations as fn
        result=fn(local_papers,external_papers,recommendation_records,relation_types)
        if not isinstance(result,dict) or not isinstance(result.get("relations"),list): raise ValueError
        return result
    except (ImportError,ValueError,TypeError,RuntimeError):
        relations=[]
        if "recommended_from" in relation_types:
            for r in recommendation_records:
                for seed in r.get("seed_paper_ids",[]):
                    relations.append({"source":f"local:{seed}","target":f"recommendation:{r['id']}","relation_type":"recommended_from","weight":max(0,min(1,float(r.get('score',0)))),"description":"Persisted recommendation","directed":True,"is_fallback":True})
        return {"relations":relations}
