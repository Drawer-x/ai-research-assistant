import json
import re

from .llm_client import chat_with_deepseek


def generate_paper_summary(paper_text: str) -> dict:
    """
    根据论文全文生成结构化总结
    """

    # 防止输入过长
    max_length = 15000
    if len(paper_text) > max_length:
        paper_text = paper_text[:max_length]

    prompt = f"""
你是一名专业科研助手，请阅读下面的论文内容，
生成结构化论文总结。

要求：
1. 只能输出JSON，不要输出Markdown代码块
2. 不要编造论文中不存在的信息
3. 如果论文没有相关内容，填写"未提及"

输出格式必须严格如下：

{{
    "background": "研究背景",
    "problem": "论文解决的问题",
    "method": "核心方法",
    "experiment": "实验设置",
    "result": "主要实验结果",
    "innovation": "创新点",
    "limitation": "局限性"
}}

论文内容：

{paper_text}
"""

    result = chat_with_deepseek(prompt)

    try:
        # 防止模型返回 ```json
        result = re.sub(
            r"```json|```",
            "",
            result
        ).strip()

        summary = json.loads(result)

    except Exception:

        summary = {
            "background": "",
            "problem": "",
            "method": "",
            "experiment": "",
            "result": "",
            "innovation": "",
            "limitation": "",
            "raw": result
        }

    return summary