from sentence_transformers import SentenceTransformer
import numpy as np
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed(text: str):
    vec = model.encode(text)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()