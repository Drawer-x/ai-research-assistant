"""Opt-in, privacy-safe diagnostics for the three ChatECNU business services."""

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services.ai_summary_service import generate_paper_summary_result
from app.services.compare_service import compare_papers
from app.services.qa_service import answer_question_about_paper


PAPER_TEXT = (
    "本文研究小样本图像分类问题，提出带注意力机制的轻量模型。"
    "实验在公开数据集上进行，相比基线准确率提高两个百分点。"
    "局限性是实验规模较小。"
)


def _text_chars(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, dict):
        return sum(_text_chars(item) for item in value.values())
    if isinstance(value, list):
        return sum(_text_chars(item) for item in value)
    return 0


def _report(name: str, call: Callable[[], Any]) -> bool:
    try:
        value = call()
        if name == "summary":
            result, is_mock, model = value
            fields = sorted(result)
            print(f"[{name}] success={not is_mock} is_mock={is_mock} fields={fields} text_chars={_text_chars(result)} model={model}")
            return not is_mock
        result = value
        fields = sorted(result) if isinstance(result, dict) else []
        print(f"[{name}] success={not result.get('is_mock', True)} is_mock={result.get('is_mock', True)} fields={fields} text_chars={_text_chars(result)}")
        failure_reason = result.get("failure_reason")
        if failure_reason:
            print(f"[{name}] safe_reason={failure_reason}")
        return result.get("is_mock") is False
    except Exception as exc:
        reason = getattr(getattr(exc, "reason", None), "value", type(exc).__name__)
        print(f"[{name}] success=False is_mock=True safe_reason={reason}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatECNU business-flow diagnostics")
    parser.add_argument("--live", action="store_true", help="explicitly call the real ChatECNU API")
    args = parser.parse_args()
    if not args.live:
        print("未发送请求。仅添加 --live 才会测试真实 ChatECNU 业务调用。")
        return 0
    print(f"ECNU_API_KEY configured: {bool(settings.ecnu_api_key)}")
    if not settings.ecnu_api_key:
        return 2

    summary_real = _report("summary", lambda: generate_paper_summary_result(PAPER_TEXT))
    _report("qa", lambda: answer_question_about_paper("论文采用了什么方法？", PAPER_TEXT))
    papers = [
        {"paper_id": 1, "title": "轻量注意力模型", "full_text": PAPER_TEXT},
        {"paper_id": 2, "title": "卷积基线", "full_text": "本文使用卷积网络完成图像分类，实验结果作为基线。"},
    ]
    _report("compare", lambda: compare_papers(papers, ["problem", "method", "result", "limitation"]))
    return 0 if summary_real else 1


if __name__ == "__main__":
    raise SystemExit(main())
