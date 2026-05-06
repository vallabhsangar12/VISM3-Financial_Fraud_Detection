# ============================================================
# Pydantic Validators — backend/utils/validators.py
# Request / Response schemas for the FastAPI prediction API
# ============================================================

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ── Prediction Input ───────────────────────────────────────────────────────────

class TransactionInput(BaseModel):
    """Incoming transaction payload for the /predict endpoint."""

    txn_id:    str   = Field(..., description="Unique transaction identifier")
    card_id:   str   = Field(..., description="Card identifier")
    Amount:    float = Field(..., ge=0.01, le=1_000_000, description="Transaction amount (USD)")
    Time:      float = Field(0.0, ge=0.0, description="Seconds elapsed since dataset epoch")

    # PCA-transformed features (V1–V28); optional — defaults to 0 if not supplied
    V1:  Optional[float] = 0.0
    V2:  Optional[float] = 0.0
    V3:  Optional[float] = 0.0
    V4:  Optional[float] = 0.0
    V5:  Optional[float] = 0.0
    V6:  Optional[float] = 0.0
    V7:  Optional[float] = 0.0
    V8:  Optional[float] = 0.0
    V9:  Optional[float] = 0.0
    V10: Optional[float] = 0.0
    V11: Optional[float] = 0.0
    V12: Optional[float] = 0.0
    V13: Optional[float] = 0.0
    V14: Optional[float] = 0.0
    V15: Optional[float] = 0.0
    V16: Optional[float] = 0.0
    V17: Optional[float] = 0.0
    V18: Optional[float] = 0.0
    V19: Optional[float] = 0.0
    V20: Optional[float] = 0.0
    V21: Optional[float] = 0.0
    V22: Optional[float] = 0.0
    V23: Optional[float] = 0.0
    V24: Optional[float] = 0.0
    V25: Optional[float] = 0.0
    V26: Optional[float] = 0.0
    V27: Optional[float] = 0.0
    V28: Optional[float] = 0.0

    # Engineered features
    is_night:  Optional[int] = Field(0, ge=0, le=1)
    rapid_txn: Optional[int] = Field(0, ge=0, le=1)

    model_config = {"extra": "ignore"}


# ── Prediction Output ──────────────────────────────────────────────────────────

class PredictionResult(BaseModel):
    """Response payload from the /predict endpoint."""

    txn_id:          str
    fraud_probability: float = Field(..., ge=0.0, le=1.0)
    risk_score:      float   = Field(..., ge=0.0, le=100.0)
    decision:        str     = Field(..., description="Fraud | Legitimate")
    risk_level:      str     = Field(..., description="CRITICAL | HIGH | MEDIUM | LOW")
    confidence:      float   = Field(..., ge=0.0, le=1.0)
    timestamp:       str


# ── Alert Schemas ──────────────────────────────────────────────────────────────

class AlertUpdate(BaseModel):
    """Payload to update an alert's status or assign an investigator."""
    status:      Optional[str] = None
    investigator: Optional[str] = None
    notes:       Optional[str] = None


# ── Case Management Schemas ────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    """Payload to open a new investigation case."""
    txn_id:      str
    alert_id:    Optional[str] = None
    description: str = Field(..., min_length=10, max_length=2000)
    assigned_to: Optional[str] = None
    priority:    str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")


class CaseUpdate(BaseModel):
    """Payload to update a case."""
    status:      Optional[str] = Field(None, pattern="^(Open|In Progress|Closed)$")
    assigned_to: Optional[str] = None
    notes:       Optional[str] = None


# ── Auth Schemas ───────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int
