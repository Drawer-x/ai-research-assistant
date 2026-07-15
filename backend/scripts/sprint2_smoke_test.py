"""Sprint 2 HTTP smoke test. Start the backend before running this script."""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import requests


def expect(response: requests.Response, step: str):
    try:
        body = response.json()
    except ValueError as exc:
        raise AssertionError(f"{step} 返回非 JSON：{response.status_code} {response.text}") from exc
    if response.status_code != 200 or body.get("code") != 200:
        raise AssertionError(f"{step} 失败：HTTP {response.status_code}，响应 {body}")
    print(f"[PASS] {step}")
    return body.get("data")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sprint 2 backend smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    session = requests.Session()

    expect(session.get(f"{base_url}/api/health", timeout=10), "健康检查")
    unique = str(int(time.time() * 1000))
    username = f"sprint2_smoke_{unique}"
    password = "123456"
    expect(session.post(
        f"{base_url}/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
        timeout=10,
    ), "注册")
    login = expect(session.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    ), "登录")
    session.headers.update({"Authorization": f"Bearer {login['token']}"})
    expect(session.get(f"{base_url}/api/auth/me", timeout=10), "JWT 鉴权")

    paper_ids: list[int] = []
    with tempfile.TemporaryDirectory(prefix="sprint2-smoke-") as temp_dir:
        for number in (1, 2):
            path = Path(temp_dir) / f"sprint2-paper-{number}.pdf"
            path.write_bytes(b"%PDF-1.4\nSprint 2 fallback smoke test\n%%EOF")
            with path.open("rb") as source:
                paper = expect(session.post(
                    f"{base_url}/api/papers/upload",
                    files={"file": (path.name, source, "application/pdf")},
                    timeout=30,
                ), f"上传测试 PDF {number}")
            paper_ids.append(paper["paper_id"])

    papers = expect(session.get(f"{base_url}/api/papers", timeout=10), "文献列表")
    if not all(paper_id in {item["paper_id"] for item in papers} for paper_id in paper_ids):
        raise AssertionError(f"文献列表缺少上传记录：{paper_ids}")

    first_paper_id = paper_ids[0]
    expect(session.post(f"{base_url}/api/papers/{first_paper_id}/summary", timeout=30), "生成总结")
    summaries = expect(session.get(
        f"{base_url}/api/papers/{first_paper_id}/summaries", timeout=10,
    ), "总结历史")
    if not summaries:
        raise AssertionError("总结历史为空")

    qa = expect(session.post(
        f"{base_url}/api/papers/{first_paper_id}/qa",
        json={"question": "这篇论文解决了什么问题？"},
        timeout=30,
    ), "论文问答")
    if not all(key in qa for key in ("answer", "evidence", "has_evidence", "is_mock")):
        raise AssertionError(f"QA 返回结构不完整：{qa}")
    records = expect(session.get(
        f"{base_url}/api/papers/{first_paper_id}/qa-records", timeout=10,
    ), "问答历史")
    if not records:
        raise AssertionError("问答历史为空")

    comparison = expect(session.post(
        f"{base_url}/api/papers/compare",
        json={
            "paper_ids": paper_ids,
            "compare_dimensions": ["problem", "method", "dataset", "result", "limitation"],
        },
        timeout=30,
    ), "多论文对比")
    if not comparison.get("comparison_table") and not comparison.get("summary"):
        raise AssertionError(f"对比结果结构不完整：{comparison}")
    history = expect(session.get(f"{base_url}/api/papers/comparisons", timeout=10), "对比历史")
    if not history:
        raise AssertionError("对比历史为空")

    print(f"\nSprint 2 冒烟测试全部通过，paper_ids={paper_ids}")


if __name__ == "__main__":
    main()
