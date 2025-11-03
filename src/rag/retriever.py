"""
Context retrieval for GaddisAI agents.
Retrieves relevant documents from vector store based on query.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yaml


class ContextRetriever:
    """Retrieves relevant context from vector store for agent queries."""

    def __init__(self, vectorstore, config_path: str):
        """
        Initialize context retriever.

        Args:
            vectorstore: VectorStore instance
            config_path: Path to retrieval.yaml configuration
        """
        self.vectorstore = vectorstore

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def retrieve_for_query(
        self,
        query: str,
        include_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant context for a query across all document types.

        Args:
            query: User query or policy question
            include_types: Optional list of doc types to retrieve
                          (defaults to ["memo", "doctrine", "dossiers"])

        Returns:
            Dict mapping collection names to lists of retrieved documents
            Each document is a dict with 'content', 'metadata', 'distance'
        """
        if include_types is None:
            include_types = ["memo", "doctrine", "dossiers"]

        results = {}

        for doc_type in include_types:
            if doc_type not in self.vectorstore.collections:
                continue

            # Get top_k for this document type
            n_results = self.config.get("top_k", {}).get(doc_type, 3)

            # Build filters if needed
            where_filter = None
            if doc_type == "news":
                # Filter news by max age
                max_age_days = self.config.get("filters", {}).get("news_max_age_days", 7)
                cutoff_date = datetime.now() - timedelta(days=max_age_days)
                where_filter = {"published_date": {"$gte": cutoff_date.isoformat()}}

            # Query vector store
            raw_results = self.vectorstore.query(
                query_text=query,
                collection_name=doc_type,
                n_results=n_results,
                where=where_filter
            )

            # Format results
            formatted_results = []
            for i in range(len(raw_results["documents"][0])):
                formatted_results.append({
                    "content": raw_results["documents"][0][i],
                    "metadata": raw_results["metadatas"][0][i],
                    "distance": raw_results["distances"][0][i],
                    "id": raw_results["ids"][0][i]
                })

            results[doc_type] = formatted_results

        return results

    def retrieve_specific_dossier(self, role: str) -> Optional[Dict]:
        """
        Retrieve a specific agent's dossier by role name.

        Args:
            role: Role name (e.g., "SecDef", "SecState")

        Returns:
            Dossier document dict or None if not found
        """
        # Query for specific role
        raw_results = self.vectorstore.query(
            query_text=f"Role: {role}",
            collection_name="dossiers",
            n_results=1
        )

        if not raw_results["documents"][0]:
            return None

        return {
            "content": raw_results["documents"][0][0],
            "metadata": raw_results["metadatas"][0][0],
            "distance": raw_results["distances"][0][0],
            "id": raw_results["ids"][0][0]
        }

    def format_context_for_prompt(
        self,
        retrieved_docs: Dict[str, List[Dict]],
        include_distances: bool = False
    ) -> str:
        """
        Format retrieved documents into a context string for agent prompts.

        Args:
            retrieved_docs: Retrieved documents from retrieve_for_query()
            include_distances: Whether to include similarity distances

        Returns:
            Formatted context string
        """
        context_parts = []

        # Format by document type
        for doc_type, docs in retrieved_docs.items():
            if not docs:
                continue

            context_parts.append(f"\n## {doc_type.upper()}\n")

            for i, doc in enumerate(docs, 1):
                metadata = doc["metadata"]
                source = metadata.get("source", "Unknown")

                header = f"### [{doc_type.upper()}] {source}"
                if include_distances:
                    header += f" (similarity: {1 - doc['distance']:.3f})"

                context_parts.append(header)
                context_parts.append(doc["content"])
                context_parts.append("")  # Empty line

        return "\n".join(context_parts)

    def get_all_advisors(self) -> List[str]:
        """
        Get list of all advisor roles from dossier collection.

        Returns:
            List of role names (e.g., ["SecDef", "SecState", "NSA"])
        """
        # Query all dossiers
        all_dossiers = self.vectorstore.collections["dossiers"].get()

        roles = []
        for metadata in all_dossiers.get("metadatas", []):
            source = metadata.get("source")
            if source and source not in roles:
                roles.append(source)

        return sorted(roles)
