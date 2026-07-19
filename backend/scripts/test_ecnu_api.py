"""Opt-in ChatECNU connectivity check; never sends a request by default."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services.ai_errors import AIServiceError
from app.services.llm_client import chat_completion


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatECNU connectivity check")
    parser.add_argument("--live", action="store_true", help="explicitly send one minimal request")
    args = parser.parse_args()
    if not args.live:
        print("未发送请求。仅在明确需要真实连通性测试时添加 --live。")
        return 0
    if not settings.ecnu_api_key:
        print("未配置 ECNU_API_KEY；请在 backend/.env 中配置后重试。")
        return 2
    try:
        content = chat_completion([
            {"role": "system", "content": "你是一个简洁的测试助手。"},
            {"role": "user", "content": "只回复“ECNU API connected”。"},
        ])
    except AIServiceError as exc:
        print(f"连接失败：{exc.reason.value}；{exc}")
        return 1
    print("连接成功")
    print(f"模型：{settings.ecnu_model}")
    print(f"响应预览：{content[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
