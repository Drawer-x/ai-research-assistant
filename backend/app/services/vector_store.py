import os
import pickle

import numpy as np
try:
    import faiss
except ImportError:
    faiss = None



VECTOR_DIR = "vector_db"


def search_vector_store(
        paper_id,
        query_embedding,
        top_k=5
):

    if faiss is None:
        raise RuntimeError("faiss-cpu 依赖未安装")
    index_path=f"vector_db/{paper_id}.index"

    index=faiss.read_index(
        index_path
    )


    distances, ids = index.search(
        np.array([query_embedding]),
        top_k
    )


    with open(
        f"vector_db/{paper_id}.pkl",
        "rb"
    ) as f:
        chunks=pickle.load(f)


    result=[]

    for i in ids[0]:
        if i!=-1:
            result.append(
                chunks[i]
            )

    return result
def save_vector_store(
        paper_id,
        chunks,
        embeddings
):

    """
    保存论文向量库
    """


    if not chunks:
        return
    if faiss is None:
        raise RuntimeError("faiss-cpu 依赖未安装")
    os.makedirs(
        VECTOR_DIR,
        exist_ok=True
    )


    vectors = np.array(
        embeddings
    ).astype("float32")


    dimension = vectors.shape[1]


    index = faiss.IndexFlatL2(
        dimension
    )


    index.add(vectors)


    index_path = (
        f"{VECTOR_DIR}/{paper_id}.index"
    )


    data_path = (
        f"{VECTOR_DIR}/{paper_id}.pkl"
    )


    faiss.write_index(
        index,
        index_path
    )


    with open(
        data_path,
        "wb"
    ) as f:

        pickle.dump(
            chunks,
            f
        )




def search_similar_chunks(
        paper_id,
        query_embedding,
        top_k=3
):

    """
    根据问题搜索相关论文片段
    """


    if faiss is None:
        raise RuntimeError("faiss-cpu 依赖未安装")
    index_path = (
        f"{VECTOR_DIR}/{paper_id}.index"
    )


    data_path = (
        f"{VECTOR_DIR}/{paper_id}.pkl"
    )


    index = faiss.read_index(
        index_path
    )


    with open(
        data_path,
        "rb"
    ) as f:

        chunks = pickle.load(f)



    query = np.array(
        [query_embedding]
    ).astype(
        "float32"
    )


    distances, indices = index.search(
        query,
        top_k
    )



    results=[]


    for idx in indices[0]:

        if idx < len(chunks):

            results.append(
                chunks[idx]
            )


    return results
