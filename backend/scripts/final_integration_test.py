"""End-to-end HTTP verification for the complete local application contract."""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import fitz
import requests


def positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("request timeout must be a number") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("request timeout must be greater than zero")
    return timeout


class Client:
    def __init__(self, base_url: str, request_timeout: float):
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        step: str,
        *,
        expected_status: int = 200,
        **kwargs: Any,
    ) -> Any:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            timeout=(10.0, self.request_timeout),
            **kwargs,
        )
        try:
            body = response.json()
        except ValueError as exc:
            raise AssertionError(f"{step}: non-JSON response (HTTP {response.status_code})") from exc
        if response.status_code != expected_status or body.get("code") != expected_status:
            raise AssertionError(
                f"{step}: HTTP {response.status_code}, code={body.get('code')}, "
                f"message={body.get('message')}"
            )
        print(f"[PASS] {step}")
        return body.get("data")


def create_user(client: Client, label: str) -> dict[str, Any]:
    suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    username = f"final_{label}_{suffix}"
    password = "Local-test-123456"
    client.request(
        "POST",
        "/api/auth/register",
        f"register user {label}",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    login = client.request(
        "POST",
        "/api/auth/login",
        f"login user {label}",
        json={"username": username, "password": password},
    )
    token = login.get("token")
    if not isinstance(token, str) or not token:
        raise AssertionError(f"login user {label}: token is missing")
    client.session.headers["Authorization"] = f"Bearer {token}"
    current = client.request("GET", "/api/auth/me", f"current user {label}")
    if current.get("username") != username:
        raise AssertionError(f"current user {label}: identity mismatch")
    return current


def write_pdf(path: Path, title: str, body: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 545, 790), f"{title}\n\n{body}", fontsize=11)
    document.set_metadata({"title": title, "author": "Final integration test"})
    document.save(path)
    document.close()


def upload_papers(client: Client) -> list[int]:
    fixtures = [
        (
            "RAG Transformer Foundations",
            "Retrieval augmented generation uses Transformer embeddings, attention, and vector retrieval.",
        ),
        (
            "RAG Transformer Evaluation",
            "We evaluate retrieval augmented generation with Transformer embeddings and vector retrieval. "
            "References: RAG Transformer Foundations.",
        ),
        (
            "RAG Transformer Applications",
            "Academic applications use retrieval augmented generation, Transformer attention, embeddings, "
            "and vector retrieval. References: RAG Transformer Evaluation.",
        ),
    ]
    paper_ids: list[int] = []
    with tempfile.TemporaryDirectory(prefix="final-integration-") as temp_dir:
        for number, (title, body) in enumerate(fixtures, start=1):
            path = Path(temp_dir) / f"paper-{number}.pdf"
            write_pdf(path, title, body)
            with path.open("rb") as source:
                paper = client.request(
                    "POST",
                    "/api/papers/upload",
                    f"upload paper {number}",
                    files={"file": (path.name, source, "application/pdf")},
                )
            paper_ids.append(int(paper["paper_id"]))
    return paper_ids


