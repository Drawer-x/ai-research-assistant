import json
import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.schemas.agent import ResearchPlanRequest
from app.schemas.ai import ComparePapersRequest, QARequest
from app.services.agent_service import generate_research_plan
from app.services.ai_adapter_service import safe_answer_question, safe_compare_papers, safe_generate_summary
from app.services.ai_errors import AIErrorReason
from app.services.ai_summary_service import SUMMARY_FIELDS, generate_paper_summary_result
from app.services.compare_service import compare_papers
from app.services.llm_client import LLMServiceError
from app.services import llm_client
from app.services.qa_service import answer_question_about_paper
from app.services.structured_output import StructuredOutputError, parse_json_object
from app.services.vector_store import RetrievedChunk
from app.services.vector_store import VectorStoreError


def valid_summary() -> dict[str, str]:
    return {field: f"valid {field}" for field in SUMMARY_FIELDS}


def valid_plan(weeks: int = 2) -> dict:
    return {
        "stages": [{"name": "调研", "tasks": ["阅读论文"], "output": "调研笔记"}],
        "weekly_plan": [
            {"week": week, "goal": f"目标 {week}", "tasks": [f"任务 {week}"]}
            for week in range(1, weeks + 1)
        ],
        "risks": ["数据不足"],
    }


class StructuredOutputTests(unittest.TestCase):
    def test_extracts_object_from_fenced_explanation(self):
        self.assertEqual(parse_json_object('result:\n```json\n{"ok": true}\n```')["ok"], True)

    def test_rejects_multiple_top_level_json_objects(self):
        with self.assertRaises(StructuredOutputError):
            parse_json_object('example: {"answer":"wrong"}\nresult: {"answer":"right"}')

    def test_nested_object_is_not_mistaken_for_a_second_result(self):
        value = parse_json_object('result: {"outer":{"inner":true}}')
        self.assertTrue(value["outer"]["inner"])


class LLMClientTests(unittest.TestCase):
    def test_missing_key_has_typed_reason(self):
        with patch.object(llm_client.settings, "ecnu_api_key", None):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client.chat_completion([{"role": "user", "content": "test"}])
        self.assertEqual(caught.exception.reason, AIErrorReason.MISSING_CONFIGURATION)

    def _response(self, payload=None, *, status=200, json_error=None):
        response = Mock(ok=status < 400, status_code=status)
        response.json.side_effect = json_error
        if json_error is None:
            response.json.return_value = payload
        return response

    @patch("app.services.llm_client.requests.post")
    def test_standard_choices_response_and_request_contract(self, post):
        post.return_value = self._response({"choices": [{"message": {"content": " connected "}}]})
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            result = llm_client.chat_completion([{"role": "user", "content": "test"}])
        self.assertEqual(result, "connected")
        kwargs = post.call_args.kwargs
        self.assertFalse(kwargs["json"]["stream"])
        self.assertEqual(kwargs["json"]["model"], llm_client.settings.ecnu_model)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer configured")

    @patch("app.services.llm_client.requests.post")
    def test_nested_data_choices_response(self, post):
        post.return_value = self._response({"data": {"choices": [{"message": {"content": "nested"}}]}})
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            self.assertEqual(llm_client.chat_completion([{"role": "user", "content": "test"}]), "nested")

    @patch("app.services.llm_client.requests.post")
    def test_http_error_is_sanitized(self, post):
        post.return_value = self._response(status=503)
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client.chat_completion([{"role": "user", "content": "secret prompt"}])
        self.assertEqual(caught.exception.reason, AIErrorReason.PROVIDER_ERROR)
        self.assertNotIn("secret", str(caught.exception))

    @patch("app.services.llm_client.requests.post", side_effect=llm_client.requests.Timeout("secret"))
    def test_timeout_is_sanitized(self, _post):
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client.chat_completion([{"role": "user", "content": "test"}])
        self.assertEqual(caught.exception.reason, AIErrorReason.TIMEOUT)
        self.assertNotIn("secret", str(caught.exception))

    @patch("app.services.llm_client.requests.post")
    def test_non_json_response_is_rejected(self, post):
        post.return_value = self._response(json_error=ValueError("raw body"))
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client.chat_completion([{"role": "user", "content": "test"}])
        self.assertEqual(caught.exception.reason, AIErrorReason.MALFORMED_RESPONSE)

    @patch("app.services.llm_client.requests.post")
    def test_missing_content_is_rejected(self, post):
        post.return_value = self._response({"choices": []})
        with patch.object(llm_client.settings, "ecnu_api_key", "configured"):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client.chat_completion([{"role": "user", "content": "test"}])
        self.assertEqual(caught.exception.reason, AIErrorReason.MALFORMED_RESPONSE)


