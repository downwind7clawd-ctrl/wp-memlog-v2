"""Meilisearch indexer with bge-m3 embeddings"""

from typing import Optional

from meilisearch import Client as MeiliClient

from .embedder import BgeM3Embedder


class Indexer:
    def __init__(
        self,
        meili_url: str,
        meili_api_key: str,
        index_name: str = "wp_posts",
        embedder: Optional[BgeM3Embedder] = None,
    ):
        self.meili = MeiliClient(meili_url, meili_api_key)
        self.index = self.meili.index(index_name)
        self.embedder = embedder

    def add_documents(
        self,
        documents: list[dict],
        generate_embeddings: bool = True,
    ):
        """Add documents to the index."""
        if generate_embeddings and self.embedder:
            for doc in documents:
                text = f"{doc.get('title', '')} {doc.get('content', '')}"
                embedding = self.embedder.embed_single(text)
                doc["_embedding"] = embedding

        self.index.add_documents(documents)

    def index_post(
        self,
        post_id: int,
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        categories: Optional[list] = None,
        tags: Optional[list] = None,
        date: Optional[str] = None,
        status: str = "private",
        enriched: bool = False,
        generate_embedding: bool = True,
    ):
        """Index a single post."""
        doc = {
            "id": str(post_id),
            "title": title,
            "content": content,
            "excerpt": excerpt or "",
            "categories": categories or [],
            "tags": tags or [],
            "date": date or "",
            "status": status,
            "_enriched": enriched,
        }

        if generate_embedding and self.embedder:
            text = f"{title} {content}"
            doc["_embedding"] = self.embedder.embed_single(text)

        self.index.add_documents([doc])

    def update_enriched(self, post_id: int, excerpt: str):
        """Update after ClassifAI enrichment."""
        self.index.update_documents([{
            "id": str(post_id),
            "excerpt": excerpt,
            "_enriched": True,
        }])

    def delete_document(self, post_id: int):
        """Delete a document."""
        self.index.delete_document(str(post_id))

    def configure_settings(
        self,
        filterable: Optional[list] = None,
        sortable: Optional[list] = None,
        searchable: Optional[list] = None,
    ):
        """Configure index settings."""
        settings = {}
        if filterable:
            settings["filterableAttributes"] = filterable
        if sortable:
            settings["sortableAttributes"] = sortable
        if searchable:
            settings["searchableAttributes"] = searchable

        if settings:
            self.index.update_settings(settings)