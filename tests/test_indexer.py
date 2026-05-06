"""Tests for wp_memlog.indexer"""
from unittest.mock import patch, MagicMock

from wp_memlog.indexer import Indexer


class TestIndexer:
    """Test Indexer class"""

    @patch("wp_memlog.indexer.MeiliClient")
    def test_index_post(self, mock_meili):
        """Test indexing a single post"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        indexer = Indexer("http://meili:7700", "test-key")
        indexer.index_post(
            post_id=1,
            title="Test Post",
            content="Test content",
            categories=["deus"],
            tags=["test"],
        )

        mock_index.add_documents.assert_called_once()
        call_args = mock_index.add_documents.call_args[0][0]
        assert call_args[0]["id"] == "1"
        assert call_args[0]["title"] == "Test Post"
        assert call_args[0]["status"] == "private"

    @patch("wp_memlog.indexer.MeiliClient")
    def test_index_post_with_embedding(self, mock_meili):
        """Test indexing with embedding generation"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        mock_embedder = MagicMock()
        mock_embedder.embed_single.return_value = [0.1, 0.2, 0.3]

        indexer = Indexer("http://meili:7700", "test-key", embedder=mock_embedder)
        indexer.index_post(
            post_id=1,
            title="Test",
            content="Content",
            generate_embedding=True,
        )

        mock_embedder.embed_single.assert_called_once_with("Test Content")
        call_args = mock_index.add_documents.call_args[0][0]
        assert call_args[0]["_embedding"] == [0.1, 0.2, 0.3]

    @patch("wp_memlog.indexer.MeiliClient")
    def test_index_post_without_embedding(self, mock_meili):
        """Test indexing without embedding"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        mock_embedder = MagicMock()

        indexer = Indexer("http://meili:7700", "test-key", embedder=mock_embedder)
        indexer.index_post(
            post_id=1,
            title="Test",
            content="Content",
            generate_embedding=False,
        )

        mock_embedder.embed_single.assert_not_called()

    @patch("wp_memlog.indexer.MeiliClient")
    def test_update_enriched(self, mock_meili):
        """Test updating enriched data"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        indexer = Indexer("http://meili:7700", "test-key")
        indexer.update_enriched(1, "New excerpt")

        mock_index.update_documents.assert_called_once_with([{
            "id": "1",
            "excerpt": "New excerpt",
            "_enriched": True,
        }])

    @patch("wp_memlog.indexer.MeiliClient")
    def test_delete_document(self, mock_meili):
        """Test deleting a document"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        indexer = Indexer("http://meili:7700", "test-key")
        indexer.delete_document(1)

        mock_index.delete_document.assert_called_once_with("1")

    @patch("wp_memlog.indexer.MeiliClient")
    def test_configure_settings(self, mock_meili):
        """Test configuring index settings"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        indexer = Indexer("http://meili:7700", "test-key")
        indexer.configure_settings(
            filterable=["categories", "date"],
            sortable=["date"],
            searchable=["title", "content"],
        )

        mock_index.update_settings.assert_called_once()
        call_args = mock_index.update_settings.call_args[0][0]
        assert "filterableAttributes" in call_args
        assert "sortableAttributes" in call_args
        assert "searchableAttributes" in call_args

    @patch("wp_memlog.indexer.MeiliClient")
    def test_add_documents(self, mock_meili):
        """Test adding multiple documents"""
        mock_index = MagicMock()
        mock_meili.return_value.index.return_value = mock_index

        indexer = Indexer("http://meili:7700", "test-key")
        docs = [
            {"id": "1", "title": "Doc 1", "content": "Content 1"},
            {"id": "2", "title": "Doc 2", "content": "Content 2"},
        ]
        indexer.add_documents(docs, generate_embeddings=False)

        mock_index.add_documents.assert_called_once_with(docs)
