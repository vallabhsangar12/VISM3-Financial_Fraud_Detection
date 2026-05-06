# ============================================================
# Predict Route — backend/routes/predict.py
# POST /predict — Accept transaction JSON → return fraud verdict
# ============================================================

import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

# Lazy-load model to avoid import-time cost
_MODEL_BUNDLE = None

def _get_bundle():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        from backend.model.train_model import load_model
        _MODEL_BUNDLE = load_model()
    return _MODEL_BUNDLE


from backend.utils.validators import TransactionInput, PredictionResult
from backend.utils.logger import logger

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post(
    "",
    response_model=PredictionResult,
    summary="Predict fraud probability for a transaction",
)
async def predict(txn: TransactionInput):
    """
    Run the ML fraud detection model on an incoming transaction.

    **Input**: Full transaction feature vector (V1–V28, Amount, Time, etc.)

    **Output**:
    - `fraud_probability` — Model output probability (0.0 – 1.0)
    - `risk_score` — Scaled 0–100 risk score
    - `decision` — Fraud | Legitimate
    - `risk_level` — CRITICAL | HIGH | MEDIUM | LOW
    - `confidence` — Model confidence in the decision
    """
    try:
        bundle = _get_bundle()
        from backend.model.train_model import predict_transaction

        txn_dict = txn.model_dump()
        result   = predict_transaction(bundle, txn_dict)

        logger.info(
            f"PREDICT | txn={txn.txn_id} | decision={result['decision']} "
            f"| prob={result['fraud_probability']:.4f} | risk={result['risk_level']}"
        )

        return PredictionResult(
            txn_id            = txn.txn_id,
            fraud_probability = result["fraud_probability"],
            risk_score        = result["risk_score"],
            decision          = result["decision"],
            risk_level        = result["risk_level"],
            confidence        = result["confidence"],
            timestamp         = datetime.utcnow().isoformat() + "Z",
        )

    except Exception as exc:
        logger.error(f"PREDICT ERROR | txn={txn.txn_id} | {exc}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}")


@router.get("/health", summary="Model health check")
async def health():
    """Return model status and metadata."""
    try:
        bundle = _get_bundle()
        meta   = bundle.get("metadata", {})
        return {
            "status":     "ok",
            "model_type": meta.get("model_type", "unknown"),
            "roc_auc":    meta.get("roc_auc"),
            "trained_at": meta.get("trained_at"),
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
