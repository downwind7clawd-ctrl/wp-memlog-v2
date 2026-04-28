"""bge-m3 local embedder for semantic search"""

import os
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class BgeM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    @property
    def model(self):
        if self._model is None:
            if SentenceTransformer is None:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "pip install wp-memlog[embedder]"
                )
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def embed(self, texts: list[str], normalize: bool = True) -> list[list[float]]:
        """Generate embeddings for texts."""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_single(self, text: str, normalize: bool = True) -> list[float]:
        """Generate embedding for a single text."""
        return self.embed([text], normalize)[0]

    @classmethod
    def from_env(cls) -> Optional["BgeM3Embedder"]:
        """Create embedder from environment variables."""
        model = os.getenv("WP_MEMLOG_EMBEDDER_MODEL", "BAAI/bge-m3")
        device = os.getenv("WP_MEMLOG_EMBEDDER_DEVICE", "cpu")
        if model:
            return cls(model_name=model, device=device)
        return None


def get_embedding_dim(model_name: str = "BAAI/bge-m3") -> int:
    """Get embedding dimension for a model."""
    return 1024  # bge-m3 outputs 1024-dim embeddings