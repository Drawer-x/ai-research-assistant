import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


def chat_with_deepseek(prompt: str):
    """Call the optional ECNU model without making application import depend on it."""
    api_key = os.getenv("ECNU_API_KEY")
    if not api_key:
        raise RuntimeError("ECNU_API_KEY 未配置")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 依赖未安装") from exc
    client = OpenAI(api_key=api_key, base_url="https://chat.ecnu.edu.cn/open/api/v1")
    response = client.chat.completions.create(
        model="ecnu-max",
        messages=[
            {
                "role":"system",
                "content":"你是一名专业科研助手"
            },
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
