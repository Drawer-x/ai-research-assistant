import os


def _get_client():
    api_key = os.getenv("ECNU_API_KEY")
    if not api_key:
        raise RuntimeError("ECNU_API_KEY 未配置")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 依赖未安装") from exc
    return OpenAI(api_key=api_key, base_url="https://chat.ecnu.edu.cn/open/api/v1")



def get_embedding(text: str):

    """
    获取文本向量
    """

    response = _get_client().embeddings.create(
        model="ecnu-embedding-small",
        input=text
    )


    vector = response.data[0].embedding


    return vector



def get_embeddings(texts):

    """
    批量获取向量
    """

    vectors=[]


    for text in texts:

        vectors.append(
            get_embedding(text)
        )


    return vectors
