def generate_research_plan(topic: str, level: str, duration_weeks: int) -> dict:
    weekly_plan = [
        {"week": week, "goal": "了解基础概念" if week == 1 else "推进研究任务", "tasks": ["阅读 2 篇相关论文", "整理研究笔记"]}
        for week in range(1, duration_weeks + 1)
    ]
    return {
        "topic": topic,
        "stages": [{"name": "背景学习", "tasks": ["阅读综述论文", "了解基础概念"], "output": "完成研究背景笔记"}],
        "weekly_plan": weekly_plan,
        "risks": ["选题范围较大，建议先聚焦具体任务"],
        "is_mock": True,
    }
