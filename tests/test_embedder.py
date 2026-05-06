"""Tests for wp_memlog.embedder"""
import pytest
from unittest.mock import patch, MagicMock

from wp_memlog.embedder import BgeM3Embedder, get_embedding_dim


class TestBgeM3Embedder:
    """Test BgeM3Embedder class"""

    @patch("wp_memlog.embedder.SentenceTransformer")
    def test_embed_single(self, mock_st):
        """Test embedding a single text"""
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_st.return_value = mock_model

        embedder = BgeM3Embedder()
        result = embedder.embed_single("test text")

        assert result == [0.1, 0.2, 0.3]
        mock_st.assert_called_once_with("BAAI/bge-m3", device="cpu")

    @patch("wp_memlog.embedder.SentenceTransformer")
    def test_embed_batch(self, mock_st):
        """Test embedding multiple texts"""
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_st.return_value = mock_model

        embedder = BgeM3Embedder()
        result = embedder.embed(["text1", "text2"])

        assert len(result) == 2
        mock_model.encode.assert_called_once()

    @patch("wp_memlog.embedder.SentenceTransformer", None)
    def test_import_error_raises(self):
        """Test that ImportError is raised when sentence-transformers not installed"""
        embedder = BgeM3Embedder()
        with pytest.raises(ImportError, match="sentence-transformers not installed"):
            embedder.embed_single("test")

    def test_from_env_defaults(self, monkeypatch):
        """Test from_env with default values"""
        monkeypatch.setenv("WP_MEMLOG_EMBEDDER_MODEL", "BAAI/bge-m3")
        monkeypatch.setenv("WP_MEMLOG_EMBEDDER_DEVICE", "cpu")

        embedder = BgeM3Embedder.from_env()

        assert embedder is not None
        assert embedder.model_name == "BAAI/bge-m3"
        assert embedder.device == "cpu"

    def test_from_env_custom(self, monkeypatch):
        """Test from_env with custom values"""
        monkeypatch.setenv("WP_MEMLOG_EMBEDDER_MODEL", "BAAI/bge-small-en")
        monkeypatch.setenv("WP_MEMLOG_EMBEDDER_DEVICE", "cuda")

        embedder = BgeM3Embedder.from_env()

        assert embedder.model_name == "BAAI/bge-small-en"
        assert embedder.device == "cuda"


class TestGetEmbeddingDim:
    """Test get_embedding_dim function"""

    def test_known_models(self):
        """Test known model dimensions"""
        assert get_embedding_dim("BAAI/bge-m3") == 1024
        assert get_embedding_dim("BAAI/bge-small-en") == 384
        assert get_embedding_dim("BAAI/bge-base-en") == 768
        assert get_embedding_dim("BAAI/bge-large-en") == 1024

    def test_unknown_model_default(self):
        """Test unknown model returns default 1024"""
        assert get_embedding_dim("unknown/model") == 1024
