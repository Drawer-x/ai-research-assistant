"""Sprint 3 local HTTP smoke test; requires a running backend."""

import argparse
import sys
import tempfile
import time
from pathlib import Path

import requests
import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings


def positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("request timeout 必须是正数") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("request timeout 必须大于 0")
    return timeout


def default_request_timeout() -> float:
    return max(120.0, float(settings.ecnu_api_timeout_seconds) + 30.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sprint 3 backend smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--request-timeout", type=positive_timeout, default=default_request_timeout())
    return parser


class SmokeClient:
    def __init__(self, base_url: str, request_timeout: float):
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def request(self, method: str, path: str, step: str, expected_status: int = 200, **kwargs):
        try:
            response = self.session.request(
                method, f"{self.base_url}{path}", timeout=(10.0, self.request_timeout), **kwargs
            )
        except requests.Timeout as exc:
            raise AssertionError(
                f"{step}: 请求超时（read timeout={self.request_timeout}s）；上游模型可能响应较慢"
            ) from exc
        except requests.ConnectionError as exc:
            raise AssertionError(f"{step}: 无法连接本地后端") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise AssertionError(f"{step}: 返回非 JSON（HTTP {response.status_code}）") from exc
        if response.status_code != expected_status or body.get("code") != expected_status:
            raise AssertionError(
                f"{step}: HTTP {response.status_code}, code={body.get('code')}, message={body.get('message')}"
            )
        print(f"[PASS] {step}")
        return body.get("data")


def create_user(client: SmokeClient, suffix: str) -> None:
    username = f"sprint3_{suffix}_{int(time.time() * 1000)}"
    password = "123456"
    client.request("POST", "/api/auth/register", f"注册 {suffix}", json={
        "username": username, "email": f"{username}@example.com", "password": password})
    login = client.request("POST", "/api/auth/login", f"登录 {suffix}", json={
        "username": username, "password": password})
    client.session.headers["Authorization"] = f"Bearer {login['token']}"


def write_test_pdf(path: Path, title: str, body: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(
        fitz.Rect(50, 50, 545, 790),
        f"{title}\n\n{body}",
        fontsize=11,
    )
    document.set_metadata({"title": title, "author": "Sprint 3 integration test"})
    document.save(path)
    document.close()


def run(base_url: str, request_timeout: float) -> None:
    owner = SmokeClient(base_url, request_timeout)
    owner.request("GET", "/api/health", "健康检查")
    create_user(owner, "owner")
    paper_ids = []
    with tempfile.TemporaryDirectory(prefix="sprint3-") as temp_dir:
        fixtures = [
            (
                "RAG Transformer Foundations",
                "Retrieval augmented generation with Transformer embeddings. "
                "This paper studies vector retrieval and attention for academic research.",
            ),
            (
                "RAG Transformer Evaluation",
                "We evaluate retrieval augmented generation with Transformer embeddings "
                "and vector retrieval. References: RAG Transformer Foundations.",
            ),
            (
                "RAG Transformer Applications",
                "Academic research applications use retrieval augmented generation, "
                "Transformer attention, embeddings, and vector retrieval. "
                "References: RAG Transformer Evaluation.",
            ),
        ]
        for number, (title, body) in enumerate(fixtures, start=1):
            path = Path(temp_dir) / f"paper-{number}.pdf"
            write_test_pdf(path, title, body)
            with path.open("rb") as source:
                paper = owner.request("POST", "/api/papers/upload", f"上传论文 {number}",
                    files={"file": (path.name, source, "application/pdf")})
            paper_ids.append(paper["paper_id"])
    papers = owner.request("GET", "/api/papers", "论文列表")
    assert set(paper_ids) <= {paper["paper_id"] for paper in papers}
    generated = owner.request("POST", "/api/graph/generate", "生成关系图", json={
        "paper_ids": paper_ids,
        "relation_types": ["citation", "topic_similarity", "method_similarity"],
        "force_regenerate": False})
    assert len(generated["nodes"]) >= 3 and generated["edges"]
    relation_types = {edge["relation_type"] for edge in generated["edges"]}
    assert {"citation", "topic_similarity", "method_similarity"} <= relation_types
    graph = owner.request("GET", "/api/graph/papers", "查询关系图")
    assert graph["nodes"] and graph["edges"]
    owner.request("GET", "/api/graph/relations", "查询关系列表")
    plan = owner.request("POST", "/api/agent/research-plan", "生成科研计划", json={
        "research_topic": "RAG literature analysis", "research_goal": "prototype",
        "duration_weeks": 3, "current_level": "undergraduate", "paper_ids": paper_ids})
    print(f"[INFO] Agent result is_mock={bool(plan.get('is_mock', True))}")
    history = owner.request("GET", "/api/agent/research-plans", "计划历史")
    assert history and history[0]["plan_id"] == plan["plan_id"]
    owner.request("GET", f"/api/agent/research-plans/{plan['plan_id']}", "计划详情")
    other = SmokeClient(base_url, request_timeout)
    create_user(other, "other")
    other.request("POST", "/api/graph/generate", "跨用户关系拒绝", 404, json={"paper_ids": paper_ids})
    other.request("GET", f"/api/agent/research-plans/{plan['plan_id']}", "跨用户计划拒绝", 404)
    print("\nSPRINT3_SMOKE_TEST_OK")


def main() -> int:
    args = build_parser().parse_args()
    try:
        run(args.base_url, args.request_timeout)
    except (AssertionError, KeyError) as exc:
        print(f"SPRINT3_SMOKE_TEST_FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
