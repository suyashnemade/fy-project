"""
User feedback storage and scoring module.
Records feedback (relevant/not_relevant) and applies score boosts to future searches.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

from .logger import get_logger
from . import config

logger = get_logger(__name__)


class FeedbackStore:
    """JSON-based storage for user feedback on search results."""
    
    def __init__(self):
        self.feedback_path = config.FEEDBACK_PATH
        self.entries = []
        self._load()
    
    def _load(self):
        """Load feedback entries from disk."""
        if self.feedback_path.exists():
            try:
                with open(self.feedback_path, 'r') as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
                logger.info(f"Loaded {len(self.entries)} feedback entries.")
            except Exception as e:
                logger.error(f"Failed to load feedback: {e}")
                self.entries = []
        else:
            self.entries = []
    
    def _save(self):
        """Save feedback entries to disk."""
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.feedback_path, 'w') as f:
                json.dump({"entries": self.entries}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def add_feedback(
        self, 
        query: str, 
        image_path: str, 
        feedback: str, 
        original_rank: int = -1, 
        original_score: float = 0.0
    ):
        """
        Record user feedback for a search result.
        
        Args:
            query: The search query text
            image_path: Path to the image
            feedback: "relevant" or "not_relevant"
            original_rank: Position in the original result list
            original_score: Original similarity score
        """
        entry = {
            "query": query,
            "image_path": image_path,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
            "original_rank": original_rank,
            "original_score": original_score
        }
        self.entries.append(entry)
        self._save()
        logger.info(f"Feedback recorded: '{feedback}' for query='{query}', image='{Path(image_path).name}'")
    
    def get_boost(self, query: str, image_path: str) -> float:
        """
        Get the cumulative feedback boost for a query-image pair.
        
        Returns:
            Boost value: +0.02 per "relevant", -0.01 per "not_relevant"
            Kept small relative to cosine sim scores (~0.2-0.35).
        """
        boost = 0.0
        query_lower = query.lower().strip()
        
        for entry in self.entries:
            entry_query = entry.get("query", "").lower().strip()
            entry_path = entry.get("image_path", "")
            
            # Match on exact query only (previous prefix matching was too broad)
            if entry_query == query_lower:
                
                if entry_path == image_path:
                    if entry.get("feedback") == "relevant":
                        boost += 0.02
                    elif entry.get("feedback") == "not_relevant":
                        boost -= 0.01
        
        return boost
    
    def apply_feedback_boost(
        self, 
        results: List[Tuple[str, float]], 
        query: str
    ) -> List[Tuple[str, float]]:
        """
        Apply feedback-based score boosts to search results and re-sort.
        
        Args:
            results: List of (image_path, score) tuples
            query: The search query
            
        Returns:
            Re-sorted list of (image_path, boosted_score) tuples
        """
        if not self.entries:
            return results
        
        boosted = []
        for path, score in results:
            boost = self.get_boost(query, path)
            boosted.append((path, score + boost))
        
        boosted.sort(key=lambda x: x[1], reverse=True)
        return boosted
    
    def get_stats(self) -> dict:
        """Get feedback statistics."""
        relevant = sum(1 for e in self.entries if e.get("feedback") == "relevant")
        not_relevant = sum(1 for e in self.entries if e.get("feedback") == "not_relevant")
        return {
            "total": len(self.entries),
            "relevant": relevant,
            "not_relevant": not_relevant
        }
