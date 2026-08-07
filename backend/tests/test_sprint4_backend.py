import unittest
from unittest.mock import Mock, patch
import requests
from app.services.crossref_client import *
from app.services.recommendation_adapter_service import recommend_by_topic

def response(status=200,message=None,headers=None):
    r=Mock(status_code=status,headers=headers or {});r.json.return_value={"message":message or {}};return r

class Sprint4CrossrefTests(unittest.TestCase):
    def setUp(self): CrossrefClient.clear_cache()
    def client(self,*responses):
        s=Mock();s.get.side_effect=list(responses);return CrossrefClient(s),s
    def test_public_headers_and_optional_mailto(self):
        with patch("app.services.crossref_client.settings.crossref_mailto",None):
            c,s=self.client(response(message={"items":[],"total-results":0}));c.search_works("test");kw=s.get.call_args.kwargs
            self.assertNotIn("Authorization",kw["headers"]);self.assertNotIn("x-api-key",kw["headers"]);self.assertNotIn("mailto",kw["params"]);self.assertEqual(kw["headers"]["User-Agent"],"AIResearchAssistant/1.0")
        CrossrefClient.clear_cache()
        with patch("app.services.crossref_client.settings.crossref_mailto","dev@example.test"):
            c,s=self.client(response(message={"items":[],"total-results":0}));c.search_works("test");self.assertEqual(s.get.call_args.kwargs["params"]["mailto"],"dev@example.test");self.assertIn("mailto:",s.get.call_args.kwargs["headers"]["User-Agent"])
    def test_search_pagination_year_select_and_normalize(self):
        c,s=self.client(response(message={"total-results":21,"items":[{"DOI":"10.X/Y","title":[" A "],"author":[]}]}));r=c.search_works("test",2022,2026,page=2,page_size=10);p=s.get.call_args.kwargs["params"]
        self.assertEqual((p["query.bibliographic"],p["rows"],p["offset"]),("test",10,10));self.assertIn("from-pub-date:2022-01-01",p["filter"]);self.assertIn("until-pub-date:2026-12-31",p["filter"]);self.assertIn("DOI",p["select"]);self.assertEqual(r["items"][0]["external_id"],"10.x/y")
    def test_doi_encoding_references_and_jats(self):
        target={"DOI":"10.X/A B","title":["T"],"abstract":"<jats:p>A &amp; B</jats:p>","reference":[{"DOI":"10.R/1"}]}
        ref={"DOI":"10.r/1","title":["R"]};c,s=self.client(response(message=target),response(message=ref));p=c.get_work("https://doi.org/10.X/A B");self.assertIn("10.x%2Fa%20b",s.get.call_args_list[0].args[0]);self.assertEqual(p["abstract"],"A & B");self.assertEqual(c.get_references("10.x/a b",1)[0]["doi"],"10.r/1")
    def test_retry_timeout_invalid_and_cache(self):
        with patch("app.services.crossref_client.settings.crossref_max_retries",1),patch("app.services.crossref_client.time.sleep"):
            c,s=self.client(response(429,headers={"Retry-After":"1"}),response(429));
            with self.assertRaises(RateLimitedError):c.search_works("rate")
            self.assertEqual(s.get.call_count,2)
            c,_=self.client(requests.Timeout(),requests.Timeout());
            with self.assertRaises(UpstreamTimeoutError):c.search_works("timeout")
        CrossrefClient.clear_cache();c,s=self.client(response(message={"items":[],"total-results":0}));c.search_works("cache");c.search_works("cache");self.assertEqual(s.get.call_count,1)
    def test_normalization_and_b_algorithm(self):
        p=normalize_crossref_work({"DOI":"doi:10.X/Y","title":[" A title "],"published":{"date-parts":[[2024,2,3]]},"is-referenced-by-count":4});self.assertEqual((p["doi"],p["publication_date"],p["provider"]),("10.x/y","2024-02-03","crossref"));r=recommend_by_topic("title",[p],None,None,1);self.assertFalse(r["items"][0]["is_fallback"])

    def test_5xx_retries_are_bounded_and_mapped(self):
        with patch("app.services.crossref_client.settings.crossref_max_retries",1),patch("app.services.crossref_client.time.sleep"):
            c,s=self.client(response(503),response(503))
            with self.assertRaises(UpstreamUnavailableError): c.search_works("server failure")
            self.assertEqual(s.get.call_count,2)

    def test_errors_are_not_cached(self):
        with patch("app.services.crossref_client.settings.crossref_max_retries",0),patch("app.services.crossref_client.time.sleep"):
            c,s=self.client(response(503),response(message={"items":[],"total-results":0}))
            with self.assertRaises(UpstreamUnavailableError): c.search_works("not cached")
            self.assertEqual(c.search_works("not cached")["items"],[])
            self.assertEqual(s.get.call_count,2)

    def test_expired_cache_is_refetched(self):
        c,s=self.client(response(message={"items":[],"total-results":0}),response(message={"items":[],"total-results":0}))
        with patch("app.services.crossref_client.settings.crossref_cache_ttl_seconds",0):
            c.search_works("expires");c.search_works("expires")
        self.assertEqual(s.get.call_count,2)

    def test_references_ignore_records_without_real_doi(self):
        work={"DOI":"10.seed/x","title":["Seed"],"reference":[{}, {"DOI":""}, {"DOI":"10.real/ref"}, {"DOI":"https://doi.org/10.REAL/REF"}]}
        ref={"DOI":"10.real/ref","title":["Reference"]};c,s=self.client(response(message=work),response(message=ref))
        items=c.get_references("10.seed/x",10)
        self.assertEqual([x["doi"] for x in items],["10.real/ref"]);self.assertEqual(s.get.call_count,2)

    def test_missing_abstract_stays_none(self):
        paper=normalize_crossref_work({"DOI":"10.test/no-abstract","title":["No abstract"]})
        self.assertIsNone(paper["abstract"]);self.assertFalse(paper["is_open_access"])

    def test_fastapi_detail_route_accepts_doi_slash_and_citation_scope_contract(self):
        import inspect
        discovery_source=inspect.getsource(__import__("app.api.discovery",fromlist=["detail"]))
        self.assertIn('"/papers/{external_id:path}"',discovery_source)
        graph_source=inspect.getsource(__import__("app.api.graph",fromlist=["expand"]).expand)
        self.assertIn('citation_scope="known_records_only"',graph_source)

if __name__=="__main__": unittest.main()
