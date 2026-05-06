# ============================================================
# Main Dashboard — app.py
# Real-Time Fraud Monitoring Dashboard (Streamlit)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta

from backend.stream_simulator import StreamSimulator

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FraudShield | Real-Time Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "FraudShield v1.0 — Enterprise Fraud Detection System"},
)

# ── CSS Theme ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main { background-color: #080b14; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b27 100%);
    border-right: 1px solid #1e2433;
}

/* KPI Cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1117 0%, #161b27 100%);
    border: 1px solid #1e2d40;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 4px 20px rgba(0,212,255,0.05);
    transition: transform 0.2s;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); }
[data-testid="stMetricLabel"]  { color: #7b8bad !important; font-size: 0.80rem; letter-spacing: 0.05em; text-transform: uppercase; }
[data-testid="stMetricValue"]  { color: #e8eaf6 !important; font-size: 1.6rem; font-weight: 700; }
[data-testid="stMetricDelta"]  { font-size: 0.80rem; }

/* Tab styling */
[data-testid="stTabs"] button { color: #7b8bad; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #00d4ff; border-bottom: 2px solid #00d4ff; }

h1 { color: #00d4ff !important; font-weight: 700; letter-spacing: -0.02em; }
h2, h3 { color: #c9d1e9 !important; font-weight: 600; }

/* Alert badge */
.badge-critical { color: #ff4d6d; font-weight: 700; }
.badge-high     { color: #ff8844; font-weight: 700; }
.badge-medium   { color: #ffdd57; font-weight: 700; }
.badge-low      { color: #44ff88; font-weight: 700; }

div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* Status dot */
.status-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #44ff88; border-radius: 50%;
    margin-right: 6px; animation: pulse 2s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(68,255,136,0.6); }
    70%  { box-shadow: 0 0 0 10px rgba(68,255,136,0); }
    100% { box-shadow: 0 0 0 0 rgba(68,255,136,0); }
}
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────────────
if "simulator" not in st.session_state:
    st.session_state.simulator = StreamSimulator()
if "latest_transactions" not in st.session_state:
    st.session_state.latest_transactions = pd.DataFrame()
if "alerts" not in st.session_state:
    st.session_state.alerts = pd.DataFrame()
if "cases" not in st.session_state:
    st.session_state.cases = pd.DataFrame()
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []
if "total_processed" not in st.session_state:
    st.session_state.total_processed = 0
if "fraud_caught" not in st.session_state:
    st.session_state.fraud_caught = 0
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()

sim: StreamSimulator = st.session_state.simulator

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px;'>
        <div style='font-size:2.2rem;'>🛡️</div>
        <div style='font-size:1.1rem; font-weight:700; color:#00d4ff;'>FraudShield</div>
        <div style='font-size:0.72rem; color:#7b8bad; letter-spacing:0.1em;'>ENTERPRISE MONITORING</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Stream Controls**")
    stream_speed = st.slider("Throughput (TPS)", 10, 500, 100, step=10)
    auto_refresh = st.toggle("Live Mode", value=True)

    st.markdown("---")
    fraud_threshold = st.slider("Alert Threshold", 0.3, 0.95, 0.60, step=0.05,
                                help="Fraud probability above this value triggers an alert")
    st.markdown("---")

    if st.button("🔄 Reset System", use_container_width=True):
        for key in ["latest_transactions", "alerts", "cases", "audit_log",
                    "total_processed", "fraud_caught"]:
            if key in ["total_processed", "fraud_caught"]:
                st.session_state[key] = 0
            elif key == "audit_log":
                st.session_state[key] = []
            else:
                st.session_state[key] = pd.DataFrame()
        st.session_state.session_start = datetime.now()
        st.rerun()

    # System status
    uptime = datetime.now() - st.session_state.session_start
    uptime_str = f"{int(uptime.total_seconds() // 60)}m {int(uptime.total_seconds() % 60)}s"
    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1e2433;border-radius:10px;padding:12px;margin-top:10px;'>
        <div style='font-size:0.72rem;color:#7b8bad;text-transform:uppercase;letter-spacing:0.08em;'>System Status</div>
        <div style='margin-top:6px;'><span class='status-dot'></span>
            <span style='color:#44ff88;font-weight:600;font-size:0.9rem;'>ONLINE</span></div>
        <div style='font-size:0.75rem;color:#7b8bad;margin-top:6px;'>Uptime: {uptime_str}</div>
        <div style='font-size:0.75rem;color:#7b8bad;'>Threshold: {fraud_threshold:.0%}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Data Fetch ─────────────────────────────────────────────────────────────────
def fetch_data():
    n       = max(5, int(stream_speed / 10))
    batch   = sim.get_latest_transactions(n=n)
    st.session_state.total_processed += len(batch)

    # Identify new fraud alerts
    new_fraud = batch[batch["fraud_score"] >= fraud_threshold].copy()
    st.session_state.fraud_caught += len(new_fraud)

    # Rolling transaction buffer (keep last 200)
    if st.session_state.latest_transactions.empty:
        st.session_state.latest_transactions = batch
    else:
        st.session_state.latest_transactions = (
            pd.concat([batch, st.session_state.latest_transactions])
            .drop_duplicates(subset=["txn_id"])
            .head(200)
            .reset_index(drop=True)
        )

    # Append new alerts (dedup by txn_id)
    if not new_fraud.empty:
        if st.session_state.alerts.empty:
            st.session_state.alerts = new_fraud
        else:
            st.session_state.alerts = (
                pd.concat([new_fraud, st.session_state.alerts])
                .drop_duplicates(subset=["txn_id"])
                .head(500)
                .reset_index(drop=True)
            )

if auto_refresh:
    fetch_data()
    time.sleep(1.8)
    st.rerun()
else:
    if st.sidebar.button("⟳ Manual Refresh"):
        fetch_data()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='margin-bottom:4px;'>🛡️ FraudShield — Real-Time Monitoring</h1>
<p style='color:#7b8bad; margin-top:0; font-size:0.9rem;'>
    Live transaction intelligence &amp; fraud surveillance platform
</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ── KPI Row ────────────────────────────────────────────────────────────────────
df_txn    = st.session_state.latest_transactions
df_alerts = st.session_state.alerts
total     = st.session_state.total_processed
fraud_cnt = st.session_state.fraud_caught
det_rate  = (fraud_cnt / max(1, total)) * 100
pending   = len(df_alerts[df_alerts["status"] == "Pending"]) if not df_alerts.empty else 0
fraud_amt = df_alerts["Amount"].sum() if not df_alerts.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Transactions Processed", f"{total:,}", delta=f"+{max(5,int(stream_speed/10))} batch")
k2.metric("Active Alerts", f"{pending}", delta=f"{fraud_cnt} caught")
k3.metric("Detection Rate", f"{det_rate:.2f}%")
k4.metric("Throughput", f"{stream_speed} TPS")
k5.metric("Fraud Amount Blocked", f"${fraud_amt:,.0f}")

st.markdown("---")

# ── Charts Row ─────────────────────────────────────────────────────────────────
col_main, col_side = st.columns([3, 2])

with col_main:
    tab1, tab2 = st.tabs(["📊 Risk Distribution", "📈 Fraud Trend (7d)"])

    with tab1:
        if not df_txn.empty:
            risk_counts = df_txn["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            color_map = {"CRITICAL": "#ff4d6d", "HIGH": "#ff8844", "MEDIUM": "#ffdd57", "LOW": "#44ff88"}
            fig = px.bar(
                risk_counts, x="Risk Level", y="Count",
                color="Risk Level", color_discrete_map=color_map,
                text="Count",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font_color="#c9d1e9", showlegend=False,
                margin=dict(t=20, b=20), height=280,
                xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for data stream...")

    with tab2:
        trend_df = sim.get_trend_data(days=7)
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["fraud_count"],
            name="Fraud Count", line=dict(color="#ff4d6d", width=2.5),
            fill="tozeroy", fillcolor="rgba(255,77,109,0.1)",
        ), secondary_y=False)
        fig2.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["fraud_amount"],
            name="Fraud Amount ($)", line=dict(color="#00d4ff", width=2, dash="dot"),
        ), secondary_y=True)
        fig2.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#c9d1e9",
            legend=dict(bgcolor="#0d1117"), height=280,
            margin=dict(t=20, b=20),
            xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"),
        )
        st.plotly_chart(fig2, use_container_width=True)

with col_side:
    tab3, tab4 = st.tabs(["⚡ System Health", "🥧 Risk Breakdown"])

    with tab3:
        latency = np.random.normal(14, 3)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=latency,
            delta={"reference": 20, "decreasing": {"color": "#44ff88"}, "increasing": {"color": "#ff4d6d"}},
            title={"text": "API Latency (ms)", "font": {"color": "#c9d1e9", "size": 13}},
            gauge={
                "axis": {"range": [0, 50], "tickcolor": "#7b8bad", "tickfont": {"color": "#7b8bad"}},
                "bar":  {"color": "#00d4ff"},
                "steps": [
                    {"range": [0, 20],  "color": "#0d1b2e"},
                    {"range": [20, 35], "color": "#1a2a10"},
                    {"range": [35, 50], "color": "#2a1010"},
                ],
                "threshold": {"line": {"color": "#ff4d6d", "width": 2}, "value": 40},
            }
        ))
        fig_gauge.update_layout(paper_bgcolor="#0d1117", font_color="#c9d1e9", height=260, margin=dict(t=30,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with tab4:
        if not df_txn.empty:
            rc2 = df_txn["risk_level"].value_counts().reset_index()
            rc2.columns = ["Risk Level", "Count"]
            colors = [{"CRITICAL": "#ff4d6d", "HIGH": "#ff8844", "MEDIUM": "#ffdd57", "LOW": "#44ff88"}.get(r, "#888") for r in rc2["Risk Level"]]
            fig_pie = go.Figure(go.Pie(
                labels=rc2["Risk Level"], values=rc2["Count"],
                marker=dict(colors=colors),
                hole=0.52, textinfo="percent+label",
                textfont=dict(size=12, color="#c9d1e9"),
            ))
            fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#c9d1e9",
                                  height=260, margin=dict(t=20,b=10), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Awaiting data...")

st.markdown("---")

# ── Bottom Row: Transaction Feed + Suspicious Accounts ────────────────────────
col_feed, col_accts = st.columns([3, 2])

with col_feed:
    st.subheader("🔴 Live Transaction Feed")
    if not df_txn.empty:
        show_cols = ["timestamp", "txn_id", "card_id", "Amount", "merchant_category", "location", "fraud_score", "risk_level"]
        # Only show columns that exist
        show_cols = [c for c in show_cols if c in df_txn.columns]
        disp = df_txn[show_cols].head(20).copy()

        def _risk_color(val):
            return {
                "CRITICAL": "color: #ff4d6d; font-weight:700;",
                "HIGH":     "color: #ff8844; font-weight:700;",
                "MEDIUM":   "color: #ffdd57; font-weight:600;",
                "LOW":      "color: #44ff88;",
            }.get(val, "")

        fmt = {}
        if "fraud_score" in disp.columns: fmt["fraud_score"] = "{:.4f}"
        if "Amount"      in disp.columns: fmt["Amount"]      = "${:.2f}"

        styled = disp.style.format(fmt)
        if "risk_level" in disp.columns:
            styled = styled.map(_risk_color, subset=["risk_level"])

        st.dataframe(styled, use_container_width=True, height=340)
    else:
        st.info("Stream initializing...")

with col_accts:
    st.subheader("🕵️ Top Suspicious Accounts")
    susp = sim.get_top_suspicious_accounts(n=8)
    susp_disp = susp.copy()
    susp_disp["avg_score"] = susp_disp["avg_score"].map("{:.4f}".format)
    susp_disp["total_amount"] = susp_disp["total_amount"].map("${:,.2f}".format)
    st.dataframe(susp_disp, use_container_width=True, height=340)

# ── Fraud Pattern Mini-Section ─────────────────────────────────────────────────
if not df_txn.empty and "merchant_category" in df_txn.columns:
    st.markdown("---")
    st.subheader("🔍 Fraud Patterns — Category & Time")
    pc1, pc2 = st.columns(2)

    with pc1:
        fraud_by_cat = (
            df_txn[df_txn["fraud_score"] >= fraud_threshold]
            .groupby("merchant_category")["fraud_score"]
            .count()
            .reset_index()
            .rename(columns={"fraud_score": "Fraud Alerts"})
            .sort_values("Fraud Alerts", ascending=True)
        )
        if not fraud_by_cat.empty:
            fig_cat = px.bar(fraud_by_cat, x="Fraud Alerts", y="merchant_category",
                             orientation="h", color="Fraud Alerts",
                             color_continuous_scale=["#1e2433", "#ff4d6d"],
                             title="Fraud Alerts by Merchant Category")
            fig_cat.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                                  font_color="#c9d1e9", height=280, margin=dict(t=40,b=20),
                                  coloraxis_showscale=False)
            st.plotly_chart(fig_cat, use_container_width=True)

    with pc2:
        # Amount distribution scatter
        fig_scatter = px.scatter(
            df_txn, x="Amount", y="fraud_score",
            color="risk_level",
            color_discrete_map={"CRITICAL": "#ff4d6d", "HIGH": "#ff8844", "MEDIUM": "#ffdd57", "LOW": "#44ff88"},
            title="Amount vs Fraud Score",
            opacity=0.7, size_max=8,
        )
        fig_scatter.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                                  font_color="#c9d1e9", height=280, margin=dict(t=40,b=20),
                                  xaxis=dict(gridcolor="#1e2433"), yaxis=dict(gridcolor="#1e2433"))
        st.plotly_chart(fig_scatter, use_container_width=True)