def require_items(value: Any, step: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise AssertionError(f"{step}: expected a non-empty list")
    return value


def run(base_url: str, request_timeout: float) -> None:
    anonymous = Client(base_url, request_timeout)
    anonymous.request("GET", "/api/health", "health")
    anonymous.request("GET", "/api/auth/me", "anonymous authentication rejection", expected_status=401)

    owner = Client(base_url, request_timeout)
    other = Client(base_url, request_timeout)
    create_user(owner, "owner")
    create_user(other, "other")
    paper_ids = upload_papers(owner)
    first, second, third = paper_ids

    papers = require_items(owner.request("GET", "/api/papers", "paper list"), "paper list")
    if not set(paper_ids) <= {int(item["paper_id"]) for item in papers}:
        raise AssertionError("paper list: uploaded records are missing")
    owner.request("GET", f"/api/papers/{first}", "paper detail")
    owner.request("PUT", f"/api/papers/{first}", "paper update", json={"venue": "Local Test Venue"})
    owner.request(
        "PUT", f"/api/papers/{first}/status", "reading status", json={"read_status": "rough_read"}
    )
    tag = owner.request("POST", "/api/tags", "create tag", json={"name": f"rag-{uuid.uuid4().hex[:8]}"})
    owner.request("POST", f"/api/papers/{first}/tags", "attach tag", json={"tag_name": tag["name"]})
    require_items(owner.request("GET", "/api/tags", "tag list"), "tag list")
    owner.request("DELETE", f"/api/papers/{first}/tags/{tag['id']}", "detach tag")

    summary = owner.request("POST", f"/api/papers/{first}/summary", "AI summary")
    if not isinstance(summary.get("is_mock"), bool):
        raise AssertionError("AI summary: is_mock must be boolean")
    require_items(
        owner.request("GET", f"/api/papers/{first}/summaries", "summary history"),
        "summary history",
    )
    qa = owner.request(
        "POST",
        f"/api/papers/{first}/qa",
        "paper question answering",
        json={"question": "What method does this paper use?"},
    )
    if not isinstance(qa.get("answer"), str) or not isinstance(qa.get("evidence"), list):
        raise AssertionError("paper question answering: invalid answer/evidence shape")
    require_items(
        owner.request("GET", f"/api/papers/{first}/qa-records", "QA history"),
        "QA history",
    )

    comparison = owner.request(
        "POST",
        "/api/papers/compare",
        "paper comparison",
        json={
            "paper_ids": paper_ids,
            "compare_dimensions": ["problem", "method", "dataset", "result", "limitation"],
        },
    )
    if not comparison.get("comparison_table") and not comparison.get("summary"):
        raise AssertionError("paper comparison: empty result")
    require_items(owner.request("GET", "/api/papers/comparisons", "comparison history"), "comparison history")

    graph = owner.request(
        "POST",
        "/api/graph/generate",
        "graph generation",
        json={
            "paper_ids": paper_ids,
            "relation_types": ["citation", "topic_similarity", "method_similarity"],
            "force_regenerate": True,
        },
    )
    relation_types = {edge.get("relation_type") for edge in graph.get("edges", [])}
    if not {"citation", "topic_similarity", "method_similarity"} <= relation_types:
        raise AssertionError(f"graph generation: missing relation types {relation_types}")
    require_items(owner.request("GET", "/api/graph/papers", "graph query").get("nodes"), "graph nodes")
    require_items(owner.request("GET", "/api/graph/relations", "relation query"), "relation query")

    plan = owner.request(
        "POST",
        "/api/agent/research-plan",
        "research plan",
        json={
            "research_topic": "RAG for academic research",
            "research_goal": "Build and evaluate a local prototype",
            "duration_weeks": 4,
            "current_level": "undergraduate",
            "paper_ids": paper_ids,
        },
    )
    if not isinstance(plan.get("plan_id"), int) or not isinstance(plan.get("is_mock"), bool):
        raise AssertionError("research plan: invalid plan_id/is_mock")
    require_items(owner.request("GET", "/api/agent/research-plans", "plan history"), "plan history")
    owner.request("GET", f"/api/agent/research-plans/{plan['plan_id']}", "plan detail")

    other.request("GET", f"/api/papers/{first}", "foreign paper detail rejected", expected_status=404)
    other.request(
        "POST",
        "/api/papers/compare",
        "foreign comparison rejected",
        expected_status=404,
        json={
            "paper_ids": [first, second],
            "compare_dimensions": ["problem", "method"],
        },
    )
    other.request(
        "POST",
        "/api/graph/generate",
        "foreign graph rejected",
        expected_status=404,
        json={"paper_ids": paper_ids},
    )
    other.request(
        "GET",
        f"/api/agent/research-plans/{plan['plan_id']}",
        "foreign plan rejected",
        expected_status=404,
    )

    for paper_id in (third, second, first):
        owner.request("DELETE", f"/api/papers/{paper_id}", f"cleanup paper {paper_id}")
    print("FINAL_INTEGRATION_TEST_OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--request-timeout", type=positive_timeout, default=120.0)
    args = parser.parse_args()
    try:
        run(args.base_url, args.request_timeout)
    except (AssertionError, KeyError, TypeError, requests.RequestException) as exc:
        print(f"FINAL_INTEGRATION_TEST_FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
