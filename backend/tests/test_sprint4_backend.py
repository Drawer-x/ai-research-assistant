import unittest
from unittest.mock import Mock,patch
import requests
from app.services.semantic_scholar_client import *
from app.services.recommendation_adapter_service import recommend_by_topic

def response(status=200,data=None,headers=None):
    r=Mock(status_code=status,headers=headers or {});r.json.side_effect=data if isinstance(data,Exception) else None;r.json.return_value={} if data is None else data;return r
class Sprint4ClientTests(unittest.TestCase):
    def setUp(self):SemanticScholarClient.clear_cache()
    def client(self,*responses,anonymous=False):
        s=Mock();s.request.side_effect=list(responses);return SemanticScholarClient(s,anonymous=anonymous),s
    def test_key_normalization(self):
        for value in (None,"","   ","None","null"):
            with self.subTest(value=value),patch("app.services.semantic_scholar_client.settings.s2_api_key",value):self.assertNotIn("x-api-key",SemanticScholarClient()._build_headers())
    def test_real_key_and_anonymous_override(self):
        with patch("app.services.semantic_scholar_client.settings.s2_api_key"," secret "):
            self.assertEqual(SemanticScholarClient()._build_headers()["x-api-key"],"secret");self.assertNotIn("x-api-key",SemanticScholarClient(anonymous=True)._build_headers())
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_search_pagination_fields_and_normalize(self,_):
        c,s=self.client(response(data={"total":21,"data":[{"paperId":"x","title":" A ","authors":[]}]}));r=c.search_papers("test",page=2,page_size=10);kw=s.request.call_args.kwargs;self.assertEqual(kw["params"]["offset"],10);self.assertIn("citationCount",kw["params"]["fields"]);self.assertEqual(r["items"][0]["title"],"A")
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_url_encoding_and_links(self,_):
        c,s=self.client(response(data={"paperId":"a","title":"T"}),response(data={"data":[{"citedPaper":{"paperId":"r","title":"R"}}]}),response(data={"data":[{"citingPaper":{"paperId":"c","title":"C"}}]}));c.get_paper("DOI:10/x y");self.assertIn("DOI%3A10%2Fx%20y",s.request.call_args.args[1]);self.assertEqual(c.get_references("a",1)[0]["external_id"],"r");self.assertEqual(c.get_citations("a",1)[0]["external_id"],"c")
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_recommendation_success_and_post_contract(self,_):
        c,s=self.client(response(data={"recommendedPapers":[{"paperId":"r","title":"R"}]}),response(data={"recommendedPapers":[]}));self.assertEqual(c.get_recommendations_for_paper("a",1)[0]["external_id"],"r");c.get_recommendations_for_seeds(["a"],[],2);self.assertEqual(s.request.call_args.args[0],"POST");self.assertEqual(s.request.call_args.kwargs["json"],[{"positivePaperIds":["a"],"negativePaperIds":[]}][0])
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_auth_errors_no_retry(self,_):
        for status in (401,403):
            c,s=self.client(response(status));
            with self.assertRaises(AuthenticationRequiredError):c.get_recommendations_for_paper("a")
            self.assertEqual(s.request.call_count,1)
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_rate_limit_retries_once(self,_):
        c,s=self.client(response(429,headers={"Retry-After":"1"}),response(429));
        with self.assertRaises(RateLimitedError):c.get_recommendations_for_paper("a")
        self.assertEqual(s.request.call_count,2)
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_timeout_5xx_and_non_json(self,_):
        for responses,exc in [((requests.Timeout(),requests.Timeout()),UpstreamTimeoutError),((response(503),response(503)),UpstreamUnavailableError),((response(data=ValueError()),),InvalidUpstreamResponseError)]:
            c,_=self.client(*responses)
            with self.assertRaises(exc):c.get_recommendations_for_paper("a")
    @patch("app.services.semantic_scholar_client.time.sleep")
    def test_cache_hit_and_errors_not_cached(self,_):
        c,s=self.client(response(data={"total":0,"data":[]}));c.search_papers("cache");c.search_papers("cache");self.assertEqual(s.request.call_count,1)
        SemanticScholarClient.clear_cache();c,s=self.client(response(503),response(503),response(data={"total":0,"data":[]}));
        with self.assertRaises(UpstreamUnavailableError):c.search_papers("error")
        c.search_papers("error");self.assertEqual(s.request.call_count,3)
    def test_normalizers_and_fallback_real_candidates(self):
        # Member B algorithm is present: adapter should return scored items with is_fallback=false.
        p=normalize_paper({"paperId":"x","title":" A  title ","externalIds":{"DOI":"doi:10.X/Y"}});self.assertEqual(p["doi"],"10.x/y");candidates=[p];r=recommend_by_topic("x",candidates,None,None,1);self.assertIs(r["items"][0]["paper"],p);self.assertFalse(r["items"][0]["is_fallback"]);self.assertTrue(0<=r["items"][0]["score"]<=1);self.assertTrue(r["items"][0]["reasons"])
if __name__=="__main__":unittest.main()