class SummaryServiceTests(unittest.TestCase):
    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_successful_structured_summary_is_real(self, chat):
        chat.return_value = json.dumps(valid_summary())
        summary, is_mock, model_name = generate_paper_summary_result("paper body")
        self.assertEqual(summary, valid_summary())
        self.assertFalse(is_mock)
        self.assertTrue(model_name)

    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_fenced_structured_summary_is_real(self, chat):
        chat.return_value = f"```json\n{json.dumps(valid_summary())}\n```"
        summary, is_mock, _ = generate_paper_summary_result("paper body")
        self.assertEqual(summary, valid_summary())
        self.assertFalse(is_mock)

    @patch("app.services.ai_summary_service.chat_with_deepseek", return_value="not json")
    def test_malformed_json_uses_complete_fallback(self, _chat):
        summary, is_mock, model_name = generate_paper_summary_result("paper body")
        self.assertEqual(set(summary), set(SUMMARY_FIELDS))
        self.assertTrue(all(summary.values()))
        self.assertTrue(is_mock)
        self.assertEqual(model_name, "local-fallback")

    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_missing_noncritical_field_is_normalized_as_real(self, chat):
        incomplete = valid_summary()
        incomplete.pop("limitation")
        chat.return_value = json.dumps(incomplete)
        summary, is_mock, _ = generate_paper_summary_result("paper body")
        self.assertFalse(is_mock)
        self.assertEqual(summary["limitation"], "")

    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_nested_summary_envelopes_are_normalized(self, chat):
        chat.return_value = json.dumps({"data": {"content": {"summary": {"method": "nested method"}}}})
        summary, is_mock, _ = generate_paper_summary_result("paper body")
        self.assertFalse(is_mock)
        self.assertEqual(summary["method"], "nested method")
        self.assertEqual(summary["background"], "")

    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_provider_failure_uses_complete_fallback(self, chat):
        chat.side_effect = LLMServiceError(AIErrorReason.PROVIDER_ERROR, "AI 服务调用失败")
        summary, is_mock, _ = generate_paper_summary_result("paper body")
        self.assertEqual(tuple(summary), SUMMARY_FIELDS)
        self.assertTrue(is_mock)

    def test_empty_paper_text_uses_complete_fallback(self):
        summary, is_mock, _ = generate_paper_summary_result("  ")
        self.assertEqual(tuple(summary), SUMMARY_FIELDS)
        self.assertTrue(is_mock)


