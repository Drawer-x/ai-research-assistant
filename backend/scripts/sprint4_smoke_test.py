from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import app
required={"/api/discovery/search","/api/discovery/papers/{external_id}","/api/discovery/import","/api/recommendations/by-paper","/api/recommendations/for-library","/api/recommendations/by-topic","/api/recommendations","/api/recommendations/{recommendation_id}/status","/api/recommendations/{recommendation_id}/import","/api/graph/enhanced","/api/graph/expand","/api/graph/relation-types"}
missing=required-set(app.openapi()["paths"])
if missing:raise SystemExit("missing Sprint 4 routes: "+", ".join(sorted(missing)))
print("SPRINT4_SMOKE_TEST_OK")
