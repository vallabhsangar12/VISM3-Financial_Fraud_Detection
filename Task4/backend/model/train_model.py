# ============================================================
# Model Training Pipeline — backend/model/train_model.py
# Trains Random Forest + XGBoost on creditcard.csv
# Saves the best model as fraud_model.pkl
# ============================================================

import os
import sys
import pickle
import time
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, roc_auc_score,
    precision_recall_curve, average_precision_score, confusion_matrix
)
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# ── Paths ──────────────────────────────────────────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_TASK4_DIR  = os.path.join(_THIS_DIR, "..", "..")
_DATASET    = os.path.join(_TASK4_DIR, "dataset", "creditcard.csv")
_MODEL_OUT  = os.path.join(_THIS_DIR, "fraud_model.pkl")
_SCALER_OUT = os.path.join(_THIS_DIR, "scaler.pkl")

# ── Feature columns ────────────────────────────────────────────────────────────
V_FEATURES = [f"V{i}" for i in range(1, 29)]
FEATURES   = V_FEATURES + ["Amount", "Time"]
TARGET     = "Class"


def load_data(path: str) -> pd.DataFrame:
    """Load and validate the creditcard dataset."""
    print(f"[TRAIN] Loading dataset from: {path}")
    df = pd.read_csv(path)
    assert TARGET in df.columns, f"Target column '{TARGET}' not found!"
    print(f"[TRAIN] Loaded {len(df):,} rows | Fraud rate: {df[TARGET].mean():.4%}")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features to the dataset."""
    df = df.copy()
    df["is_night"]  = ((df["Time"] % 86400) < 21600).astype(int)
    df["Amount_log"] = np.log1p(df["Amount"])
    df["Amount_sq"]  = df["Amount"] ** 0.5
    return df


def train(dataset_path: str = _DATASET):
    """Full training pipeline: load → engineer → split → SMOTE → train → evaluate → save."""

    if not os.path.exists(dataset_path):
        print(f"[TRAIN] ERROR: Dataset not found at {dataset_path}")
        print("[TRAIN] Generating synthetic training data instead...")
        df = _generate_synthetic_data()
    else:
        df = load_data(dataset_path)

    df = engineer_features(df)

    feat_cols = FEATURES + ["is_night", "Amount_log", "Amount_sq"]
    X = df[feat_cols].values
    y = df[TARGET].values

    # ── Train / test split ─────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"[TRAIN] Train: {len(X_train):,} | Test: {len(X_test):,}")

    # ── Scale ──────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── SMOTE oversampling (on training set only) ──────────────────────────────
    print("[TRAIN] Applying SMOTE oversampling...")
    sm = SMOTE(random_state=42, k_neighbors=5)
    X_res, y_res = sm.fit_resample(X_train_s, y_train)
    print(f"[TRAIN] After SMOTE → {len(X_res):,} samples | Fraud: {y_res.sum():,}")

    # ── Choose model ───────────────────────────────────────────────────────────
    if XGBOOST_AVAILABLE:
        print("[TRAIN] Training XGBoost classifier...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1,   # SMOTE already balanced
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
    else:
        print("[TRAIN] XGBoost not available — training Random Forest...")
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

    t0 = time.time()
    model.fit(X_res, y_res)
    elapsed = time.time() - t0
    print(f"[TRAIN] Training completed in {elapsed:.1f}s")

    # ── Evaluate ───────────────────────────────────────────────────────────────
    y_pred      = model.predict(X_test_s)
    y_proba     = model.predict_proba(X_test_s)[:, 1]
    roc_auc     = roc_auc_score(y_test, y_proba)
    avg_prec    = average_precision_score(y_test, y_proba)
    cm          = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr         = fp / max(fp + tn, 1)

    print("\n" + "=" * 60)
    print("  MODEL EVALUATION")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))
    print(f"  ROC-AUC:           {roc_auc:.4f}")
    print(f"  Avg Precision:     {avg_prec:.4f}")
    print(f"  False Positive Rate: {fpr:.4f}")
    print(f"  True Positives:    {tp} | False Negatives: {fn}")
    print("=" * 60)

    # ── Save model + scaler + metadata ────────────────────────────────────────
    metadata = {
        "model_type":    type(model).__name__,
        "feature_cols":  feat_cols,
        "roc_auc":       round(roc_auc, 4),
        "avg_precision": round(avg_prec, 4),
        "fpr":           round(fpr, 4),
        "trained_at":    datetime.utcnow().isoformat() + "Z",
        "n_train":       len(X_res),
        "n_test":        len(X_test),
    }

    bundle = {"model": model, "scaler": scaler, "metadata": metadata, "feature_cols": feat_cols}

    os.makedirs(_THIS_DIR, exist_ok=True)
    with open(_MODEL_OUT, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[TRAIN] Model saved → {_MODEL_OUT}")

    return bundle


def _generate_synthetic_data(n: int = 10000) -> pd.DataFrame:
    """Fallback: generate a synthetic credit card fraud dataset."""
    np.random.seed(42)
    fraud = np.random.choice([0, 1], size=n, p=[0.948, 0.052])
    data  = {"Time": np.random.randint(0, 172800, n),
              "Amount": np.where(fraud, np.random.exponential(200, n), np.random.exponential(50, n)),
              "Class": fraud}
    for i in range(1, 29):
        data[f"V{i}"] = np.where(fraud, np.random.normal(-1.5, 2.5, n), np.random.normal(0, 1, n))
    return pd.DataFrame(data)


def load_model(path: str = _MODEL_OUT) -> dict:
    """
    Load the saved model bundle.

    Returns:
        dict with keys: model, scaler, metadata, feature_cols
    """
    if not os.path.exists(path):
        print(f"[MODEL] Model not found at {path}. Training now...")
        return train()
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    print(f"[MODEL] Loaded {bundle['metadata']['model_type']} "
          f"(ROC-AUC: {bundle['metadata']['roc_auc']})")
    return bundle


def predict_transaction(bundle: dict, transaction: dict) -> dict:
    """
    Run inference on a single transaction dict.

    Args:
        bundle:      Model bundle returned by load_model()
        transaction: Feature dict with keys matching FEATURES + engineered features

    Returns:
        dict with fraud_probability, risk_score, decision, risk_level, confidence
    """
    feat_cols = bundle["feature_cols"]
    model     = bundle["model"]
    scaler    = bundle["scaler"]

    # Build feature vector (fill missing with 0)
    x = np.array([[transaction.get(c, 0.0) for c in feat_cols]], dtype=float)

    # Add engineered features if not already present
    if "is_night" in feat_cols and "is_night" not in transaction:
        t = transaction.get("Time", 0)
        x[0][feat_cols.index("is_night")] = 1 if (t % 86400) < 21600 else 0
    if "Amount_log" in feat_cols:
        amt = transaction.get("Amount", 0)
        x[0][feat_cols.index("Amount_log")] = np.log1p(amt)
    if "Amount_sq" in feat_cols:
        amt = transaction.get("Amount", 0)
        x[0][feat_cols.index("Amount_sq")] = amt ** 0.5

    x_scaled  = scaler.transform(x)
    proba     = float(model.predict_proba(x_scaled)[0][1])
    risk_score = round(proba * 100, 2)

    if proba >= 0.80:
        risk_level = "CRITICAL"
    elif proba >= 0.60:
        risk_level = "HIGH"
    elif proba >= 0.35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    decision   = "Fraud" if proba >= 0.50 else "Legitimate"
    confidence = abs(proba - 0.5) * 2   # 0 = uncertain, 1 = fully confident

    return {
        "fraud_probability": round(proba, 6),
        "risk_score":        risk_score,
        "decision":          decision,
        "risk_level":        risk_level,
        "confidence":        round(confidence, 4),
    }


if __name__ == "__main__":
    train()
