import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


api_key = os.getenv("ECNU_API_KEY")


if not api_key:
    raise ValueError(
        "没有找到 ECNU_API_KEY，请检查 backend/.env"
    )


client = OpenAI(
    api_key=api_key,
    base_url="https://chat.ecnu.edu.cn/open/api/v1"
)


def chat_with_deepseek(prompt:str):

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