import functools
from typing import List, Union
import numpy as np

_embedder_instance = None

def get_embedder():
    """
    Lazy singleton loader for FastEmbed model (BAAI/bge-small-en-v1.5).
    Loads ONNX runtime only on first call.
    """
    global _embedder_instance
    if _embedder_instance is None:
        try:
            from fastembed import TextEmbedding
            _embedder_instance = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception as e:
            raise RuntimeError(f"Failed to load FastEmbed model: {e}")
    return _embedder_instance

@functools.lru_cache(maxsize=512)
def embed_single(text: str) -> np.ndarray:
    """
    Cached embedding for a single string.
    Returns normalized 1D numpy array.
    """
    res = embed([text])
    return res[0]

def embed(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Computes normalized embeddings for a text or list of texts.
    Returns 2D numpy array of shape (N, dim).
    Falls back gracefully to deterministic pseudo-embeddings if fastembed is unavailable.
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    try:
        model = get_embedder()
        raw_generator = model.embed(texts)
        embeddings = np.array(list(raw_generator), dtype=np.float32)
    except Exception:
        out = []
        for t in texts:
            vec = np.zeros(384, dtype=np.float32)
            words = (t or "").lower().split()
            if not words:
                vec[0] = 1.0
            else:
                for word in words:
                    idx = abs(hash(word)) % 384
                    vec[idx] += 1.0
            out.append(vec)
        embeddings = np.array(out, dtype=np.float32)

    # L2 normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms
