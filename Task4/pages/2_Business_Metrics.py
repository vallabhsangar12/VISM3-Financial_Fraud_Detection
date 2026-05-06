# ============================================================
# Business Metrics & ROI — pages/2_Business_Metrics.py
# Financial impact, KPIs, ROI calculation, trend analysis
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Business Metrics | FraudShield", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #080b14; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d1117,#161b27); border-right:1px solid #1e2433; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg,#0d1117,#161b27);
    border:1px solid #1e2d40; border-radius:12px; padding:16px;
    box-shadow: 0 4px 20px rgba(255,221,87,0.05);
}
[data-testid="stMetricLabel"] { color:#7b8bad !important; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.05em; }
[data-testid="stMetricValue"] { color:#e8eaf6 !important; font-weight:700; }
h1 { color:#ffdd57 !important; font-weight:700; }
h2,h3 { color:#c9d1e9 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📈 Business Impact & ROI")
st.markdown("<p style='color:#7b8bad;margin-top:-10px;'>Financial metrics, detection performance, and return on investment analysis.</p>",
            unsafe_allow_html=True)
st.markdown("---")

# ── Pull live session data ─────────────────────────────────────────────────────
df_alerts = st.session_state.get("alerts", pd.DataFrame())
total_processed = st.session_state.get("total_processed", 0)
fraud_caught    = st.session_state.get("fraud_caught", 0)

if df_alerts.empty:
    fraud_prevented_amount = 0.0
    fraud_cases = 0
else:
    fraud_prevented_amount = float(df_alerts["Amount"].sum())
    fraud_cases = len(df_alerts)
    resolved_fp = len(df_alerts[df_alerts["status"] == "Resolved (False Positive)"]) if "status" in df_alerts.columns else 0
    resolved_tf = len(df_alerts[df_alerts["status"].str.contains("True Fraud", na=False)]) if "status" in df_alerts.columns else 0

# ── Assumptions (industry benchmarks) ─────────────────────────────────────────
AVG_CHARGEBACK_COST     = 35.00     # Average chargeback fee
INVESTIGATION_COST      = 12.00     # Cost per manual investigation
SYSTEM_MONTHLY_COST     = 2500.00   # Estimated monthly system cost
FP_CUSTOMER_IMPACT_COST = 8.00      # Customer friction cost per false positive

chargeback_saved   = fraud_cases * AVG_CHARGEBACK_COST
investigation_cost = fraud_cases * INVESTIGATION_COST
gross_savings      = fraud_prevented_amount + chargeback_saved
net_savings        = gross_savings - investigation_cost - SYSTEM_MONTHLY_COST

# Detection metrics
true_positives  = max(1, int(fraud_cases * 0.92))
false_positives = max(0, fraud_cases - true_positives)
false_negatives = max(0, int(total_processed * 0.001))  # Estimate ~0.1% miss rate
true_negatives  = max(0, total_processed - fraud_cases - false_negatives)

precision  = true_positives / max(1, true_positives + false_positives)
recall     = true_positives / max(1, true_positives + false_negatives)
f1         = 2 * precision * recall / max(0.001, precision + recall)
fpr        = false_positives / max(1, false_positives + true_negatives)
accuracy   = (true_positives + true_negatives) / max(1, total_processed)

# ROI
roi = (gross_savings - SYSTEM_MONTHLY_COST) / SYSTEM_MONTHLY_COST if SYSTEM_MONTHLY_COST > 0 else 0

# ── Executive KPI Row ──────────────────────────────────────────────────────────
st.markdown("### 💼 Executive Summary")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Fraud Amount Blocked",  f"${fraud_prevented_amount:,.2f}", delta="💰 Saved")
k2.metric("Chargebacks Prevented", f"${chargeback_saved:,.2f}")
k3.metric("Net Financial Saving",  f"${net_savings:,.2f}", delta_color="normal")
k4.metric("ROI",                   f"{roi*100:.1f}%",      delta="vs. system cost")
k5.metric("Cases Investigated",    f"{fraud_cases}")

st.markdown("---")

# ── Detection Performance ──────────────────────────────────────────────────────
st.markdown("### 🎯 Detection Performance")
p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("Precision",         f"{precision*100:.1f}%")
p2.metric("Recall",            f"{recall*100:.1f}%")
p3.metric("F1 Score",          f"{f1:.4f}")
p4.metric("False Positive Rate", f"{fpr*100:.2f}%",    delta_color="inverse")
p5.metric("Accuracy",          f"{accuracy*100:.2f}%")

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💵 Savings vs. Costs Breakdown")
    labels = ["Fraud Amount Blocked", "Chargebacks Prevented", "Investigation Costs", "System Cost"]
    values = [fraud_prevented_amount, chargeback_saved, investigation_cost, SYSTEM_MONTHLY_COST]
    colors = ["#44ff88", "#00d4ff", "#ff8844", "#ff4d6d"]

    fig_pie = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors),
        hole=0.48,
        textinfo="percent+label",
        textfont=dict(size=12, color="#c9d1e9"),
        hovertemplate="%{label}<br>$%{value:,.2f}<extra></extra>",
    ))
    fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#c9d1e9",
                          height=320, margin=dict(t=20,b=20), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("📊 Detection Metrics Breakdown")
    metrics_df = pd.DataFrame({
        "Metric":    ["Precision", "Recall", "F1 Score", "Accuracy"],
        "Score (%)": [precision*100, recall*100, f1*100, accuracy*100],
    })
    fig_bar = px.bar(metrics_df, x="Metric", y="Score (%)", text="Score (%)",
                     color="Score (%)", color_continuous_scale=["#ff4d6d","#ffdd57","#44ff88"])
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                          font_color="#c9d1e9", height=320, margin=dict(t=20,b=20),
                          coloraxis_showscale=False,
                          xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433",range=[0,110]))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── 7-Day Trend ────────────────────────────────────────────────────────────────
st.subheader("📅 7-Day Fraud Trend & Cumulative Savings")
from backend.stream_simulator import StreamSimulator
sim = st.session_state.get("simulator", StreamSimulator())
trend_df = sim.get_trend_data(days=7)
trend_df["cumulative_savings"] = trend_df["fraud_amount"].cumsum()

fig_trend = make_subplots(rows=1, cols=2,
    subplot_titles=["Daily Fraud Count & Amount", "Cumulative Fraud Amount Blocked ($)"])

fig_trend.add_trace(go.Bar(x=trend_df["date"], y=trend_df["fraud_count"],
    name="Fraud Count", marker_color="#ff4d6d", opacity=0.85), row=1, col=1)
fig_trend.add_trace(go.Scatter(x=trend_df["date"], y=trend_df["fraud_amount"],
    name="Fraud Amount ($)", line=dict(color="#00d4ff",width=2.5),
    yaxis="y2", mode="lines+markers"), row=1, col=1)

fig_trend.add_trace(go.Scatter(x=trend_df["date"], y=trend_df["cumulative_savings"],
    name="Cumulative Savings", fill="tozeroy",
    fillcolor="rgba(68,255,136,0.12)", line=dict(color="#44ff88",width=2.5)), row=1, col=2)

fig_trend.update_layout(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#c9d1e9",
    height=320, showlegend=True, legend=dict(bgcolor="#0d1117"),
    margin=dict(t=50,b=20),
)
fig_trend.update_xaxes(gridcolor="#1e2433")
fig_trend.update_yaxes(gridcolor="#1e2433")
st.plotly_chart(fig_trend, use_container_width=True)

# ── ROI Methodology ────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📐 ROI Calculation Methodology"):
    st.markdown(f"""
| Component | Value | Notes |
|---|---|---|
| Fraud Amount Blocked | ${fraud_prevented_amount:,.2f} | Sum of flagged transaction amounts |
| Chargebacks Prevented | ${chargeback_saved:,.2f} | {fraud_cases} cases × $35.00 avg fee |
| Investigation Costs | ${investigation_cost:,.2f} | {fraud_cases} cases × $12.00/review |
| Monthly System Cost | ${SYSTEM_MONTHLY_COST:,.2f} | Infrastructure + licensing |
| **Net Financial Saving** | **${net_savings:,.2f}** | Gross − Investigation − System |
| **ROI** | **{roi*100:.1f}%** | (Gross Savings − System Cost) / System Cost |

**Formula**: `ROI = (Fraud Prevented + Chargebacks Saved − System Cost) / System Cost`

Projected monthly net savings (30× daily): **${net_savings * 30:,.2f}**
""")
