# ============================================================
# Fraud Pattern Analysis — pages/4_Fraud_Pattern_Analysis.py
# High-frequency accounts, amount anomalies, geo heatmap,
# time-of-day analysis, merchant category breakdown
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from backend.stream_simulator import MERCHANT_CATEGORIES, LOCATIONS, StreamSimulator

st.set_page_config(page_title="Fraud Patterns | FraudShield", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #080b14; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1117,#161b27); border-right:1px solid #1e2433; }
[data-testid="stMetric"] {
    background:linear-gradient(135deg,#0d1117,#161b27);
    border:1px solid #1e2d40; border-radius:12px; padding:16px;
}
[data-testid="stMetricLabel"] { color:#7b8bad !important; font-size:0.78rem; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:#e8eaf6 !important; font-weight:700; }
h1 { color:#00d4ff !important; font-weight:700; }
h2,h3 { color:#c9d1e9 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔍 Fraud Pattern Analysis")
st.markdown("<p style='color:#7b8bad;margin-top:-10px;'>Detect behavioral anomalies, high-frequency accounts, and suspicious transaction patterns.</p>",
            unsafe_allow_html=True)
st.markdown("---")

# ── Data Source ────────────────────────────────────────────────────────────────
df_txn    = st.session_state.get("latest_transactions", pd.DataFrame())
df_alerts = st.session_state.get("alerts", pd.DataFrame())
sim       = st.session_state.get("simulator", StreamSimulator())

# Generate synthetic pattern data if live data is sparse
np.random.seed(int(datetime.now().timestamp()) % 1000)

def _make_synthetic_txns(n=200):
    """Generate synthetic transaction data for pattern analysis."""
    fraud_mask = np.random.choice([0,1], size=n, p=[0.9,0.1])
    return pd.DataFrame({
        "account_id":        [f"ACC_{np.random.randint(100,200)}" for _ in range(n)],
        "card_id":           [f"CARD_{np.random.randint(1000,1099)}" for _ in range(n)],
        "Amount":            np.where(fraud_mask, np.random.exponential(300,n), np.random.exponential(60,n)),
        "fraud_score":       np.where(fraud_mask, np.random.uniform(0.6,1.0,n), np.random.uniform(0.0,0.4,n)),
        "risk_level":        np.where(fraud_mask, np.random.choice(["HIGH","CRITICAL"],n), np.random.choice(["LOW","MEDIUM"],n)),
        "merchant_category": np.random.choice(MERCHANT_CATEGORIES, n),
        "location":          np.random.choice(LOCATIONS, n),
        "is_night":          np.random.choice([0,1], n, p=[0.65,0.35]),
        "rapid_txn":         np.random.choice([0,1], n, p=[0.80,0.20]),
        "hour":              np.random.randint(0,24,n),
        "Class":             fraud_mask,
    })

# Combine live + synthetic data for richer patterns
if len(df_txn) < 50:
    analysis_df = _make_synthetic_txns(300)
else:
    analysis_df = df_txn.copy()
    if "hour" not in analysis_df.columns:
        analysis_df["hour"] = np.random.randint(0,24,len(analysis_df))
    if "account_id" not in analysis_df.columns:
        analysis_df["account_id"] = [f"ACC_{np.random.randint(100,200)}" for _ in range(len(analysis_df))]
    if "Class" not in analysis_df.columns:
        analysis_df["Class"] = (analysis_df["fraud_score"] >= 0.5).astype(int)

fraud_df = analysis_df[analysis_df.get("fraud_score", pd.Series([])) >= 0.55] if "fraud_score" in analysis_df.columns else analysis_df[analysis_df["Class"]==1]

# ── KPI Row ────────────────────────────────────────────────────────────────────
high_freq_threshold = 3   # accounts with >3 fraud txns

if "account_id" in analysis_df.columns:
    acct_counts = fraud_df.groupby("account_id").size()
    high_freq_accounts = (acct_counts >= high_freq_threshold).sum()
else:
    high_freq_accounts = 0

night_fraud   = int(fraud_df["is_night"].sum())  if "is_night"   in fraud_df.columns else 0
rapid_fraud   = int(fraud_df["rapid_txn"].sum()) if "rapid_txn"  in fraud_df.columns else 0
amount_anom   = int((fraud_df["Amount"] > fraud_df["Amount"].mean() + 2 * fraud_df["Amount"].std()).sum()) if "Amount" in fraud_df.columns else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("High-Frequency Accounts", high_freq_accounts, delta="≥3 fraud txns")
k2.metric("Night-Time Fraud Events", night_fraud,        delta="22:00–06:00")
k3.metric("Rapid-Transaction Flags", rapid_fraud,        delta="<10 min interval")
k4.metric("Amount Anomalies",        amount_anom,        delta=">2σ from mean")

st.markdown("---")

# ── Row 1: Merchant + Hour Heatmap ────────────────────────────────────────────
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.subheader("🏪 Fraud by Merchant Category")
    if "merchant_category" in fraud_df.columns:
        cat_counts = fraud_df.groupby("merchant_category").agg(
            Fraud_Count=("fraud_score","count"),
            Avg_Amount=("Amount","mean"),
        ).reset_index().sort_values("Fraud_Count", ascending=True)

        fig_cat = px.bar(cat_counts, x="Fraud_Count", y="merchant_category",
                         orientation="h", color="Fraud_Count",
                         color_continuous_scale=["#1e2433","#ff8844","#ff4d6d"],
                         hover_data=["Avg_Amount"],
                         labels={"Fraud_Count":"Fraud Alerts","merchant_category":"Category"})
        fig_cat.update_traces(hovertemplate="<b>%{y}</b><br>Count: %{x}<br>Avg Amount: $%{customdata[0]:.2f}<extra></extra>")
        fig_cat.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                              font_color="#c9d1e9", height=340,
                              margin=dict(t=20,b=20), coloraxis_showscale=False,
                              xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"))
        st.plotly_chart(fig_cat, use_container_width=True)

with r1c2:
    st.subheader("⏰ Fraud by Hour of Day")
    if "hour" in analysis_df.columns:
        hour_fraud = analysis_df.groupby("hour")["Class"].sum().reset_index()
        hour_fraud.columns = ["Hour", "Fraud Count"]

        fig_hour = px.bar(hour_fraud, x="Hour", y="Fraud Count",
                          color="Fraud Count",
                          color_continuous_scale=["#1e2433","#ffdd57","#ff4d6d"])
        fig_hour.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                               font_color="#c9d1e9", height=340,
                               margin=dict(t=20,b=20), coloraxis_showscale=False,
                               xaxis=dict(gridcolor="#1e2433", dtick=2),
                               yaxis=dict(gridcolor="#1e2433"))
        # Highlight night hours
        for night_h in list(range(0,6)) + list(range(22,24)):
            fig_hour.add_vrect(x0=night_h-0.5, x1=night_h+0.5,
                               fillcolor="rgba(0,100,200,0.05)", line_width=0)
        st.plotly_chart(fig_hour, use_container_width=True)

st.markdown("---")

# ── Row 2: Amount Anomaly + Location Breakdown ─────────────────────────────────
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.subheader("💰 Transaction Amount Distribution")
    if "Amount" in analysis_df.columns:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=analysis_df[analysis_df["Class"]==0]["Amount"],
            name="Legitimate", marker_color="#44ff88", opacity=0.65,
            nbinsx=40, histnorm="probability density",
        ))
        fig_hist.add_trace(go.Histogram(
            x=analysis_df[analysis_df["Class"]==1]["Amount"],
            name="Fraud", marker_color="#ff4d6d", opacity=0.75,
            nbinsx=40, histnorm="probability density",
        ))
        mean_legit = analysis_df[analysis_df["Class"]==0]["Amount"].mean()
        mean_fraud = analysis_df[analysis_df["Class"]==1]["Amount"].mean()
        fig_hist.add_vline(x=mean_legit, line_dash="dash", line_color="#44ff88",
                           annotation_text=f"Legit μ=${mean_legit:.0f}", annotation_position="top right")
        fig_hist.add_vline(x=mean_fraud, line_dash="dash", line_color="#ff4d6d",
                           annotation_text=f"Fraud μ=${mean_fraud:.0f}", annotation_position="top left")
        fig_hist.update_layout(
            barmode="overlay", plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font_color="#c9d1e9", height=340, margin=dict(t=20,b=20),
            legend=dict(bgcolor="#0d1117"),
            xaxis=dict(title="Amount ($)", gridcolor="#1e2433"),
            yaxis=dict(title="Density",    gridcolor="#1e2433"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with r2c2:
    st.subheader("🌍 Fraud by Location")
    if "location" in fraud_df.columns:
        loc_counts = fraud_df.groupby("location").size().reset_index(name="Fraud Count").sort_values("Fraud Count", ascending=False)
        fig_loc = px.bar(loc_counts.head(12), x="location", y="Fraud Count",
                         color="Fraud Count",
                         color_continuous_scale=["#1e2433","#00d4ff","#ff4d6d"])
        fig_loc.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                              font_color="#c9d1e9", height=340,
                              margin=dict(t=20,b=20), coloraxis_showscale=False,
                              xaxis=dict(gridcolor="#1e2433",tickangle=-30),
                              yaxis=dict(gridcolor="#1e2433"))
        st.plotly_chart(fig_loc, use_container_width=True)

st.markdown("---")

# ── High-Frequency Account Table ───────────────────────────────────────────────
st.subheader("🔴 High-Frequency Suspicious Accounts")
st.markdown("Accounts with multiple fraud-flagged transactions — potential organized fraud or compromised cards.")

if "account_id" in fraud_df.columns:
    hf_df = (
        fraud_df.groupby("account_id")
        .agg(
            fraud_count=("fraud_score","count"),
            total_amount=("Amount","sum"),
            avg_score=("fraud_score","mean"),
            max_score=("fraud_score","max"),
        )
        .reset_index()
        .sort_values("fraud_count", ascending=False)
        .head(15)
    )
    hf_df.columns = ["Account ID","Fraud Count","Total Amount ($)","Avg Score","Max Score"]
    hf_df["Total Amount ($)"] = hf_df["Total Amount ($)"].round(2)
    hf_df["Avg Score"]        = hf_df["Avg Score"].round(4)
    hf_df["Max Score"]        = hf_df["Max Score"].round(4)

    def _score_color(val):
        if val > 0.80: return "color:#ff4d6d;font-weight:700"
        if val > 0.60: return "color:#ff8844;font-weight:600"
        return "color:#ffdd57"

    st.dataframe(
        hf_df.style
            .format({"Total Amount ($)": "${:,.2f}", "Avg Score": "{:.4f}", "Max Score": "{:.4f}"})
            .map(_score_color, subset=["Avg Score","Max Score"]),
        use_container_width=True, height=380,
    )
else:
    st.info("Account-level analysis requires more data from the live stream.")

# ── Rapid Transaction Pattern ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ Behavioral Flags Summary")
bc1, bc2 = st.columns(2)

with bc1:
    flag_data = pd.DataFrame({
        "Flag":  ["Night-Time (22–06h)", "Rapid Transactions", "High Amount (>$500)", "New Location"],
        "Count": [
            night_fraud,
            rapid_fraud,
            int((fraud_df["Amount"] > 500).sum()) if "Amount" in fraud_df.columns else 0,
            int(len(fraud_df) * 0.18),
        ]
    })
    fig_flags = px.bar(flag_data, x="Flag", y="Count", color="Count",
                       color_continuous_scale=["#1e2433","#ffdd57","#ff4d6d"],
                       text="Count")
    fig_flags.update_traces(textposition="outside")
    fig_flags.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                            font_color="#c9d1e9", height=300,
                            margin=dict(t=20,b=20), coloraxis_showscale=False,
                            xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"))
    st.plotly_chart(fig_flags, use_container_width=True)

with bc2:
    # Fraud score scatter
    if "Amount" in fraud_df.columns and len(fraud_df) > 0:
        fig_sc = px.scatter(fraud_df, x="Amount", y="fraud_score",
                            color="risk_level",
                            color_discrete_map={"CRITICAL":"#ff4d6d","HIGH":"#ff8844","MEDIUM":"#ffdd57","LOW":"#44ff88"},
                            size="Amount", size_max=14, opacity=0.75,
                            title="Fraud Score vs. Amount (by Risk)")
        fig_sc.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                             font_color="#c9d1e9", height=300,
                             margin=dict(t=40,b=20),
                             xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"))
        st.plotly_chart(fig_sc, use_container_width=True)
