"""
Document ingestion pipeline for GaddisAI RAG system.
Processes and chunks documents from data directory into vector store.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import yaml
from datetime import datetime


class DocumentIngester:
    """Handles document chunking and ingestion into vector store."""

    def __init__(self, config_path: str, data_dir: str = "./data"):
        """
        Initialize document ingester.

        Args:
            config_path: Path to retrieval.yaml configuration
            data_dir: Root data directory
        """
        self.data_dir = Path(data_dir)

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.chunk_tokens = self.config.get("chunk_tokens", 700)
        self.chunk_overlap = self.config.get("chunk_overlap", 120)

    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Chunk text into overlapping segments by approximate token count.

        Args:
            text: Text to chunk
            chunk_size: Target tokens per chunk (defaults to config)
            overlap: Overlap tokens (defaults to config)

        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.chunk_tokens
        if overlap is None:
            overlap = self.chunk_overlap

        # Approximate: 1 token ≈ 4 characters
        chars_per_chunk = chunk_size * 4
        overlap_chars = overlap * 4

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chars_per_chunk
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chars_per_chunk * 0.7:  # Only break if >70% through chunk
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap_chars

        return chunks

    def _generate_doc_id(self, content: str, metadata: Dict) -> str:
        """Generate unique ID for document chunk."""
        id_string = f"{metadata.get('source', '')}_{content[:100]}"
        return hashlib.md5(id_string.encode()).hexdigest()

    def ingest_memos(self) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Ingest policy memos from data/memo directory.

        Returns:
            Tuple of (documents, metadatas, ids)
        """
        memo_dir = self.data_dir / "memo"
        documents = []
        metadatas = []
        ids = []

        if not memo_dir.exists():
            print(f"Warning: {memo_dir} does not exist")
            return documents, metadatas, ids

        for file_path in memo_dir.glob("*.txt"):
            with open(file_path, 'r') as f:
                content = f.read()

            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": file_path.name,
                    "source_type": "memo",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "ingested_at": datetime.now().isoformat()
                })
                ids.append(self._generate_doc_id(chunk, {"source": file_path.name, "chunk": i}))

        print(f"Ingested {len(documents)} chunks from {len(list(memo_dir.glob('*.txt')))} memos")
        return documents, metadatas, ids

    def ingest_doctrine(self) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Ingest doctrine documents from data/doctrine directory.

        Returns:
            Tuple of (documents, metadatas, ids)
        """
        doctrine_dir = self.data_dir / "doctrine"
        documents = []
        metadatas = []
        ids = []

        if not doctrine_dir.exists():
            print(f"Warning: {doctrine_dir} does not exist")
            return documents, metadatas, ids

        # Handle both .txt and .yaml doctrine files
        file_count = 0
        for file_path in list(doctrine_dir.glob("*.txt")) + list(doctrine_dir.glob("*.yaml")):
            file_count += 1

            if file_path.suffix == ".yaml":
                # Convert YAML to text representation
                with open(file_path, 'r') as f:
                    doctrine_data = yaml.safe_load(f)
                content = yaml.dump(doctrine_data, default_flow_style=False, sort_keys=False)
            else:
                # Plain text file
                with open(file_path, 'r') as f:
                    content = f.read()

            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": file_path.name,
                    "source_type": "doctrine",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "ingested_at": datetime.now().isoformat()
                })
                ids.append(self._generate_doc_id(chunk, {"source": file_path.name, "chunk": i}))

        print(f"Ingested {len(documents)} chunks from {file_count} doctrine documents")
        return documents, metadatas, ids

    def ingest_dossiers(self) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Ingest agent dossiers from data/dossiers directory.

        Returns:
            Tuple of (documents, metadatas, ids)
        """
        dossier_dir = self.data_dir / "dossiers"
        documents = []
        metadatas = []
        ids = []

        if not dossier_dir.exists():
            print(f"Warning: {dossier_dir} does not exist")
            return documents, metadatas, ids

        # Check for nested structure (trump_admin/) vs flat structure
        trump_admin_dir = dossier_dir / "trump_admin"
        if trump_admin_dir.exists():
            dossier_dir = trump_admin_dir

        # Collect dossier files from both flat and nested structures
        dossier_files = []

        # Flat structure: *.yaml files directly in dossier_dir
        dossier_files.extend(dossier_dir.glob("*.yaml"))

        # Nested structure: role_dir/profile.yaml
        for role_dir in dossier_dir.iterdir():
            if role_dir.is_dir():
                profile_path = role_dir / "profile.yaml"
                if profile_path.exists():
                    dossier_files.append(profile_path)

        for file_path in dossier_files:
            with open(file_path, 'r') as f:
                dossier = yaml.safe_load(f)

            # Convert dossier to text representation
            text_parts = [
                f"Person: {dossier.get('person', 'Unknown')}",
                f"Role: {dossier.get('role', 'Unknown')}",
                f"Mandate: {dossier.get('mandate', '')}",
                f"\nEnduring Priorities:\n{dossier.get('enduring_priorities', '')}",
                f"\nPositions:\n{yaml.dump(dossier.get('positions', {}), default_flow_style=False)}",
                f"\nRecent Actions:\n{dossier.get('recent_actions', '')}",
                f"\nConstraints:\n{dossier.get('constraints', '')}"
            ]
            content = "\n\n".join(text_parts)

            # Determine source name (role)
            if file_path.name == "profile.yaml":
                source_name = file_path.parent.name  # e.g., "President" from President/profile.yaml
            else:
                source_name = file_path.stem  # e.g., "SecDef" from SecDef.yaml

            # Chunk dossiers by semantic sections for better retrieval precision
            person_name = dossier.get('person', 'Unknown')
            role_name = dossier.get('role', 'Unknown')

            chunks = []

            # Chunk 1: Identity & Mandate
            identity_chunk = f"""Person: {person_name}
Role: {role_name}

Mandate: {dossier.get('mandate', '')}""".strip()
            chunks.append(("identity", identity_chunk))

            # Chunk 2: Priorities & Weights
            priorities_data = dossier.get('enduring_priorities', '')
            weights_data = dossier.get('interests_weights', {})
            priorities_chunk = f"""Person: {person_name} ({role_name})

Enduring Priorities:
{priorities_data}

Interest Weights:
{yaml.dump(weights_data, default_flow_style=False) if weights_data else 'None specified'}""".strip()
            chunks.append(("priorities", priorities_chunk))

            # Chunk 3: Positions (only if exists)
            positions_data = dossier.get('positions', {})
            if positions_data:
                positions_chunk = f"""Person: {person_name} ({role_name})

Known Positions:
{yaml.dump(positions_data, default_flow_style=False)}""".strip()
                chunks.append(("positions", positions_chunk))

            # Chunk 4: Constraints & Red Lines
            constraints_chunk = f"""Person: {person_name} ({role_name})

Red Lines: {dossier.get('red_lines', [])}

Constraints: {dossier.get('constraints', '')}

Decision-Making Style: {dossier.get('decision_making_style', '')}

Recent Actions: {dossier.get('recent_actions', '')}""".strip()
            chunks.append(("constraints", constraints_chunk))

            # Store each chunk with enhanced metadata
            for section_type, chunk_text in chunks:
                documents.append(chunk_text)
                metadatas.append({
                    "source": source_name,
                    "person": person_name,
                    "role": role_name,
                    "source_type": "dossier",
                    "section": section_type,
                    "ingested_at": datetime.now().isoformat()
                })
                ids.append(self._generate_doc_id(chunk_text, {"source": source_name, "section": section_type}))

        print(f"Ingested {len(documents)} dossier chunks from {len(dossier_files)} agents")
        return documents, metadatas, ids

    def ingest_all(self) -> Dict[str, Tuple[List[str], List[Dict], List[str]]]:
        """
        Ingest all document types.

        Returns:
            Dict mapping collection names to (documents, metadatas, ids) tuples
        """
        results = {}

        print("Ingesting memos...")
        results["memo"] = self.ingest_memos()

        print("Ingesting doctrine...")
        results["doctrine"] = self.ingest_doctrine()

        print("Ingesting dossiers...")
        results["dossiers"] = self.ingest_dossiers()

        # News ingestion would go here (not implemented yet)
        results["news"] = ([], [], [])

        return results
