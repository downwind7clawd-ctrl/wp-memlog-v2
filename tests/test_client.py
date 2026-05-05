"""Tests for wp_memlog.client"""
import pytest
from unittest.mock import patch, MagicMock

from wp_memlog.client import WpClient, MeiliSearchClient, PostResult, SearchResult


class TestWpClient:
    """Test WpClient class"""

    def test_create_post(self, httpx_mock):
        """Test creating a post via WP REST API"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts",
            json={"id": 42},
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        post_id = client.create_post("Test Title", "Test Content")
        assert post_id == 42

    def test_create_post_with_category(self, httpx_mock):
        """Test creating a post with category"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts",
            json={"id": 43},
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        post_id = client.create_post("Test", "Content", category=5)
        assert post_id == 43

    def test_create_post_with_meta(self, httpx_mock):
        """Test creating a post with meta fields"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts",
            json={"id": 44},
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        post_id = client.create_post("Test", "Content", meta={"_memlog_idem": "uuid-123"})
        assert post_id == 44

    def test_get_post(self, httpx_mock):
        """Test getting a post"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts/42",
            json={"id": 42, "title": {"rendered": "Test"}},
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        post = client.get_post(42)
        assert post["id"] == 42

    def test_list_posts(self, httpx_mock):
        """Test listing posts"""
        httpx_mock.add_response(
            json=[{"id": 1}, {"id": 2}],
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        posts = client.list_posts()
        assert len(posts) == 2

    def test_list_posts_with_pagination(self, httpx_mock):
        """Test listing posts with pagination"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts?per_page=1&offset=10",
            json=[{"id": 1}],
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        posts = client.list_posts(per_page=1, offset=10)
        assert len(posts) == 1

    def test_update_post(self, httpx_mock):
        """Test updating a post"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts/42",
            json={"id": 42, "title": {"rendered": "Updated"}},
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        result = client.update_post(42, title="Updated")
        assert result["id"] == 42

    def test_create_post_http_error(self, httpx_mock):
        """Test that HTTP errors are raised"""
        httpx_mock.add_response(
            url="http://127.0.0.1:8080/wp-json/wp/v2/posts",
            status_code=401,
        )
        client = WpClient("http://127.0.0.1:8080", "admin", "password")
        with pytest.raises(Exception):
            client.create_post("Test", "Content")


class TestMeiliSearchClient:
    """Test MeiliSearchClient class"""

    @patch("wp_memlog.client.MeiliClient")
    def test_search(self, mock_meili):
        """Test search returns SearchResult list"""
        mock_index = MagicMock()
        mock_index.search.return_value = {
            "hits": [
                {
                    "id": "42",
                    "title": "Test Post",
                    "excerpt": "Summary",
                    "content": "Full content",
                    "categories": ["deus"],
                    "tags": ["test"],
                    "date": "2026-01-01",
                    "_rankingScore": 0.95,
                    "_enriched": True,
                }
            ]
        }
        mock_meili.return_value.index.return_value = mock_index

        client = MeiliSearchClient("http://127.0.0.1:7700", "test-key")
        results = client.search("test query")

        assert len(results) == 1
        assert results[0].post_id == 42
        assert results[0].title == "Test Post"
        assert results[0].relevance_score == 0.95
        assert results[0].enriched is True

    @patch("wp_memlog.client.MeiliClient")
    def test_search_with_category_filter(self, mock_meili):
        """Test search with category filter"""
        mock_index = MagicMock()
        mock_index.search.return_value = {"hits": []}
        mock_meili.return_value.index.return_value = mock_index

        client = MeiliSearchClient("http://127.0.0.1:7700", "test-key")
        results = client.search("query", category="deus")

        assert len(results) == 0
        mock_index.search.assert_called_once()

    @patch("wp_memlog.client.MeiliClient")
    def test_index_document(self, mock_meili):
        """Test indexing a document"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        client = MeiliSearchClient("http://127.0.0.1:7700", "test-key")
        client.index_document(
            post_id=1,
            title="Test",
            content="Content",
            categories=["deus"],
        )

        mock_index.add_documents.assert_called_once()

    @patch("wp_memlog.client.MeiliClient")
    def test_update_excerpt(self, mock_meili):
        """Test updating excerpt"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        client = MeiliSearchClient("http://127.0.0.1:7700", "test-key")
        client.update_excerpt(1, "New excerpt")

        mock_index.update_documents.assert_called_once_with([
            {"id": "1", "excerpt": "New excerpt", "_enriched": True}
        ])


class TestSearchResult:
    """Test SearchResult dataclass"""

    def test_search_result_creation(self):
        """Test creating a SearchResult"""
        result = SearchResult(
            post_id=1,
            title="Test",
            excerpt="Summary",
            content_preview="Preview",
            date="2026-01-01",
            categories=["deus"],
            tags=["test"],
            relevance_score=0.95,
            enriched=True,
            url="http://example.com",
        )
        assert result.post_id == 1
        assert result.title == "Test"
        assert result.enriched is True


class TestPostResult:
    """Test PostResult dataclass"""

    def test_post_result_creation(self):
        """Test creating a PostResult"""
        result = PostResult(post_id=1, indexed=True, enriched=False)
        assert result.post_id == 1
        assert result.indexed is True
        assert result.enriched is False
