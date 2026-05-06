# ============================================================
# Synthetic Data Generator — data/generate_sample.py
# Generates a realistic credit card fraud dataset
# Use when creditcard.csv is unavailable
# ============================================================

import pandas as pd
import numpy as np
import os
from datetime import datetime

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "sample_transactions.csv")


def generate_dataset(n_samples: int = 10_000, fraud_rate: float = 0.052, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic credit card transaction dataset that mirrors the
    structure of the Kaggle creditcard.csv dataset.

    Args:
        n_samples:  Total number of transactions to generate
        fraud_rate: Proportion of fraudulent transactions (default ~5.2%)
        seed:       Random seed for reproducibility

    Returns:
        DataFrame with columns: Time, V1–V28, Amount, Class
    """
    rng = np.random.default_rng(seed)

    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud
    labels  = np.array([1] * n_fraud + [0] * n_legit)
    rng.shuffle(labels)

    data: dict = {}

    # Time (seconds from first transaction, up to 2 days)
    data["Time"] = np.sort(rng.uniform(0, 172_800, n_samples))

    # V1–V28: PCA-derived features
    # Legitimate transactions cluster around μ=0; fraud has shifted distributions
    for i in range(1, 29):
        legit_vals = rng.normal(0, 1, n_samples)
        fraud_shift = rng.choice([-2.5, -1.5, 0, 1.5, 2.5])  # Feature-specific shift
        fraud_vals  = rng.normal(fraud_shift, 2.0, n_samples)
        data[f"V{i}"] = np.where(labels == 1, fraud_vals, legit_vals)

    # Amount — fraud tends toward higher amounts
    legit_amount = rng.exponential(scale=50,  size=n_samples)
    fraud_amount = rng.exponential(scale=220, size=n_samples)
    data["Amount"] = np.where(labels == 1, fraud_amount, legit_amount).clip(0.01, 25_000)

    data["Class"] = labels

    df = pd.DataFrame(data)
    print(f"[GENERATOR] Generated {n_samples:,} transactions | Fraud: {n_fraud:,} ({fraud_rate:.1%})")
    return df


def save_dataset(df: pd.DataFrame, path: str = OUTPUT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[GENERATOR] Dataset saved → {path} ({os.path.getsize(path) / 1024:.1f} KB)")


def generate_enriched_transactions(n: int = 500) -> pd.DataFrame:
    """
    Generate fully-enriched transactions with merchant, location, and
    dashboard fields — suitable for testing without the stream simulator.
    """
    import random
    from datetime import timedelta

    MERCHANT_CATEGORIES = [
        "E-Commerce", "Retail", "Travel", "Food & Beverage",
        "Electronics", "Healthcare", "Utilities", "Finance", "Gaming"
    ]
    LOCATIONS = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "London", "Dubai", "Singapore", "Tokyo", "Frankfurt"
    ]

    base_df = generate_dataset(n_samples=n, seed=random.randint(0, 9999))
    now = datetime.now()

    base_df["txn_id"]           = [f"TXN_{random.randint(100000,999999)}" for _ in range(n)]
    base_df["card_id"]          = [f"CARD_{random.randint(1000,9999)}"   for _ in range(n)]
    base_df["account_id"]       = [f"ACC_{random.randint(100,999)}"      for _ in range(n)]
    base_df["timestamp"]        = [(now - timedelta(seconds=i*30)).strftime("%Y-%m-%d %H:%M:%S") for i in range(n)]
    base_df["merchant_category"] = [random.choice(MERCHANT_CATEGORIES) for _ in range(n)]
    base_df["location"]          = [random.choice(LOCATIONS)            for _ in range(n)]
    base_df["is_night"]          = ((base_df["Time"] % 86400) < 21600).astype(int)
    base_df["rapid_txn"]         = np.random.choice([0,1], n, p=[0.85,0.15])
    base_df["fraud_score"]       = np.clip(base_df["Class"] * 0.75 + np.random.uniform(0.02,0.25,n), 0, 1)
    base_df["risk_level"]        = pd.cut(base_df["fraud_score"],
                                          bins=[0, 0.35, 0.60, 0.80, 1.0],
                                          labels=["LOW","MEDIUM","HIGH","CRITICAL"])
    base_df["status"]            = "Pending"
    return base_df


if __name__ == "__main__":
    df = generate_dataset(n_samples=50_000)
    save_dataset(df)
    print("\nSample rows:")
    print(df.head(3).to_string())
    print(f"\nFraud distribution:\n{df['Class'].value_counts()}")
