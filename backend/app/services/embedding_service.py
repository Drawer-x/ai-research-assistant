import os

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("ECNU_API_KEY"),
    base_url="https://chat.ecnu.edu.cn/open/api/v1"
)



def get_embedding(text: str):

    """
    获取文本向量
    """

    response = client.embeddings.create(
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