class AdapterTests(unittest.TestCase):
    @patch("app.services.ai_summary_service.generate_paper_summary_result")
    def test_summary_adapter_preserves_execution_metadata(self, generate):
        generate.return_value = (valid_summary(), False, "validated-model")
        result = safe_generate_summary("paper")
        self.assertFalse(result["is_mock"])
        self.assertEqual(result["model_name"], "validated-model")

    @patch("app.services.ai_summary_service.generate_paper_summary_result")
    def test_summary_adapter_normalizes_incomplete_real_result(self, generate):
        generate.return_value = ({"background": "only one field"}, False, "model")
        result = safe_generate_summary("paper")
        self.assertFalse(result["is_mock"])
        self.assertEqual(set(result["summary"]), set(SUMMARY_FIELDS))

    @patch("app.services.ai_summary_service.generate_paper_summary_result")
    def test_summary_adapter_falls_back_on_upstream_exception(self, generate):
        generate.side_effect = LLMServiceError(AIErrorReason.TIMEOUT, "safe timeout")
        result = safe_generate_summary("paper")
        self.assertTrue(result["is_mock"])
        self.assertEqual(set(result["summary"]), set(SUMMARY_FIELDS))

    @patch("app.services.ai_summary_service.generate_paper_summary_result")
    def test_summary_adapter_drops_unserializable_extra_fields(self, generate):
        summary = {**valid_summary(), "provider_object": object()}
        generate.return_value = (summary, False, "validated-model")
        result = safe_generate_summary("paper")
        self.assertEqual(result["summary"], valid_summary())
        json.dumps(result)

    @patch("app.services.ai_summary_service.generate_paper_summary_result")
    def test_summary_adapter_normalizes_nested_summary(self, generate):
        generate.return_value = ({"summary": valid_summary()}, False, "validated-model")
        self.assertEqual(safe_generate_summary("paper")["summary"], valid_summary())

    @patch("app.services.qa_service.answer_question_about_paper")
    def test_qa_adapter_does_not_mark_unverifiable_result_real(self, answer):
        answer.return_value = {"answer": "answer", "evidence": [], "is_mock": False}
        result = safe_answer_question("question", "paper", 1)
        self.assertTrue(result["is_mock"])
        self.assertEqual(result["failure_reason"], "rag_unavailable")

    @patch("app.services.qa_service.answer_question_about_paper")
    def test_qa_adapter_clears_failure_reason_for_real_result(self, answer):
        answer.return_value = {
            "answer": "supported",
            "evidence": ["source"],
            "is_mock": False,
            "failure_reason": "generation_failure",
        }
        result = safe_answer_question("question", "paper", 1, 2)
        self.assertFalse(result["is_mock"])
        self.assertIsNone(result["failure_reason"])

    @patch("app.services.qa_service.answer_question_about_paper")
    def test_qa_adapter_normalizes_non_list_evidence(self, answer):
        answer.return_value = {"answer": "supported", "evidence": "source", "is_mock": False}
        result = safe_answer_question("question", "paper", 1, 2)
        self.assertEqual(result["evidence"], ["source"])
        self.assertFalse(result["is_mock"])

    @patch("app.services.compare_service.compare_papers")
    def test_compare_adapter_preserves_service_fallback(self, compare):
        papers = [{"paper_id": 1, "title": "A"}, {"paper_id": 2, "title": "B"}]
        compare.return_value = {
            "comparison_table": [
                {"paper_id": 1, "title": "A", "method": "unavailable"},
                {"paper_id": 2, "title": "B", "method": "unavailable"},
            ],
            "summary": "service fallback",
            "is_mock": True,
        }
        result = safe_compare_papers(papers, ["method"])
        self.assertEqual(result["summary"], "service fallback")
        self.assertTrue(result["is_mock"])


