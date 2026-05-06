# ============================================================
# Stream Simulator — Enhanced
# Simulates a real-time transaction stream from creditcard.csv
# ============================================================

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Resolve dataset path relative to this file's location
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATASET_PATH = os.path.join(_THIS_DIR, "..", "dataset", "creditcard.csv")

MERCHANT_CATEGORIES = [
    "E-Commerce", "Retail", "Travel", "Food & Beverage",
    "Electronics", "Healthcare", "Utilities", "Finance", "Gaming"
]

LOCATIONS = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "London", "Dubai", "Singapore", "Tokyo", "Frankfurt"
]

INVESTIGATORS = ["Alice Johnson", "Bob Martinez", "Carol Singh", "David Lee", "Eve Chen"]


class StreamSimulator:
    """
    Simulates a real-time transaction data stream.
    Loads from creditcard.csv when available; falls back to synthetic data.
    """

    def __init__(self):
        self.df = None
        self._load_data()

    def _load_data(self):
        """Load the real credit card dataset or fall back to synthetic data."""
        path = _DATASET_PATH
        try:
            if os.path.exists(path):
                self.df = pd.read_csv(path)
            else:
                self._generate_dummy_data()
        except Exception as exc:
            print(f"[StreamSimulator] Warning: Could not load dataset ({exc}). Using synthetic data.")
            self._generate_dummy_data()

    def _generate_dummy_data(self):
        """Generate synthetic credit card transaction data as fallback."""
        n = 5000
        fraud_mask = np.random.choice([0, 1], size=n, p=[0.948, 0.052])
        data = {
            "Time": np.random.randint(0, 172800, n),
            "Amount": np.where(
                fraud_mask,
                np.random.exponential(200, n),   # Fraudulent: higher amounts
                np.random.exponential(50, n)      # Legitimate: lower amounts
            ),
            "Class": fraud_mask,
        }
        for i in range(1, 29):
            # Fraudulent transactions have more extreme V-feature values
            data[f"V{i}"] = np.where(
                fraud_mask,
                np.random.normal(-1.5, 2.5, n),
                np.random.normal(0, 1, n)
            )
        self.df = pd.DataFrame(data)

    def get_latest_transactions(self, n: int = 10) -> pd.DataFrame:
        """
        Fetch a simulated batch of the latest transactions.

        Args:
            n: Number of transactions to return

        Returns:
            DataFrame with enriched transaction fields
        """
        n = min(n, len(self.df))
        idx = np.random.choice(len(self.df), n, replace=False)
        sample = self.df.iloc[idx].copy().reset_index(drop=True)

        # ── Synthetic identifiers ──────────────────────────────────────────
        now = datetime.now()
        sample["txn_id"]   = [f"TXN_{random.randint(100000, 999999)}" for _ in range(n)]
        sample["card_id"]  = [f"CARD_{random.randint(1000, 9999)}"    for _ in range(n)]
        sample["account_id"] = [f"ACC_{random.randint(100, 999)}"     for _ in range(n)]

        # Stagger timestamps slightly to simulate a stream
        sample["timestamp"] = [
            (now - timedelta(seconds=random.randint(0, 300))).strftime("%Y-%m-%d %H:%M:%S")
            for _ in range(n)
        ]

        # ── Contextual fields ──────────────────────────────────────────────
        sample["merchant_category"] = [random.choice(MERCHANT_CATEGORIES) for _ in range(n)]
        sample["location"]          = [random.choice(LOCATIONS)            for _ in range(n)]

        # Is transaction at night? (22:00–06:00)
        sample["is_night"] = sample["Time"].apply(
            lambda t: 1 if (t % 86400) < 21600 or (t % 86400) > 79200 else 0
        )

        # Rapid transaction flag (within a 10-minute window of prior known fraud)
        sample["rapid_txn"] = np.random.choice([0, 1], size=n, p=[0.85, 0.15])

        # ── Fraud score calculation ────────────────────────────────────────
        # Base score from ground-truth Class; add controlled noise
        base = sample["Class"] * 0.70
        noise = np.random.uniform(0.02, 0.25, n)
        # Boost score for large amounts and night-time transactions
        amount_boost = np.where(sample["Amount"] > 300, 0.12, 0.0)
        night_boost  = np.where(sample["is_night"] == 1, 0.05, 0.0)
        sample["fraud_score"] = np.clip(base + noise + amount_boost + night_boost, 0.0, 1.0)

        # ── Risk classification ────────────────────────────────────────────
        def _assign_risk(score: float) -> str:
            if score > 0.80: return "CRITICAL"
            if score > 0.60: return "HIGH"
            if score > 0.35: return "MEDIUM"
            return "LOW"

        sample["risk_level"]   = sample["fraud_score"].apply(_assign_risk)
        sample["status"]       = "Pending"
        sample["investigator"] = None
        sample["notes"]        = ""
        sample["case_id"]      = None

        return sample

    def get_trend_data(self, days: int = 7) -> pd.DataFrame:
        """
        Generate synthetic daily fraud trend data for chart visualizations.

        Args:
            days: Number of historical days to simulate

        Returns:
            DataFrame with date, total_transactions, fraud_count, fraud_amount columns
        """
        dates = [datetime.now() - timedelta(days=i) for i in range(days - 1, -1, -1)]
        rows = []
        for d in dates:
            total = random.randint(8000, 15000)
            fraud = random.randint(30, 120)
            amt   = round(fraud * random.uniform(80, 350), 2)
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "total_transactions": total,
                "fraud_count": fraud,
                "fraud_amount": amt,
                "false_positives": random.randint(5, 25),
            })
        return pd.DataFrame(rows)

    def get_top_suspicious_accounts(self, n: int = 10) -> pd.DataFrame:
        """Return a mock top-N suspicious account table."""
        accounts = [f"ACC_{random.randint(100, 999)}" for _ in range(n)]
        return pd.DataFrame({
            "account_id":   accounts,
            "fraud_count":  np.random.randint(3, 25, n),
            "total_amount": np.round(np.random.exponential(500, n), 2),
            "avg_score":    np.round(np.random.uniform(0.65, 0.98, n), 4),
            "last_seen":    [datetime.now().strftime("%Y-%m-%d %H:%M") for _ in range(n)],
        }).sort_values("fraud_count", ascending=False).reset_index(drop=True)
