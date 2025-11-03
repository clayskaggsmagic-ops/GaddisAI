"""
Vector database initialization and management for GaddisAI RAG system.
Uses ChromaDB for document storage and retrieval.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import yaml


class VectorStore:
    """Manages ChromaDB vector database for document retrieval."""

    def __init__(self, config_path: str, persist_directory: str = "./data/chroma"):
        """
        Initialize the vector store.

        Args:
            config_path: Path to retrieval.yaml configuration
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name=self.config.get("embed_model", "text-embedding-3-small")
        )

        # Create/get collections for each document type
        self.collections = {}
        for doc_type in ["memo", "doctrine", "dossiers", "news"]:
            self.collections[doc_type] = self.client.get_or_create_collection(
                name=doc_type,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        collection_name: str
    ):
        """
        Add documents to a specific collection.

        Args:
            documents: List of document texts
            metadatas: List of metadata dicts for each document
            ids: List of unique IDs for each document
            collection_name: Name of collection (memo/doctrine/dossiers/news)
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        collection = self.collections[collection_name]
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"Added {len(documents)} documents to {collection_name} collection")

    def query(
        self,
        query_text: str,
        collection_name: str,
        n_results: Optional[int] = None,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query a specific collection.

        Args:
            query_text: Query string
            collection_name: Name of collection to query
            n_results: Number of results (defaults to config top_k)
            where: Optional metadata filter

        Returns:
            Dict with 'documents', 'metadatas', 'distances', 'ids'
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        if n_results is None:
            n_results = self.config.get("top_k", {}).get(collection_name, 3)

        collection = self.collections[collection_name]
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )

        return results

    def clear_collection(self, collection_name: str):
        """Clear all documents from a collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        self.client.delete_collection(collection_name)
        self.collections[collection_name] = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Cleared collection: {collection_name}")

    def get_collection_count(self, collection_name: str) -> int:
        """Get document count in a collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")

        return self.collections[collection_name].count()

    def list_collections(self) -> Dict[str, int]:
        """List all collections and their document counts."""
        return {name: coll.count() for name, coll in self.collections.items()}