class CompareServiceTests(unittest.TestCase):
    def setUp(self):
        self.papers = [
            {"paper_id": 1, "title": "Paper A", "full_text": "method A"},
            {"paper_id": 2, "title": "Paper B", "full_text": "method B"},
        ]

    @patch("app.services.compare_service.chat_with_deepseek")
    def test_valid_comparison_is_real_and_ordered(self, chat):
        chat.return_value = json.dumps({
            "comparison_table": [
                {"paper_id": 2, "method": "B"},
                {"paper_id": 1, "method": "A"},
            ],
            "summary": "comparison",
        })
        result = compare_papers(self.papers, ["method"])
        self.assertFalse(result["is_mock"])
        self.assertEqual([row["paper_id"] for row in result["comparison_table"]], [1, 2])

    @patch("app.services.compare_service.chat_with_deepseek", return_value='{"comparison_table":[],"summary":"x"}')
    def test_malformed_comparison_uses_complete_fallback(self, _chat):
        result = compare_papers(self.papers, ["method", "result"])
        self.assertTrue(result["is_mock"])
        self.assertEqual(len(result["comparison_table"]), 2)
        self.assertTrue(all(row["method"] and row["result"] for row in result["comparison_table"]))

    @patch("app.services.compare_service.chat_with_deepseek")
    def test_provider_failure_uses_fallback(self, chat):
        chat.side_effect = LLMServiceError(AIErrorReason.TIMEOUT, "timeout")
        self.assertTrue(compare_papers(self.papers, ["method"])["is_mock"])

    def test_schema_rejects_reserved_long_and_boolean_fields(self):
        invalid_payloads = (
            {"paper_ids": [True, 2], "compare_dimensions": ["method"]},
            {"paper_ids": [1, 2], "compare_dimensions": ["paper_id"]},
            {"paper_ids": [1, 2], "compare_dimensions": ["x" * 101]},
            {"paper_ids": [1, 2], "compare_dimensions": ["method", " "]},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ComparePapersRequest(**payload)


class ResearchPlanTests(unittest.TestCase):
    @patch("app.services.agent_service.chat_with_deepseek")
    def test_valid_plan_is_real_and_normalized(self, chat):
        chat.return_value = json.dumps(valid_plan())
        result = generate_research_plan(" topic ", " beginner ", 2)
        self.assertEqual(result["topic"], "topic")
        self.assertFalse(result["is_mock"])
        self.assertEqual([item["week"] for item in result["weekly_plan"]], [1, 2])

    @patch("app.services.agent_service.chat_with_deepseek", return_value='{"stages": []}')
    def test_incomplete_plan_uses_stable_fallback(self, _chat):
        result = generate_research_plan("topic", "beginner", 3)
        self.assertTrue(result["is_mock"])
        self.assertEqual(len(result["weekly_plan"]), 3)
        self.assertTrue(result["stages"] and result["risks"])

    @patch("app.services.agent_service.chat_with_deepseek")
    def test_provider_failure_uses_stable_fallback(self, chat):
        chat.side_effect = LLMServiceError(AIErrorReason.TIMEOUT, "AI 服务请求超时")
        result = generate_research_plan("topic", "beginner", 1)
        self.assertTrue(result["is_mock"])

    def test_service_rejects_empty_topic_and_invalid_duration(self):
        with self.assertRaises(ValueError):
            generate_research_plan("  ", "beginner", 2)
        with self.assertRaises(ValueError):
            generate_research_plan("topic", "beginner", 0)

    def test_schema_rejects_blank_topic_level_and_invalid_duration(self):
        for payload in (
            {"topic": " ", "level": "beginner", "duration_weeks": 2},
            {"topic": "topic", "level": " ", "duration_weeks": 2},
            {"topic": "topic", "level": "beginner", "duration_weeks": 53},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ResearchPlanRequest(**payload)


class QAServiceTests(unittest.TestCase):
    def test_schema_and_service_reject_empty_question(self):
        with self.assertRaises(ValidationError):
            QARequest(question=" \n ")
        with self.assertRaises(ValueError):
            answer_question_about_paper(" ", "paper", 1)

    @patch("app.services.qa_service.chat_with_deepseek", return_value='{"answer":"direct answer"}')
    @patch("app.services.qa_service.validate_vector_store", side_effect=FileNotFoundError("missing"))
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_missing_index_uses_bounded_direct_context(self, embedding, _validate, _chat):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertIsNone(result["failure_reason"])
        self.assertFalse(result["is_mock"])
        self.assertEqual(result["evidence"], ["paper"])
        embedding.assert_not_called()

    @patch("app.services.qa_service.validate_vector_store")
    @patch("app.services.qa_service.chat_with_deepseek")
    @patch("app.services.qa_service.search_similar_chunks_with_scores", return_value=[])
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_empty_retrieval_does_not_call_llm(self, _embedding, _search, chat, _validate):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertEqual(result["failure_reason"], "empty_retrieval")
        chat.assert_not_called()

    @patch("app.services.qa_service.validate_vector_store")
    @patch("app.services.qa_service.search_similar_chunks_with_scores", side_effect=VectorStoreError("dependency"))
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_vector_dependency_failure_is_not_mislabeled_as_corruption(self, _embedding, _search, _validate):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertEqual(result["failure_reason"], "rag_unavailable")

    @patch("app.services.qa_service.validate_vector_store")
    @patch("app.services.qa_service.chat_with_deepseek", return_value='{"answer":"supported"}')
    @patch("app.services.qa_service.search_similar_chunks_with_scores", return_value=[
        RetrievedChunk("chunk 1", 0, 0.1), RetrievedChunk("chunk 2", 2, 0.2)
    ])
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_successful_rag_answer(self, _embedding, _search, _chat, _validate):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertEqual(result["answer"], "supported")
        self.assertEqual(result["evidence"], ["chunk 1", "chunk 2"])
        self.assertFalse(result["is_mock"])
        self.assertIsNone(result["failure_reason"])

    @patch("app.services.qa_service.validate_vector_store")
    @patch("app.services.qa_service.chat_with_deepseek", return_value="malformed")
    @patch("app.services.qa_service.search_similar_chunks_with_scores", return_value=[
        RetrievedChunk("retrieved chunk", 3, 0.1)
    ])
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_llm_failure_after_retrieval_is_marked_mock(self, _embedding, _search, _chat, _validate):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertEqual(result["failure_reason"], "generation_failure")
        self.assertEqual(result["evidence"], ["retrieved chunk"])
        self.assertTrue(result["is_mock"])


if __name__ == "__main__":
    unittest.main()
