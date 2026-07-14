import json
import re

from .llm_client import chat_with_deepseek


def _mock_plan(topic: str, duration_weeks: int) -> dict:
    return {
        "topic": topic,
        "stages": [{"name": "背景学习", "tasks": ["阅读综述论文", "了解基础概念"], "output": "完成研究背景笔记"}],
        "weekly_plan": [
            {"week": week, "goal": "了解基础概念" if week == 1 else "推进研究任务", "tasks": ["阅读 2 篇相关论文", "整理研究笔记"]}
            for week in range(1, duration_weeks + 1)
        ],
        "risks": ["选题范围较大，建议先聚焦具体任务"],
        "is_mock": True,
    }


def generate_research_plan(topic: str, level: str, duration_weeks: int) -> dict:
    prompt = f'''用户研究方向：{topic}\n研究水平：{level}\n周期：{duration_weeks}周
请仅返回 JSON：{{"stages":[],"weekly_plan":[],"risks":[]}}'''
    try:
        result = chat_with_deepseek(prompt)
        data = json.loads(re.sub(r"```json|```", "", result).strip())
        if not all(isinstance(data.get(key), list) for key in ("stages", "weekly_plan", "risks")):
            raise ValueError("科研计划结构不完整")
        data.update({"topic": topic, "is_mock": False})
        return data
    except Exception:
        return _mock_plan(topic, duration_weeks)
