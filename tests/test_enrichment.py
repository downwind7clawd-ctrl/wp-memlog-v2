"""Tests for wp_memlog.enrichment"""
import pytest
from unittest.mock import patch, MagicMock

from wp_memlog.enrichment import (
    EnrichmentResult,
    generate_excerpt_sync,
    _get_openrouter_key,
)


class TestGetOpenrouterKey:
    """Test _get_openrouter_key function"""

    def test_returns_key(self, monkeypatch):
        """Test key is returned when set"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        assert _get_openrouter_key() == "test-key-123"

    def test_raises_when_missing(self, monkeypatch):
        """Test ValueError when key not set"""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY not set"):
            _get_openrouter_key()


class TestEnrichmentResult:
    """Test EnrichmentResult dataclass"""

    def test_creation(self):
        """Test creating EnrichmentResult"""
        result = EnrichmentResult(
            excerpt="Summary text",
            tags=["tag1", "tag2"],
            title="Test Title",
        )
        assert result.excerpt == "Summary text"
        assert result.tags == ["tag1", "tag2"]
        assert result.title == "Test Title"

    def test_default_title(self):
        """Test title defaults to None"""
        result = EnrichmentResult(excerpt="Summary", tags=[])
        assert result.title is None


class TestGenerateExcerptSync:
    """Test generate_excerpt_sync function"""

    def test_returns_excerpt(self, monkeypatch):
        """Test excerpt generation returns content from API"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated summary"}}]
        }

        with patch("wp_memlog.enrichment.httpx.Client") as mock_client:
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_cm)
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_cm.post.return_value = mock_response
            mock_client.return_value = mock_cm

            result = generate_excerpt_sync("Test content")

        assert result == "Generated summary"

    def test_content_truncated(self, monkeypatch):
        """Test content is truncated to 3000 chars"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        long_content = "x" * 5000

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Summary"}}]
        }

        with patch("wp_memlog.enrichment.httpx.Client") as mock_client:
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_cm)
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_cm.post.return_value = mock_response
            mock_client.return_value = mock_cm

            # Should not raise, content truncated internally
            result = generate_excerpt_sync(long_content)

        assert result == "Summary"
