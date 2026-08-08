import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.api import agent, discovery, papers, recommendations
from app.core.response import error_response
from app.core.security import get_current_user
from app.database import Base, _enable_sqlite_foreign_keys, get_db
from app.models.paper import Paper
from app.models.paper_external_source import PaperExternalSource
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
        cls.app.include_router(discovery.router, prefix="/api")
        cls.app.include_router(recommendations.router, prefix="/api")

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

    def test_sqlite_connections_enable_foreign_keys(self):
        connection = sqlite3.connect(":memory:")
        try:
            _enable_sqlite_foreign_keys(connection, None)
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        finally:
            connection.close()

    def test_delete_paper_explicitly_removes_external_source(self):
        paper = self.add_paper()
        source = PaperExternalSource(
            user_id=self.user.id,
            paper_id=paper.id,
            provider="crossref",
            external_id="10.1000/delete-test",
        )
        self.db.add(source)
        self.db.commit()
        response = self.client.delete(f"/api/papers/{paper.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperExternalSource)), 0)

    def test_discovery_import_integrity_conflict_returns_409_and_rolls_back(self):
        error = IntegrityError("insert", {}, Exception("conflict"))
        with patch("app.api.discovery.import_external_paper", side_effect=error):
            response = self.client.post(
                "/api/discovery/import",
                json={"provider": "crossref", "external_id": "10.1000/conflict"},
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("文献关联记录冲突", response.json()["message"])

    def test_recommendation_by_local_paper_falls_back_when_crossref_id_is_missing(self):
        paper = self.add_paper(full_text="transformer forecasting with temporal attention")
        paper.title = "transformer"
        self.db.commit()
        candidate = {
            "provider": "crossref",
            "external_id": "10.1000/candidate",
            "title": "Transformer Forecasting Methods",
            "abstract": "temporal attention forecasting",
            "authors": [],
            "year": 2025,
            "venue": "Test Venue",
            "doi": "10.1000/candidate",
            "citation_count": 5,
            "fields_of_study": [],
        }
        with (
            patch("app.services.recommendation_orchestration_service.resolve_local_paper_external_id", return_value=None),
            patch("app.services.recommendation_orchestration_service.CrossrefClient") as client_class,
        ):
            client_class.return_value.search_papers.return_value = {"items": [candidate]}
            response = self.client.post(
                "/api/recommendations/by-paper",
                json={"paper_id": paper.id, "limit": 20},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        client_class.return_value.get_work.assert_not_called()

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
    def test_external_paper_summary_prefers_attached_full_text(self, generate):
        paper = Paper(
            user_id=self.user.id,
            title="External Paper",
            pdf_path="external://crossref/10.1000/test",
            full_text="attached external full text",
            parse_status="success",
        )
        self.db.add(paper)
        self.db.commit()
        generate.return_value = {
            "summary": {field: f"value {field}" for field in SUMMARY_FIELDS},
            "is_mock": False,
            "model_name": "test-model",
        }
        response = self.client.post(f"/api/papers/{paper.id}/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["analysis_scope"], "full_text")
        generate.assert_called_once_with("attached external full text")

    @patch("app.api.papers.safe_answer_question")
    def test_external_paper_qa_uses_attached_full_text(self, answer):
        paper = Paper(
            user_id=self.user.id,
            title="External Paper",
            pdf_path="external://crossref/10.1000/test",
            full_text="attached external full text",
            parse_status="success",
        )
        self.db.add(paper)
        self.db.commit()
        answer.return_value = {
            "answer": "answer from full text",
            "evidence": ["evidence"],
            "has_evidence": True,
            "is_mock": False,
            "failure_reason": None,
        }
        response = self.client.post(f"/api/papers/{paper.id}/qa", json={"question": "question"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["analysis_scope"], "full_text")
        answer.assert_called_once_with(
            "question",
            "attached external full text",
            paper_id=paper.id,
            user_id=self.user.id,
        )

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
        with patch("app.api.agent.safe_generate_research_plan", return_value={
            "reading_route": [], "stages": fallback["stages"], "weekly_plan": fallback["weekly_plan"],
            "tasks": [], "risks": fallback["risks"], "recommended_papers": [], "is_mock": True,
        }):
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

    def test_external_paper_pdf_is_attached_without_creating_a_duplicate(self):
        paper = Paper(
            user_id=self.user.id,
            title="Imported Paper",
            pdf_path="external://crossref/10.1000/imported",
            full_text=None,
            parse_status="external",
        )
        self.db.add(paper)
        self.db.commit()
        parsed = {"full_text": "parsed imported paper", "abstract": "parsed abstract"}
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(papers.settings, "upload_dir", temp_dir),
                patch("app.api.papers.extract_text_from_pdf", return_value=parsed),
                patch("app.api.papers._build_vector_store") as build_index,
            ):
                response = self.client.post(
                    f"/api/papers/{paper.id}/pdf",
                    files={"file": ("paper.pdf", b"%PDF-1.4 test", "application/pdf")},
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Paper)), 1)
        self.db.refresh(paper)
        self.assertEqual(paper.full_text, "parsed imported paper")
        self.assertEqual(paper.parse_status, "success")
        build_index.assert_called_once_with(paper.id, self.user.id, "parsed imported paper")


if __name__ == "__main__":
    unittest.main()
