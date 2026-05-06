# ============================================================
# Alert Management — pages/1_Alert_Management.py
# Full alert lifecycle: filter, assign, update, create cases
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime

from backend.stream_simulator import INVESTIGATORS

st.set_page_config(page_title="Alert Management | FraudShield", page_icon="🚨", layout="wide")

# ── Theme ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #080b14; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1117, #161b27); border-right: 1px solid #1e2433; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg,#0d1117,#161b27);
    border:1px solid #1e2d40; border-radius:12px; padding:16px;
}
[data-testid="stMetricLabel"] { color:#7b8bad !important; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.05em; }
[data-testid="stMetricValue"] { color:#e8eaf6 !important; font-weight:700; }
h1 { color:#ff4d6d !important; font-weight:700; }
h2,h3 { color:#c9d1e9 !important; }
.stButton>button { background:linear-gradient(135deg,#ff4d6d,#c62d4b); color:white; border:none; border-radius:8px; font-weight:600; }
.stButton>button:hover { opacity:0.88; transform:translateY(-1px); }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🚨 Alert Management & Investigation")
st.markdown("<p style='color:#7b8bad;margin-top:-10px;'>Monitor, triage and resolve fraud alerts in real-time.</p>",
            unsafe_allow_html=True)
st.markdown("---")

# ── Guard: need alerts ─────────────────────────────────────────────────────────
if "alerts" not in st.session_state or st.session_state.alerts.empty:
    st.info("🟢 No active alerts — the system is operating normally. Navigate to the main dashboard to start the stream.")
    st.stop()

df_alerts: pd.DataFrame = st.session_state.alerts.copy()

# Ensure required columns exist
for col, default in [("investigator", None), ("notes", ""), ("case_id", None),
                     ("status", "Pending"), ("risk_level", "MEDIUM")]:
    if col not in df_alerts.columns:
        df_alerts[col] = default

# ── KPI Row ────────────────────────────────────────────────────────────────────
pending   = len(df_alerts[df_alerts["status"] == "Pending"])
investing = len(df_alerts[df_alerts["status"] == "Investigating"])
resolved  = len(df_alerts[df_alerts["status"] == "Resolved"])
critical  = len(df_alerts[df_alerts["risk_level"] == "CRITICAL"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Pending Alerts",     pending,   delta=f"{critical} CRITICAL", delta_color="inverse")
k2.metric("Under Investigation", investing)
k3.metric("Resolved Today",      resolved)
k4.metric("Total Alerts",        len(df_alerts))

st.markdown("---")

# ── Filter Panel ───────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([2, 2, 2])
with fc1:
    status_filter = st.radio("Status", ["All", "Pending", "Investigating", "Resolved"], horizontal=True)
with fc2:
    risk_filter = st.multiselect("Risk Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                                  default=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
with fc3:
    sort_by = st.selectbox("Sort By", ["fraud_score ↓", "Amount ↓", "timestamp ↓"])

# Apply filters
filtered = df_alerts.copy()
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]
if risk_filter:
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]

sort_col = sort_by.split(" ")[0]
if sort_col in filtered.columns:
    filtered = filtered.sort_values(sort_col, ascending=False)

st.markdown(f"**{len(filtered)}** alerts matching filters")

# ── Alerts Table ───────────────────────────────────────────────────────────────
if not filtered.empty:
    display_cols = [c for c in ["timestamp", "txn_id", "card_id", "Amount",
                                "merchant_category", "fraud_score", "risk_level",
                                "status", "investigator"] if c in filtered.columns]
    disp = filtered[display_cols].copy()

    def _risk_style(val):
        return {"CRITICAL": "color:#ff4d6d;font-weight:700",
                "HIGH":     "color:#ff8844;font-weight:700",
                "MEDIUM":   "color:#ffdd57;font-weight:600",
                "LOW":      "color:#44ff88"}.get(val, "")

    fmt = {}
    if "fraud_score" in disp.columns: fmt["fraud_score"] = "{:.4f}"
    if "Amount"      in disp.columns: fmt["Amount"]      = "${:.2f}"

    styled = disp.style.format(fmt)
    if "risk_level" in disp.columns:
        styled = styled.map(_risk_style, subset=["risk_level"])

    st.dataframe(styled, use_container_width=True, height=280)
else:
    st.warning("No alerts match the current filters.")

st.markdown("---")

# ── Action Panel ───────────────────────────────────────────────────────────────
st.subheader("⚡ Take Action")
act1, act2 = st.columns([3, 2])

with act1:
    st.markdown("**Update Alert**")
    if not filtered.empty:
        txn_ids = filtered["txn_id"].tolist()
        selected_txn = st.selectbox("Select Transaction", txn_ids)

        col_a, col_b = st.columns(2)
        with col_a:
            new_status = st.selectbox("New Status", ["Investigating", "Resolved (True Fraud)", "Resolved (False Positive)"])
        with col_b:
            investigator = st.selectbox("Assign Investigator", ["(Unassigned)"] + INVESTIGATORS)

        notes_input = st.text_area("Add Notes / Comments", placeholder="Enter investigation notes...", height=80)

        if st.button("✅ Update Alert", use_container_width=True):
            mask = st.session_state.alerts["txn_id"] == selected_txn
            clean_status = "Resolved" if "Resolved" in new_status else new_status
            st.session_state.alerts.loc[mask, "status"] = clean_status
            if investigator != "(Unassigned)":
                st.session_state.alerts.loc[mask, "investigator"] = investigator
            if notes_input.strip():
                st.session_state.alerts.loc[mask, "notes"] = notes_input.strip()

            # Log to audit trail
            audit_entry = {
                "Timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User":       investigator if investigator != "(Unassigned)" else "SYSTEM",
                "Action":     f"Alert updated → {new_status}",
                "Target":     selected_txn,
            }
            if "audit_log" not in st.session_state:
                st.session_state.audit_log = []
            st.session_state.audit_log.insert(0, audit_entry)

            st.success(f"✅ {selected_txn} updated to **{new_status}**")
            st.rerun()
    else:
        st.info("No alerts to act on with current filters.")

with act2:
    st.markdown("**Open Investigation Case**")
    if not filtered.empty:
        case_txn = st.selectbox("Transaction for Case", filtered["txn_id"].tolist(), key="case_txn")
        case_desc = st.text_area("Case Description", placeholder="Describe the suspected fraud pattern...", height=80)
        case_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])

        if st.button("📁 Create Case", use_container_width=True):
            if case_desc.strip():
                import uuid
                case_id = f"CASE-{str(uuid.uuid4())[:6].upper()}"
                new_case = {
                    "case_id":     case_id,
                    "txn_id":      case_txn,
                    "description": case_desc.strip(),
                    "priority":    case_priority,
                    "status":      "Open",
                    "assigned_to": None,
                    "notes":       [],
                    "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                # Link case to alert
                mask = st.session_state.alerts["txn_id"] == case_txn
                st.session_state.alerts.loc[mask, "case_id"] = case_id

                # Add to cases list
                if "cases" not in st.session_state or st.session_state.cases.empty:
                    st.session_state.cases = pd.DataFrame([new_case])
                else:
                    st.session_state.cases = pd.concat(
                        [pd.DataFrame([new_case]), st.session_state.cases]
                    ).reset_index(drop=True)

                st.success(f"📁 Case **{case_id}** created for {case_txn}")
            else:
                st.error("Please enter a case description.")

# ── Alert Detail Expander ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔎 Alert Detail")
if not filtered.empty:
    detail_txn = st.selectbox("View Detail for Transaction", filtered["txn_id"].tolist(), key="detail_sel")
    row = filtered[filtered["txn_id"] == detail_txn].iloc[0]

    d1, d2, d3 = st.columns(3)
    d1.markdown(f"**Card:** `{row.get('card_id','N/A')}`")
    d1.markdown(f"**Amount:** `${row.get('Amount', 0):.2f}`")
    d2.markdown(f"**Fraud Score:** `{row.get('fraud_score', 0):.4f}`")
    d2.markdown(f"**Risk Level:** `{row.get('risk_level','N/A')}`")
    d3.markdown(f"**Status:** `{row.get('status','N/A')}`")
    d3.markdown(f"**Investigator:** `{row.get('investigator') or 'Unassigned'}`")

    if row.get("notes"):
        st.info(f"**Notes:** {row['notes']}")
