# Sprint 4 backend contract

All routes require `Authorization: Bearer <JWT>` and return `{code,message,data}`. The frontend must call this backend and must never call Semantic Scholar directly or read `S2_API_KEY`.

With an empty, whitespace-only, `None`, or `null`-like `S2_API_KEY`, the client sends no key header and uses the official anonymous API. Public responses are cached in bounded memory (search/recommendations 5 minutes, details 30 minutes, references/citations 15 minutes); user-specific import flags are applied after cache lookup. Anonymous recommendation failures are replaced only with real Academic Graph search candidates. Authentication, rate-limit, timeout, availability, not-found, and invalid-response failures remain distinct and are mapped to the standard API error envelope.

## Contract for member B

```python
recommend_by_paper(seed_paper: dict, candidates: list[dict], limit: int) -> dict
recommend_for_library(seed_papers: list[dict], candidates: list[dict], negative_external_ids: list[str], limit: int) -> dict
recommend_by_topic(topic: str, candidates: list[dict], year_from: int | None, year_to: int | None, limit: int) -> dict
generate_enhanced_relations(local_papers: list[dict], external_papers: list[dict], recommendation_records: list[dict], relation_types: list[str]) -> dict
```

Recommendation output is `{"items":[{"paper": ExternalPaper,"score":0..1,"reasons":[],"seed_paper_ids":[],"is_fallback":false}]}`. Relation output is `{"relations":[{"source":"local:1","target":"s2:id","relation_type":"recommended_from","weight":0..1,"description":"...","directed":true,"is_fallback":false}]}`. Missing strings are `null`, lists are `[]`, numbers are `0`, and booleans are `false`. IDs use `local:<paper_id>`, `s2:<external_id>`, and `recommendation:<id>`. Self-loops, invalid endpoints and non-finite/out-of-range weights are invalid. B must be deterministic, must not invent papers, and must not access the database, JWT, or HTTP routes. Until B is present, recommendation fallback preserves real provider order; relation fallback emits only persisted, citation, or recommendation evidence.

## Contract for member C

Discovery: `GET /api/discovery/search?query=&year_from=&year_to=&open_access=&page=1&page_size=20`, `GET /api/discovery/papers/{external_id}`, `POST /api/discovery/import` with `{"provider":"semantic_scholar","external_id":"id"}`.

Recommendations: `POST /api/recommendations/by-paper` (`{"paper_id":12,"limit":20}`), `POST /api/recommendations/for-library` (`{"paper_ids":[12],"limit":20}`), `POST /api/recommendations/by-topic` (`{"topic":"RAG","year_from":2022,"year_to":2026,"limit":20}`), `GET /api/recommendations?mode=&status=&page=1&page_size=20`, `PATCH /api/recommendations/{id}/status` (`{"status":"read_later"}`), and `POST /api/recommendations/{id}/import`.

Enhanced graph: `GET /api/graph/enhanced?paper_ids=1&relation_types=citation&min_weight=0&include_external=true&max_nodes=50`, `POST /api/graph/expand` (`{"node_id":"local:12","expand_type":"references","limit":10}`), and `GET /api/graph/relation-types`.

Search pagination data is `{items,page,page_size,total,has_more}`. `ExternalPaper` exposes normalized provider metadata plus `is_imported` and `local_paper_id`. Recommendation items expose `id,mode,paper,score,reasons,seed_paper_ids,status,is_fallback,created_at,updated_at`; statuses are `new`, `read_later`, `imported`, `not_interested`. Graph data contains `{nodes,edges,meta}`; nodes expose `node_type` (`local`, `external`, `recommended`) and edges expose string endpoints, type, weight, direction and `is_fallback`. AI endpoints add `analysis_scope`, either `full_text` or `abstract_only`. Errors use the same envelope with HTTP 404, 422, 429, or 502/503 as applicable.
