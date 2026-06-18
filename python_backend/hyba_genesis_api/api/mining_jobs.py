from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from hyba_genesis_api.api.mining import get_pythia_state, require_mining_read

router = APIRouter(prefix="/api/mining", tags=["mining"])


@router.get("/job", response_model=Dict[str, Any], dependencies=[Depends(require_mining_read)])
async def get_current_job() -> Dict[str, Any]:
    """Return the currently active mining job.

    Raises a 404 error if no active job is present. Uses the PYTHIA state file
    maintained by the mining API to report the full job payload.
    """
    state = get_pythia_state()
    if not state or not state.get("current_job"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_active_mining_job",
                "message": "No active mining job is present.",
            },
        )
    return {
        "status": "ok",
        "job": state["current_job"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/jobs/search", response_model=Dict[str, Any], dependencies=[Depends(require_mining_read)])
async def search_jobs(job_id: str | None = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """Search for mining jobs.

    If job_id is provided, searches for a specific job by identifier.
    If job_id is omitted, returns all available jobs with pagination.
    Scans the current and last job records in the PYTHIA state for matches.
    """
    state = get_pythia_state()
    results: List[Dict[str, Any]] = []
    
    if state:
        if job_id:
            # Search for specific job
            current_job = state.get("current_job")
            if current_job and current_job.get("job_id") == job_id:
                results.append(current_job)
            last_job = state.get("last_job")
            if last_job and last_job.get("job_id") == job_id:
                results.append(last_job)
        else:
            # Return all available jobs
            current_job = state.get("current_job")
            if current_job:
                results.append(current_job)
            last_job = state.get("last_job")
            if last_job:
                results.append(last_job)
    
    # Apply pagination
    total = len(results)
    paginated_results = results[offset:offset + limit]
    
    return {
        "jobs": paginated_results,
        "total": total,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
