import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.api import agent, papers
from app.core.response import error_response
from app.core.security import get_current_user
from app.database import Base, get_db
from app.models.paper import Paper
from app.models.qa_record import QARecord
from app.models.research_plan import ResearchPlan
from app.models.summary import AISummary
from app.models.user import User
from app.services.ai_summary_service import SUMMARY_FIELDS


class AIRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        Base.metadata.create_all(cls.engine)
        cls.app = FastAPI()

        @cls.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            errors = "; ".join(error["msg"] for error in exc.errors())
            return error_response(f"请求参数错误: {errors}", 422)

        cls.app.include_router(papers.router, prefix="/api")
        cls.app.include_router(agent.router, prefix="/api")

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.user = User(username="owner", email="owner@example.com", password_hash="hash")
        self.other = User(username="other", email="other@example.com", password_hash="hash")
        self.db.add_all([self.user, self.other])
        self.db.commit()

        def override_db():
            yield self.db

        self.app.dependency_overrides[get_db] = override_db
        self.app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()
        self.db.close()

    def add_paper(self, user: User | None = None, *, full_text: str = "paper body") -> Paper:
        paper = Paper(
            user_id=(user or self.user).id,
            title="Test Paper",
            pdf_path="uploads/test.pdf",
            full_text=full_text,
            parse_status="success",
        )
        self.db.add(paper)
        self.db.commit()
        return paper

    def test_qa_rejects_blank_question_at_api_boundary(self):
        paper = self.add_paper()
        response = self.client.post(f"/api/papers/{paper.id}/qa", json={"question": "   "})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(QARecord)), 0)

    @patch("app.api.papers.safe_answer_question")
    def test_qa_never_reads_another_users_index(self, answer):
        paper = self.add_paper(self.other)
        response = self.client.post(f"/api/papers/{paper.id}/qa", json={"question": "question"})
        self.assertEqual(response.status_code, 404)
        answer.assert_not_called()

    @patch("app.api.papers.safe_generate_summary")
    def test_summary_persists_real_execution_metadata_and_allows_history(self, generate):
        paper = self.add_paper()
        summary = {field: f"value {field}" for field in SUMMARY_FIELDS}
        generate.return_value = {"summary": summary, "is_mock": False, "model_name": "test-model"}
        first = self.client.post(f"/api/papers/{paper.id}/summary")
        second = self.client.post(f"/api/papers/{paper.id}/summary")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(first.json()["data"]["is_mock"])
        records = self.db.scalars(select(AISummary).order_by(AISummary.id)).all()
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record.model_name == "test-model" and not record.is_mock for record in records))

    @patch("app.api.papers.safe_generate_summary")
    def test_persistence_error_log_does_not_include_exception_body(self, generate):
        paper = self.add_paper()
        generate.return_value = {
            "summary": {field: f"value {field}" for field in SUMMARY_FIELDS},
            "is_mock": False,
            "model_name": "test-model",
        }
        with (
            patch.object(self.db, "commit", side_effect=RuntimeError("sensitive paper content")),
            patch.object(papers.logger, "error") as log_error,
        ):
            response = self.client.post(f"/api/papers/{paper.id}/summary")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("sensitive paper content", repr(log_error.call_args))

    @patch("app.api.papers.safe_answer_question")
    def test_qa_fallback_reason_and_evidence_are_persisted(self, answer):
        paper = self.add_paper()
        answer.return_value = {
            "answer": "generation failed",
            "evidence": ["retrieved chunk"],
            "has_evidence": True,
            "is_mock": True,
            "failure_reason": "generation_failure",
        }
        response = self.client.post(f"/api/papers/{paper.id}/qa", json={"question": "question"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["failure_reason"], "generation_failure")
        answer.assert_called_once_with(
            "question",
            "paper body",
            paper_id=paper.id,
            user_id=self.user.id,
        )
        record = self.db.scalar(select(QARecord))
        self.assertTrue(record.is_mock)
        self.assertEqual(json.loads(record.evidence_json), ["retrieved chunk"])

    @patch("app.api.papers.safe_compare_papers")
    def test_compare_rejects_foreign_paper_before_ai_call(self, compare):
        owned = self.add_paper()
        foreign = self.add_paper(self.other)
        response = self.client.post(
            "/api/papers/compare",
            json={"paper_ids": [owned.id, foreign.id], "compare_dimensions": ["method"]},
        )
        self.assertEqual(response.status_code, 404)
        compare.assert_not_called()

    def test_research_plan_validation_and_fallback_persistence(self):
        invalid = self.client.post(
            "/api/agent/research-plan",
            json={"topic": " ", "level": "beginner", "duration_weeks": 0},
        )
        self.assertEqual(invalid.status_code, 422)
        fallback = {
            "topic": "topic",
            "stages": [{"name": "stage", "tasks": ["task"], "output": "output"}],
            "weekly_plan": [{"week": 1, "goal": "goal", "tasks": ["task"]}],
            "risks": ["risk"],
            "is_mock": True,
        }
        with patch("app.api.agent.generate_research_plan", return_value=fallback):
            response = self.client.post(
                "/api/agent/research-plan",
                json={"topic": "topic", "level": "beginner", "duration_weeks": 1},
            )
        self.assertEqual(response.status_code, 200)
        record = self.db.scalar(select(ResearchPlan))
        self.assertEqual(record.user_id, self.user.id)
        self.assertTrue(record.is_mock)

    def test_index_failure_does_not_lose_uploaded_paper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parsed = {"title": "Uploaded", "full_text": "extracted text", "pages": ["extracted text"]}
            with (
                patch.object(papers.settings, "upload_dir", temp_dir),
                patch("app.api.papers.extract_text_from_pdf", return_value=parsed),
                patch("app.services.embedding_service.get_embeddings", side_effect=RuntimeError("offline")),
                patch.object(papers.logger, "exception"),
            ):
                response = self.client.post(
                    "/api/papers/upload",
                    files={"file": ("paper.pdf", b"%PDF-1.4 test", "application/pdf")},
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["parse_status"], "success")
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Paper)), 1)

    def test_upload_size_limit_rejects_and_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(papers.settings, "upload_dir", temp_dir),
                patch.object(papers.settings, "max_pdf_upload_bytes", 4),
                patch("app.api.papers.extract_text_from_pdf") as parser,
            ):
                response = self.client.post(
                    "/api/papers/upload",
                    files={"file": ("paper.pdf", b"12345", "application/pdf")},
                )
            remaining_files = [path for path in Path(temp_dir).rglob("*") if path.is_file()]
        self.assertEqual(response.status_code, 413)
        parser.assert_not_called()
        self.assertEqual(remaining_files, [])
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Paper)), 0)


if __name__ == "__main__":
    unittest.main()
