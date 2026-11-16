"""Feedback submission route handler per TRD §4.6."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from orgbrain.api.deps import Repo
from orgbrain.api.schemas.envelope import OrgBrainEnvelope
from orgbrain.api.schemas.feedback import SubmitFeedbackData, SubmitFeedbackRequest

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "",
    response_model=OrgBrainEnvelope[SubmitFeedbackData],
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    body: SubmitFeedbackRequest,
    repo: Repo,
) -> OrgBrainEnvelope[SubmitFeedbackData]:
    """Submit feedback on a completed task."""
    # Verify the task exists
    task = await repo.get_task(uuid.UUID(body.task_id))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    corrections_count = len(body.corrections) if body.corrections else 0
    gaps_count = len(body.gap_descriptions) if body.gap_descriptions else 0

    # V1: Record feedback as a simple acknowledgment.
    # Full correction processing (entity updates, gap report creation) is future work.
    return OrgBrainEnvelope(
        data=SubmitFeedbackData(
            feedback_id=str(uuid.uuid4()),
            corrections_created=corrections_count,
            gap_reports_created=gaps_count,
        ),
    )
