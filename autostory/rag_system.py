"""
RAG (Retrieval-Augmented Generation) System for Story Collection

This module provides RAG functionality for maintaining story continuity across
multiple story generations. It stores stories in a local SQLite database and
provides semantic search capabilities using sentence-transformers embeddings.
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
from sentence_transformers import SentenceTransformer
import faiss


class StoryDatabase:
    """SQLite database for storing stories and their metadata."""

    def __init__(self, db_path: str = "autostory/stories.db"):
        """
        Initialize the story database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_prompt TEXT NOT NULL,
                    story_outline TEXT NOT NULL,
                    full_story TEXT NOT NULL,
                    embedding BLOB,  -- Numpy array stored as bytes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT  -- JSON string for additional metadata
                )
            ''')

            # Create index on created_at for efficient ordering
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_stories_created_at
                ON stories(created_at)
            ''')

            conn.commit()

    def add_story(self, user_prompt: str, story_outline: str, full_story: str,
                  embedding: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a new story to the database.

        Args:
            user_prompt: The original user prompt
            story_outline: Story outline/summary
            full_story: Complete story text
            embedding: Embedding vector for the story outline
            metadata: Additional metadata

        Returns:
            Story ID
        """
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO stories (user_prompt, story_outline, full_story, embedding, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_prompt, story_outline, full_story, embedding.tobytes(), metadata_json))

            story_id = cursor.lastrowid
            conn.commit()
            return story_id

    def get_recent_stories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent stories.

        Args:
            limit: Number of recent stories to retrieve

        Returns:
            List of story dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, user_prompt, story_outline, full_story, embedding, created_at, metadata
                FROM stories
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            stories = []
            for row in cursor.fetchall():
                story = dict(row)
                # Convert embedding bytes back to numpy array
                if story['embedding']:
                    story['embedding'] = np.frombuffer(story['embedding'], dtype=np.float32)
                # Parse metadata JSON
                story['metadata'] = json.loads(story['metadata'] or '{}')
                stories.append(story)

            return stories

    def get_all_story_outlines(self) -> List[Tuple[int, str, np.ndarray]]:
        """
        Get all story outlines with their embeddings for vector search.

        Returns:
            List of (story_id, outline_text, embedding) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, story_outline, embedding
                FROM stories
                ORDER BY created_at ASC
            ''')

            outlines = []
            for row in cursor.fetchall():
                story_id, outline, embedding_bytes = row
                if embedding_bytes:
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    outlines.append((story_id, outline, embedding))

            return outlines

    def get_story_by_id(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific story by ID.

        Args:
            story_id: Story ID

        Returns:
            Story dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, user_prompt, story_outline, full_story, embedding, created_at, metadata
                FROM stories
                WHERE id = ?
            ''', (story_id,))

            row = cursor.fetchone()
            if row:
                story = dict(row)
                if story['embedding']:
                    story['embedding'] = np.frombuffer(story['embedding'], dtype=np.float32)
                story['metadata'] = json.loads(story['metadata'] or '{}')
                return story

        return None


class StoryRAG:
    """RAG system for story retrieval and context generation."""

    def __init__(self, db_path: str = "autostory/stories.db",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG system.

        Args:
            db_path: Path to the story database
            model_name: Sentence transformer model name
        """
        self.db = StoryDatabase(db_path)

        # Initialize embedding model
        try:
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")

        # Initialize FAISS index (will be rebuilt from database)
        self.index = None
        self.story_ids = []
        self._build_index()

    def _build_index(self):
        """Build FAISS index from existing stories."""
        outlines = self.db.get_all_story_outlines()

        if not outlines:
            # No stories yet, create empty index
            self.index = faiss.IndexFlatIP(384)  # Cosine similarity for sentence-transformers
            return

        # Extract embeddings and IDs
        embeddings = np.array([emb for _, _, emb in outlines])
        self.story_ids = [sid for sid, _, _ in outlines]

        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add to index
        self.index.add(embeddings)

    def add_story(self, user_prompt: str, story_outline: str, full_story: str,
                  metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a new story to the RAG system.

        Args:
            user_prompt: Original user prompt
            story_outline: Story outline/summary
            full_story: Complete story text
            metadata: Additional metadata

        Returns:
            Story ID
        """
        # Generate embedding for the outline
        embedding = self.model.encode([story_outline])[0]

        # Add to database
        story_id = self.db.add_story(user_prompt, story_outline, full_story, embedding, metadata)

        # Update FAISS index
        embedding_norm = embedding / np.linalg.norm(embedding)  # Normalize for cosine similarity
        embedding_2d = embedding_norm.reshape(1, -1)
        self.index.add(embedding_2d)
        self.story_ids.append(story_id)

        return story_id

    def retrieve_relevant_stories(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant stories based on semantic similarity.

        Args:
            query: Query string (usually the new story prompt)
            top_k: Number of top similar stories to retrieve

        Returns:
            List of relevant story dictionaries
        """
        if self.index.ntotal == 0:
            return []  # No stories in database yet

        # Encode query
        query_embedding = self.model.encode([query])[0]
        query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
        query_embedding_2d = query_embedding_norm.reshape(1, -1)

        # Search
        scores, indices = self.index.search(query_embedding_2d, min(top_k, self.index.ntotal))

        # Get stories
        relevant_stories = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.story_ids):
                story_id = self.story_ids[idx]
                story = self.db.get_story_by_id(story_id)
                if story:
                    story['similarity_score'] = float(score)
                    relevant_stories.append(story)

        return relevant_stories

    def get_recent_context(self, limit: int = 3) -> str:
        """
        Get context from recent stories for continuity.

        Args:
            limit: Number of recent stories to include

        Returns:
            Formatted context string
        """
        recent_stories = self.db.get_recent_stories(limit)

        if not recent_stories:
            return ""

        context_parts = []
        for i, story in enumerate(reversed(recent_stories), 1):  # Most recent last
            context_parts.append(f"Story {i} (Created: {story['created_at']}):")
            context_parts.append(f"User Prompt: {story['user_prompt']}")
            context_parts.append(f"Outline: {story['story_outline']}")
            context_parts.append(f"Full Story: {story['full_story'][:500]}...")  # Truncate long stories
            context_parts.append("")

        return "\n".join(context_parts)

    def generate_rag_context(self, user_prompt: str, max_stories: int = 3) -> str:
        """
        Generate RAG context for story generation.

        Args:
            user_prompt: New story prompt
            max_stories: Maximum number of relevant stories to include

        Returns:
            Formatted context string for the LLM
        """
        # Get relevant stories based on semantic similarity
        relevant_stories = self.retrieve_relevant_stories(user_prompt, max_stories)

        if not relevant_stories:
            return "No previous stories found in the collection."

        context_parts = ["Previous Stories in Collection (for continuity):"]
        context_parts.append("=" * 50)

        for i, story in enumerate(relevant_stories, 1):
            context_parts.append(f"Story {i} (Similarity: {story['similarity_score']:.3f}):")
            context_parts.append(f"Original Prompt: {story['user_prompt']}")
            context_parts.append(f"Story Outline: {story['story_outline']}")
            context_parts.append(f"Story Content: {story['full_story'][:1000]}...")
            context_parts.append("-" * 30)

        context_parts.append("")
        context_parts.append("Please create a new story that continues the narrative from these previous stories.")
        context_parts.append("Ensure thematic consistency and character development continuity.")

        return "\n".join(context_parts)
