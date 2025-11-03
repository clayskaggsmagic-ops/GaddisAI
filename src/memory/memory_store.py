"""
Memory Store for Generative Agents-style memory system.

Implements:
- Memory stream storage with timestamps
- Recency + Importance + Relevance weighted retrieval
- Observation logging
- Reflection generation (optional)
"""

import os
import yaml
from datetime import datetime
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI


class MemoryStore:
    """Manages agent memory storage and retrieval using ChromaDB."""

    def __init__(self, config_path: str, persist_directory: str = "./data/chroma"):
        """
        Initialize memory store.

        Args:
            config_path: Path to memory.yaml configuration
            persist_directory: ChromaDB persistence directory
        """
        # Load memory configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Initialize OpenAI embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name=self.config["storage"]["embedding_model"]
        )

        # Get or create agent_memories collection
        collection_name = self.config["storage"]["collection_name"]
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"[MemoryStore] Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Agent memory stream for deliberations"}
            )
            print(f"[MemoryStore] Created new collection: {collection_name}")

        # Initialize OpenAI client for importance scoring and reflection
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Track observation counts for reflection triggering
        self.observation_counts = {}

    def add_observation(
        self,
        agent_role: str,
        content: str,
        importance: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add an observation to agent's memory stream.

        Args:
            agent_role: Role of agent (e.g., "President", "SecDef")
            content: Memory content in natural language
            importance: Importance score 0-1 (if None, will be calculated)
            metadata: Additional metadata dict

        Returns:
            memory_id: Unique ID of stored memory
        """
        # Calculate importance if not provided
        if importance is None:
            importance = self._calculate_importance(content, agent_role)

        # Generate unique memory ID
        timestamp = datetime.now().isoformat()
        memory_id = f"{agent_role}_{timestamp}".replace(" ", "_").replace(":", "-")

        # Build metadata
        memory_metadata = {
            "agent_role": agent_role,
            "timestamp": timestamp,
            "importance": importance,
            "access_count": 0,
            "last_accessed": "",  # Empty string instead of None (ChromaDB doesn't accept None)
            "memory_type": metadata.get("type", "observation") if metadata else "observation"
        }
        if metadata:
            memory_metadata.update(metadata)

        # Filter out None values (ChromaDB doesn't accept None in metadata)
        memory_metadata = {k: v for k, v in memory_metadata.items() if v is not None}

        # Store in ChromaDB
        self.collection.add(
            documents=[content],
            metadatas=[memory_metadata],
            ids=[memory_id]
        )

        # Update observation count for reflection tracking
        if agent_role not in self.observation_counts:
            self.observation_counts[agent_role] = 0
        self.observation_counts[agent_role] += 1

        print(f"[MemoryStore] Stored memory for {agent_role}: {content[:60]}... (importance: {importance:.2f})")

        return memory_id

    def retrieve_memories(
        self,
        agent_role: str,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant memories for an agent based on query.

        Uses weighted scoring: Recency + Importance + Relevance

        Args:
            agent_role: Role of agent
            query: Query text for similarity search
            top_k: Number of memories to retrieve (default from config)

        Returns:
            List of memory dicts with content, metadata, and scores
        """
        if top_k is None:
            top_k = self.config["retrieval"]["top_k"]

        # Query ChromaDB (over-retrieve for re-ranking)
        try:
            results = self.collection.query(
                query_texts=[query],
                where={"agent_role": agent_role},
                n_results=min(top_k * 3, 50)  # Over-retrieve for scoring
            )
        except Exception as e:
            print(f"[MemoryStore] No memories found for {agent_role}: {e}")
            return []

        # Check if results are empty
        if not results["documents"] or not results["documents"][0]:
            print(f"[MemoryStore] No memories found for {agent_role}")
            return []

        # Re-rank by combined score: relevance + recency + importance
        scored_memories = []

        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Relevance score (cosine similarity, distance is inverted)
            relevance_score = 1.0 - min(distance, 1.0)

            # Recency score (exponential decay)
            recency_score = self._calculate_recency(metadata["timestamp"])

            # Importance score (from metadata)
            importance_score = metadata["importance"]

            # Weighted final score
            weights = self.config["retrieval"]
            final_score = (
                weights["relevance_weight"] * relevance_score +
                weights["recency_weight"] * recency_score +
                weights["importance_weight"] * importance_score
            )

            scored_memories.append({
                "content": doc,
                "timestamp": metadata["timestamp"],
                "importance": importance_score,
                "memory_type": metadata.get("memory_type", "observation"),
                "relevance_score": relevance_score,
                "recency_score": recency_score,
                "final_score": final_score,
                "metadata": metadata
            })

        # Sort by final score and return top_k
        scored_memories.sort(key=lambda x: x["final_score"], reverse=True)
        top_memories = scored_memories[:top_k]

        if top_memories:
            print(f"[MemoryStore] Retrieved {len(top_memories)} memories for {agent_role}")

        return top_memories

    def should_reflect(self, agent_role: str) -> bool:
        """
        Check if agent has accumulated enough observations to trigger reflection.

        Args:
            agent_role: Role of agent

        Returns:
            True if reflection should be triggered
        """
        threshold = self.config["reflection"]["observation_threshold"]
        count = self.observation_counts.get(agent_role, 0)

        if count >= threshold:
            self.observation_counts[agent_role] = 0  # Reset counter
            return True
        return False

    def generate_reflection(self, agent_role: str) -> Optional[str]:
        """
        Generate a high-level reflection from recent observations.

        Args:
            agent_role: Role of agent

        Returns:
            Reflection text or None if not enough observations
        """
        # Retrieve recent observations (last 20)
        try:
            results = self.collection.query(
                query_texts=["recent deliberations and decisions"],
                where={"agent_role": agent_role, "memory_type": "observation"},
                n_results=20
            )
        except:
            return None

        if not results["documents"] or not results["documents"][0]:
            return None

        # Format recent observations
        observations = results["documents"][0]
        observations_text = "\n".join([f"- {obs}" for obs in observations])

        # Generate reflection using LLM
        prompt = f"""You are {agent_role} in the National Security Council. Review your recent observations from deliberations and generate a high-level insight or pattern you've noticed.

Recent observations:
{observations_text}

Generate a single insightful reflection (1-2 sentences) about patterns in your recommendations, the President's decisions, or advisor dynamics. This should be a higher-level synthesis, not just a summary.

Reflection:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a thoughtful NSC advisor capable of reflection and pattern recognition."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )

            reflection = response.choices[0].message.content.strip()
            print(f"[MemoryStore] Generated reflection for {agent_role}: {reflection[:80]}...")

            return reflection

        except Exception as e:
            print(f"[MemoryStore] Failed to generate reflection: {e}")
            return None

    def _calculate_importance(self, content: str, agent_role: str) -> float:
        """
        Calculate importance score for an observation using LLM or heuristics.

        Args:
            content: Memory content
            agent_role: Agent role

        Returns:
            Importance score 0.0-1.0
        """
        # Check heuristics first
        heuristics = self.config["importance"]["heuristics"]

        if "I decided:" in content or "presidential decision" in content.lower():
            return heuristics["presidential_decision"]
        elif "I recommended:" in content or "recommendation" in content.lower():
            return heuristics["advisor_recommendation"]
        elif "pattern" in content.lower() or "noticed" in content.lower():
            return heuristics["reflection"]

        # Use LLM for importance scoring if enabled
        if self.config["importance"]["use_llm"]:
            try:
                prompt = f"""On a scale of 0.0 to 1.0, rate the importance of this observation for {agent_role} in National Security Council deliberations.

Consider:
- 0.1-0.3: Routine, procedural matters
- 0.4-0.6: Standard policy discussions
- 0.7-0.8: Significant recommendations or decisions
- 0.9-1.0: Critical decisions, major policy shifts, or key insights

Observation: {content}

Respond with ONLY a number between 0.0 and 1.0."""

                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=10
                )

                score = float(response.choices[0].message.content.strip())
                return max(0.0, min(1.0, score))  # Clamp to 0-1

            except Exception as e:
                print(f"[MemoryStore] LLM importance scoring failed: {e}")
                return self.config["importance"]["default_score"]

        # Default score
        return self.config["importance"]["default_score"]

    def _calculate_recency(self, timestamp_str: str) -> float:
        """
        Calculate recency score using exponential decay.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            Recency score 0.0-1.0
        """
        try:
            memory_time = datetime.fromisoformat(timestamp_str)
            current_time = datetime.now()

            hours_elapsed = (current_time - memory_time).total_seconds() / 3600
            half_life_hours = self.config["decay"]["half_life_days"] * 24

            # Exponential decay: score = 0.5^(hours_elapsed / half_life)
            decay_score = 0.5 ** (hours_elapsed / half_life_hours)

            # Apply minimum floor
            min_score = self.config["decay"]["min_recency_score"]
            return max(decay_score, min_score)

        except Exception as e:
            print(f"[MemoryStore] Recency calculation failed: {e}")
            return 0.5  # Default mid-range score

    def get_memory_count(self, agent_role: Optional[str] = None) -> int:
        """
        Get count of memories, optionally filtered by agent role.

        Args:
            agent_role: Optional role filter

        Returns:
            Count of memories
        """
        try:
            if agent_role:
                results = self.collection.get(
                    where={"agent_role": agent_role}
                )
                return len(results["ids"])
            else:
                return self.collection.count()
        except:
            return 0

    def clear_memories(self, agent_role: Optional[str] = None):
        """
        Clear memories, optionally filtered by agent role.

        Args:
            agent_role: Optional role filter (if None, clears all)
        """
        if agent_role:
            # Delete specific agent's memories
            try:
                results = self.collection.get(
                    where={"agent_role": agent_role}
                )
                if results["ids"]:
                    self.collection.delete(ids=results["ids"])
                    print(f"[MemoryStore] Cleared {len(results['ids'])} memories for {agent_role}")
            except Exception as e:
                print(f"[MemoryStore] Failed to clear memories: {e}")
        else:
            # Clear entire collection
            self.client.delete_collection(self.config["storage"]["collection_name"])
            self.collection = self.client.create_collection(
                name=self.config["storage"]["collection_name"],
                embedding_function=self.embedding_function
            )
            print("[MemoryStore] Cleared all memories")
