import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from app.schemas.agent import ResearchPlanRequest
from app.schemas.ai import ComparePapersRequest, QARequest
from app.services.agent_service import generate_research_plan
from app.services.ai_adapter_service import safe_answer_question, safe_generate_summary
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
    def tearDown(self):
        llm_client._get_client.cache_clear()

    def test_missing_key_has_typed_reason(self):
        llm_client._get_client.cache_clear()
        with patch.object(llm_client.settings, "ecnu_api_key", None):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client._get_client()
        self.assertEqual(caught.exception.reason, AIErrorReason.MISSING_CONFIGURATION)

    def test_missing_dependency_has_typed_reason(self):
        real_import = __import__

        def import_without_openai(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("not installed")
            return real_import(name, *args, **kwargs)

        llm_client._get_client.cache_clear()
        with (
            patch.object(llm_client.settings, "ecnu_api_key", "configured"),
            patch("builtins.__import__", side_effect=import_without_openai),
        ):
            with self.assertRaises(LLMServiceError) as caught:
                llm_client._get_client()
        self.assertEqual(caught.exception.reason, AIErrorReason.DEPENDENCY_MISSING)

    @patch("app.services.llm_client._get_client")
    def test_timeout_is_mapped_without_provider_details(self, get_client):
        create = get_client.return_value.chat.completions.create
        create.side_effect = TimeoutError("secret provider detail")
        with self.assertRaises(LLMServiceError) as caught:
            llm_client.chat_with_deepseek("prompt")
        self.assertEqual(caught.exception.reason, AIErrorReason.TIMEOUT)
        self.assertNotIn("secret provider detail", str(caught.exception))

    @patch("app.services.llm_client._get_client")
    def test_empty_model_response_has_typed_reason(self, get_client):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="   "))]
        )
        get_client.return_value.chat.completions.create.return_value = response
        with self.assertRaises(LLMServiceError) as caught:
            llm_client.chat_with_deepseek("prompt")
        self.assertEqual(caught.exception.reason, AIErrorReason.EMPTY_RESPONSE)


class SummaryServiceTests(unittest.TestCase):
    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_successful_structured_summary_is_real(self, chat):
        chat.return_value = json.dumps(valid_summary())
        summary, is_mock, model_name = generate_paper_summary_result("paper body")
        self.assertEqual(summary, valid_summary())
        self.assertFalse(is_mock)
        self.assertTrue(model_name)

    @patch("app.services.ai_summary_service.chat_with_deepseek", return_value="not json")
    def test_malformed_json_uses_complete_fallback(self, _chat):
        summary, is_mock, model_name = generate_paper_summary_result("paper body")
        self.assertEqual(set(summary), set(SUMMARY_FIELDS))
        self.assertTrue(all(summary.values()))
        self.assertTrue(is_mock)
        self.assertEqual(model_name, "local-fallback")

    @patch("app.services.ai_summary_service.chat_with_deepseek")
    def test_missing_field_is_not_marked_real(self, chat):
        incomplete = valid_summary()
        incomplete.pop("limitation")
        chat.return_value = json.dumps(incomplete)
        _, is_mock, _ = generate_paper_summary_result("paper body")
        self.assertTrue(is_mock)

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
    def test_summary_adapter_rejects_incomplete_real_result(self, generate):
        generate.return_value = ({"background": "only one field"}, False, "model")
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

    @patch("app.services.qa_service.validate_vector_store", side_effect=FileNotFoundError("missing"))
    @patch("app.services.qa_service.get_embedding", return_value=[0.1, 0.2])
    def test_missing_index_is_controlled(self, embedding, _validate):
        result = answer_question_about_paper("question", "paper", 1)
        self.assertEqual(result["failure_reason"], "missing_index")
        self.assertTrue(result["is_mock"])
        self.assertEqual(result["evidence"], [])
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
