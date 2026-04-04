"""
Feedback endpoints: submit relevance feedback and view statistics.
"""

from fastapi import APIRouter, Depends, HTTPException

from core.search import ImageSearcher
from ..dependencies import get_searcher
from ..models import FeedbackRequest, FeedbackStatsResponse

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/add")
def add_feedback(
    request: FeedbackRequest,
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Submit relevance feedback for a search result.

    Feedback is stored persistently and used to boost/demote results
    in future searches for the same query.

    - `feedback` must be either `"relevant"` or `"not_relevant"`
    """
    feedback_store = searcher.feedback_store
    if feedback_store is None:
        raise HTTPException(
            status_code=503,
            detail="Feedback store is not available.",
        )

    feedback_store.add_feedback(
        query=request.query,
        image_path=request.image_path,
        feedback=request.feedback,
        original_rank=request.rank,
        original_score=request.score,
    )

    return {
        "message": "Feedback recorded successfully.",
        "query": request.query,
        "feedback": request.feedback,
    }


@router.get("/stats", response_model=FeedbackStatsResponse)
def feedback_stats(
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Get feedback statistics: total entries, relevant count, not-relevant count.
    """
    feedback_store = searcher.feedback_store
    if feedback_store is None:
        return FeedbackStatsResponse(total=0, relevant=0, not_relevant=0)

    stats = feedback_store.get_stats()
    return FeedbackStatsResponse(
        total=stats["total"],
        relevant=stats["relevant"],
        not_relevant=stats["not_relevant"],
    )
