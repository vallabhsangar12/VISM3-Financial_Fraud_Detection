# ============================================================
# Cases Route — backend/routes/cases.py
# Investigation Case Management CRUD
# POST   /cases       — Open a new case
# GET    /cases       — List all cases
# GET    /cases/{id}  — Get single case
# PATCH  /cases/{id}  — Update case status / add notes
# ============================================================

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.utils.logger import logger

router = APIRouter(prefix="/cases", tags=["Case Management"])

# ── In-memory case store (replace with PostgreSQL in production) ───────────────
_CASES: List[dict] = []

VALID_STATUSES   = {"Open", "In Progress", "Closed"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}


class CaseCreate(BaseModel):
    txn_id:      str
    alert_id:    Optional[str] = None
    description: str = Field(..., min_length=10)
    assigned_to: Optional[str] = None
    priority:    str = "Medium"


class CaseUpdate(BaseModel):
    status:      Optional[str] = None
    assigned_to: Optional[str] = None
    notes:       Optional[str] = None


class NoteAdd(BaseModel):
    author: str
    body:   str = Field(..., min_length=5)


@router.post("", summary="Open a new investigation case", status_code=201)
async def create_case(payload: CaseCreate):
    """
    Create an investigation case linked to a fraud alert.

    Cases track the full investigation lifecycle: Open → In Progress → Closed.
    """
    if payload.priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"priority must be one of {VALID_PRIORITIES}")

    case = {
        "case_id":     f"CASE-{str(uuid.uuid4())[:6].upper()}",
        "txn_id":      payload.txn_id,
        "alert_id":    payload.alert_id,
        "description": payload.description,
        "assigned_to": payload.assigned_to,
        "priority":    payload.priority,
        "status":      "Open",
        "notes":       [],
        "created_at":  datetime.utcnow().isoformat() + "Z",
        "updated_at":  datetime.utcnow().isoformat() + "Z",
    }
    _CASES.insert(0, case)
    logger.info(f"CASE OPENED | id={case['case_id']} | txn={payload.txn_id}")
    return case


@router.get("", summary="List all investigation cases")
async def list_cases(
    status:      Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit:       int           = Query(50, ge=1, le=200),
):
    """Return investigation cases with optional filters."""
    result = _CASES.copy()
    if status:
        result = [c for c in result if c["status"] == status]
    if assigned_to:
        result = [c for c in result if c.get("assigned_to") == assigned_to]
    return {"count": len(result), "cases": result[:limit]}


@router.get("/{case_id}", summary="Get a single case by ID")
async def get_case(case_id: str):
    for case in _CASES:
        if case["case_id"] == case_id:
            return case
    raise HTTPException(404, f"Case {case_id} not found")


@router.patch("/{case_id}", summary="Update a case")
async def update_case(case_id: str, body: CaseUpdate):
    """Update case status, reassign investigator, or add free-text notes."""
    for case in _CASES:
        if case["case_id"] == case_id:
            if body.status:
                if body.status not in VALID_STATUSES:
                    raise HTTPException(400, f"status must be one of {VALID_STATUSES}")
                case["status"] = body.status
            if body.assigned_to is not None:
                case["assigned_to"] = body.assigned_to
            if body.notes:
                case["notes"].append({
                    "author":     body.assigned_to or "Unknown",
                    "body":       body.notes,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                })
            case["updated_at"] = datetime.utcnow().isoformat() + "Z"
            logger.info(f"CASE UPDATED | id={case_id} | status={case['status']}")
            return case
    raise HTTPException(404, f"Case {case_id} not found")


@router.post("/{case_id}/notes", summary="Add a note to a case")
async def add_note(case_id: str, note: NoteAdd):
    for case in _CASES:
        if case["case_id"] == case_id:
            case["notes"].append({
                "author":     note.author,
                "body":       note.body,
                "created_at": datetime.utcnow().isoformat() + "Z",
            })
            case["updated_at"] = datetime.utcnow().isoformat() + "Z"
            return {"message": "Note added", "case_id": case_id}
    raise HTTPException(404, f"Case {case_id} not found")


@router.get("/stats/summary", summary="Case statistics")
async def case_stats():
    from collections import Counter
    statuses    = Counter(c["status"]   for c in _CASES)
    priorities  = Counter(c["priority"] for c in _CASES)
    return {
        "total":        len(_CASES),
        "by_status":    dict(statuses),
        "by_priority":  dict(priorities),
    }
