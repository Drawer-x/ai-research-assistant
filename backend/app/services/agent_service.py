# agent_service.py

import json
import re
from .llm_client import chat_with_deepseek


def generate_research_plan(topic:str,
                           level:str,
                           duration_weeks:int):


    prompt=f"""

用户研究方向：

{topic}


研究水平：

{level}


周期：

{duration_weeks}周


请生成科研规划。


输出JSON：

{{
"stages":[],
"weekly_plan":[],
"risks":[]
}}

"""


    result=chat_with_deepseek(prompt)
    try:
        # 去掉markdown代码块
        result = re.sub(
            r"```json|```",
            "",
            result
        ).strip()

        data = json.loads(result)


    except Exception:
        data = {
            "raw": result
        }


    data["topic"]=topic
    data["is_mock"]=False

    return data