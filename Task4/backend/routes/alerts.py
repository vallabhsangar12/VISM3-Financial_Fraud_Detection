# ============================================================
# Alerts Route — backend/routes/alerts.py
# GET /alerts      — List all alerts (filterable)
# PATCH /alerts/{id} — Update alert status / assign investigator
# ============================================================

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.utils.logger import logger

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ── In-memory alert store (replace with PostgreSQL in production) ──────────────
_ALERTS: List[dict] = []


class AlertOut(BaseModel):
    alert_id:     str
    txn_id:       str
    card_id:      str
    amount:       float
    fraud_score:  float
    risk_level:   str
    status:       str
    investigator: Optional[str]
    notes:        Optional[str]
    created_at:   str
    updated_at:   str


class AlertUpdate(BaseModel):
    status:       Optional[str] = None
    investigator: Optional[str] = None
    notes:        Optional[str] = None


@router.get("", summary="List all alerts")
async def list_alerts(
    status:     Optional[str] = Query(None, description="Filter by status: Pending|Investigating|Resolved"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: CRITICAL|HIGH|MEDIUM|LOW"),
    limit:      int           = Query(100, ge=1, le=500),
):
    """Return all fraud alerts with optional status/risk filters."""
    result = _ALERTS.copy()
    if status:
        result = [a for a in result if a["status"] == status]
    if risk_level:
        result = [a for a in result if a["risk_level"] == risk_level]
    return {"count": len(result), "alerts": result[:limit]}


@router.post("", summary="Create a new alert", status_code=201)
async def create_alert(payload: dict):
    """
    Ingest a new fraud alert (typically called internally by the prediction pipeline).
    """
    import uuid
    alert = {
        "alert_id":     str(uuid.uuid4())[:8].upper(),
        "created_at":   datetime.utcnow().isoformat() + "Z",
        "updated_at":   datetime.utcnow().isoformat() + "Z",
        "status":       "Pending",
        "investigator": None,
        "notes":        "",
        **payload,
    }
    _ALERTS.insert(0, alert)
    logger.info(f"ALERT CREATED | id={alert['alert_id']} | txn={payload.get('txn_id')}")
    return alert


@router.patch("/{alert_id}", summary="Update an alert")
async def update_alert(alert_id: str, body: AlertUpdate):
    """Update status, assign investigator, or add notes to an alert."""
    for alert in _ALERTS:
        if alert["alert_id"] == alert_id:
            if body.status:
                alert["status"] = body.status
            if body.investigator is not None:
                alert["investigator"] = body.investigator
            if body.notes is not None:
                alert["notes"] = body.notes
            alert["updated_at"] = datetime.utcnow().isoformat() + "Z"
            logger.info(f"ALERT UPDATED | id={alert_id} | status={alert['status']}")
            return alert
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@router.get("/summary", summary="Alert summary statistics")
async def alert_summary():
    """Return aggregate counts by status and risk level."""
    from collections import Counter
    statuses = Counter(a["status"]     for a in _ALERTS)
    risks    = Counter(a["risk_level"] for a in _ALERTS)
    return {
        "total":      len(_ALERTS),
        "by_status":  dict(statuses),
        "by_risk":    dict(risks),
    }
