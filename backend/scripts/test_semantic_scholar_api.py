"""Safe offline configuration check and real Semantic Scholar public API probe."""
import argparse,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.services.recommendation_adapter_service import recommend_by_topic
from app.services.semantic_scholar_client import AuthenticationRequiredError,InvalidUpstreamResponseError,RateLimitedError,SemanticScholarClient,UpstreamTimeoutError,UpstreamUnavailableError

parser=argparse.ArgumentParser();parser.add_argument("--live",action="store_true");parser.add_argument("--anonymous",action="store_true");args=parser.parse_args()
configured=bool(str(settings.s2_api_key or "").strip()) and str(settings.s2_api_key).strip().casefold() not in {"none","null"}
print(f"key configured: {configured}")
if not args.live:print("status: configuration-only");raise SystemExit(0)
client=SemanticScholarClient(anonymous=args.anonymous)
if args.anonymous and "x-api-key" in client._build_headers():print("SEMANTIC_SCHOLAR_PUBLIC_API_CHECK_BLOCKED");print("reason=anonymous_header_present");raise SystemExit(1)
def run(label,fn):
    started=time.monotonic()
    try:value=fn();print(f"[PASS] {label}");print("status=200");print(f"items_count={len(value) if isinstance(value,list) else 1}");print(f"latency_ms={int((time.monotonic()-started)*1000)}");return value
    except Exception as exc:print(f"[FAIL] {label}");print(f"reason={type(exc).__name__}");raise
try:
    search=run("anonymous paper search",lambda:client.search_papers("machine learning",page_size=3)["items"])
    if not search or not search[0].get("external_id") or not search[0].get("title"):raise InvalidUpstreamResponseError("search structure")
    paper_id=search[0]["external_id"];detail=run("anonymous paper detail",lambda:client.get_paper(paper_id))
    if not detail.get("external_id") or not detail.get("title"):raise InvalidUpstreamResponseError("detail structure")
    run("anonymous references",lambda:client.get_references(paper_id,3));run("anonymous citations",lambda:client.get_citations(paper_id,3))
    recommendation_supported=False
    try:
        recs=run("anonymous single-paper recommendations",lambda:client.get_recommendations_for_paper(paper_id,3));recommendation_supported=True;print("recommendations_anonymous_supported=true")
    except AuthenticationRequiredError:print("recommendations_anonymous_supported=false");print("reason=authentication_required")
    except RateLimitedError:print("recommendations_anonymous_supported=false");print("reason=rate_limited")
    except UpstreamTimeoutError:print("recommendations_anonymous_supported=false");print("reason=timeout")
    except UpstreamUnavailableError:print("recommendations_anonymous_supported=false");print("reason=upstream_unavailable")
    except InvalidUpstreamResponseError:print("recommendations_anonymous_supported=false");print("reason=invalid_response")
    if recommendation_supported:
        run("anonymous multi-seed recommendations",lambda:client.get_recommendations_for_seeds([paper_id],[],3))
    else:print("[SKIP] anonymous multi-seed recommendations");print("reason=single_endpoint_unavailable")
    fallback=recommend_by_topic("machine learning",search,None,None,3)
    if not fallback["items"] or any(x["paper"] not in search or not x["is_fallback"] for x in fallback["items"]):raise RuntimeError("fallback validation failed")
except (UpstreamTimeoutError,UpstreamUnavailableError,RateLimitedError,AuthenticationRequiredError,InvalidUpstreamResponseError) as exc:
    print("SEMANTIC_SCHOLAR_PUBLIC_API_CHECK_BLOCKED");print(f"reason={type(exc).__name__}");raise SystemExit(1)
print("SEMANTIC_SCHOLAR_PUBLIC_API_CHECK_OK")
