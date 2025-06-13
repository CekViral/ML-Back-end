from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def embed_query(text: str):
    vector = embed_model.encode(text)
    return vector.tolist()