# qa_service.py

import json
import re


from .llm_client import chat_with_deepseek

from .embedding_service import get_embedding

from .vector_store import search_similar_chunks



def answer_question_about_paper(
        question: str,
        paper_id: int
) -> dict:


    """
    RAG论文问答
    """


    # 1. 问题向量化

    query_embedding = get_embedding(
        question
    )



    # 2. 检索相关论文片段

    chunks = search_similar_chunks(
        paper_id,
        query_embedding,
        top_k=8
    )



    context = "\n\n".join(
        chunks
    )



    # 3. 构造Prompt

    prompt=f"""

你是一名科研论文阅读助手。


请严格根据下面检索到的论文内容回答问题。


要求：

1. 不允许编造论文没有的信息
2. 如果内容不存在，回答"论文未提及"
3. 给出对应证据
4. 返回JSON格式



格式：

{{
"answer":"",
"evidence":[
""
]
}}



论文相关内容：

{context}



用户问题：

{question}

"""



    # 4. 调用ECNU模型

    result = chat_with_deepseek(
        prompt
    )



    # 5. 解析JSON

    try:

        result = re.sub(
            r"```json|```",
            "",
            result
        ).strip()


        data=json.loads(
            result
        )


    except Exception:


        data={
            "answer":result,
            "evidence":chunks
        }



    data["has_evidence"] = (
        len(
            data.get(
                "evidence",
                []
            )
        )>0
    )


    data["is_mock"]=False


    return data