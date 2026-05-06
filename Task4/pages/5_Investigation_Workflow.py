# ============================================================
# Investigation Workflow — pages/5_Investigation_Workflow.py
# Case management: Open / In Progress / Closed
# Create cases, assign investigators, add notes, update status
# ============================================================

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

from backend.stream_simulator import INVESTIGATORS

st.set_page_config(page_title="Investigation | FraudShield", page_icon="🗂️", layout="wide")

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
h1 { color:#a78bfa !important; font-weight:700; }
h2,h3 { color:#c9d1e9 !important; }
.stButton>button {
    background:linear-gradient(135deg,#7c3aed,#a78bfa);
    color:white; border:none; border-radius:8px; font-weight:600;
}
.stButton>button:hover { opacity:0.88; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🗂️ Investigation Workflow & Case Management")
st.markdown("<p style='color:#7b8bad;margin-top:-10px;'>Manage fraud investigation cases from open to closure with full audit trail.</p>",
            unsafe_allow_html=True)
st.markdown("---")

# ── Session state init for cases ───────────────────────────────────────────────
if "cases" not in st.session_state or not isinstance(st.session_state.cases, pd.DataFrame):
    st.session_state.cases = pd.DataFrame()

# ── KPI Row ────────────────────────────────────────────────────────────────────
cases_df = st.session_state.cases

open_cases  = len(cases_df[cases_df["status"] == "Open"])          if not cases_df.empty else 0
inprog      = len(cases_df[cases_df["status"] == "In Progress"])   if not cases_df.empty else 0
closed      = len(cases_df[cases_df["status"] == "Closed"])        if not cases_df.empty else 0
total_cases = len(cases_df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Open Cases",        open_cases,  delta_color="inverse")
k2.metric("In Progress",       inprog)
k3.metric("Closed Cases",      closed)
k4.metric("Total Cases",       total_cases)

st.markdown("---")

# ── Create New Case ────────────────────────────────────────────────────────────
with st.expander("➕ Open New Investigation Case", expanded=(total_cases == 0)):
    c1, c2 = st.columns(2)
    with c1:
        # Populate txn choices from alerts
        df_alerts = st.session_state.get("alerts", pd.DataFrame())
        txn_opts = df_alerts["txn_id"].tolist() if not df_alerts.empty else []
        manual_txn = st.text_input("Transaction ID (manual entry)", placeholder="TXN_XXXXXX")
        if txn_opts:
            sel_txn = st.selectbox("Or select from active alerts", ["(Type above)"] + txn_opts)
        else:
            sel_txn = "(Type above)"

        final_txn = manual_txn.strip() if manual_txn.strip() else (sel_txn if sel_txn != "(Type above)" else "")

    with c2:
        case_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        assigned_inv  = st.selectbox("Assign Investigator", ["(Unassigned)"] + INVESTIGATORS)

    case_desc = st.text_area("Case Description *", placeholder="Describe the suspected fraud behaviour, pattern, or reason for investigation...", height=100)

    if st.button("📁 Open Case", use_container_width=True):
        if not final_txn:
            st.error("Please enter or select a Transaction ID.")
        elif len(case_desc.strip()) < 10:
            st.error("Description must be at least 10 characters.")
        else:
            new_case = pd.DataFrame([{
                "case_id":     f"CASE-{str(uuid.uuid4())[:6].upper()}",
                "txn_id":      final_txn,
                "description": case_desc.strip(),
                "priority":    case_priority,
                "assigned_to": assigned_inv if assigned_inv != "(Unassigned)" else None,
                "status":      "Open",
                "notes":       "",
                "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }])
            st.session_state.cases = pd.concat([new_case, st.session_state.cases]).reset_index(drop=True)

            # Log to audit
            if "audit_log" not in st.session_state:
                st.session_state.audit_log = []
            st.session_state.audit_log.insert(0, {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User":      assigned_inv if assigned_inv != "(Unassigned)" else "SYSTEM",
                "Action":    "Investigation case opened",
                "Target":    final_txn,
            })
            st.success(f"✅ Case opened for {final_txn}")
            st.rerun()

st.markdown("---")

# ── Case Board ─────────────────────────────────────────────────────────────────
st.subheader("📋 Case Board")

if cases_df.empty:
    st.info("No investigation cases yet. Create one above, or use the Alert Management page to create cases from active alerts.")
else:
    # Filter tabs
    tab_open, tab_prog, tab_closed, tab_all = st.tabs(["🟠 Open", "🔵 In Progress", "🟢 Closed", "📂 All"])

    def _render_cases(df_subset: pd.DataFrame):
        if df_subset.empty:
            st.info("No cases in this category.")
            return

        show_cols = [c for c in ["case_id","txn_id","priority","assigned_to","status","created_at","updated_at"] if c in df_subset.columns]
        disp = df_subset[show_cols].copy()

        def _pri_color(val):
            return {"Critical":"color:#ff4d6d;font-weight:700",
                    "High":    "color:#ff8844;font-weight:700",
                    "Medium":  "color:#ffdd57;font-weight:600",
                    "Low":     "color:#44ff88"}.get(val, "")

        styled = disp.style
        if "priority" in disp.columns:
            styled = styled.map(_pri_color, subset=["priority"])
        st.dataframe(styled, use_container_width=True, height=260)

    with tab_open:   _render_cases(cases_df[cases_df["status"] == "Open"])
    with tab_prog:   _render_cases(cases_df[cases_df["status"] == "In Progress"])
    with tab_closed: _render_cases(cases_df[cases_df["status"] == "Closed"])
    with tab_all:    _render_cases(cases_df)

    st.markdown("---")

    # ── Update Panel ───────────────────────────────────────────────────────────
    st.subheader("⚙️ Update Case")
    uc1, uc2 = st.columns([3, 2])

    with uc1:
        selected_case = st.selectbox("Select Case ID", cases_df["case_id"].tolist())
        if selected_case:
            case_row = cases_df[cases_df["case_id"] == selected_case].iloc[0]
            st.markdown(f"""
            **TXN:** `{case_row.get('txn_id','N/A')}` &nbsp;|&nbsp;
            **Priority:** `{case_row.get('priority','N/A')}` &nbsp;|&nbsp;
            **Status:** `{case_row.get('status','N/A')}` &nbsp;|&nbsp;
            **Assigned:** `{case_row.get('assigned_to') or 'Unassigned'}`
            """)

            ua, ub = st.columns(2)
            with ua:
                new_status = st.selectbox("Update Status", ["Open","In Progress","Closed"])
            with ub:
                new_inv = st.selectbox("Reassign To", ["(No change)"] + INVESTIGATORS)

            new_notes = st.text_area("Add Note / Comment", placeholder="Investigation findings, evidence, next steps...", height=90)

            if st.button("✅ Update Case", use_container_width=True):
                idx = st.session_state.cases.index[st.session_state.cases["case_id"] == selected_case][0]
                st.session_state.cases.at[idx, "status"]     = new_status
                st.session_state.cases.at[idx, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if new_inv != "(No change)":
                    st.session_state.cases.at[idx, "assigned_to"] = new_inv

                if new_notes.strip():
                    existing = st.session_state.cases.at[idx, "notes"] or ""
                    timestamp_note = f"\n[{datetime.now().strftime('%H:%M')}] {new_notes.strip()}"
                    st.session_state.cases.at[idx, "notes"] = existing + timestamp_note

                # Audit log
                if "audit_log" not in st.session_state:
                    st.session_state.audit_log = []
                st.session_state.audit_log.insert(0, {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "User":      new_inv if new_inv != "(No change)" else "Analyst",
                    "Action":    f"Case status → {new_status}",
                    "Target":    selected_case,
                })
                st.success(f"✅ Case {selected_case} updated to **{new_status}**")
                st.rerun()

    with uc2:
        if selected_case:
            case_row = cases_df[cases_df["case_id"] == selected_case].iloc[0]
            st.markdown("**Case Notes History**")
            notes = case_row.get("notes","")
            if notes:
                st.markdown(f"""
                <div style='background:#0d1117;border:1px solid #1e2433;border-radius:8px;
                            padding:14px;font-size:0.84rem;color:#c9d1e9;white-space:pre-wrap;
                            max-height:200px;overflow-y:auto;'>
                {notes}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No notes yet.")

    st.markdown("---")

    # ── Workload Distribution ──────────────────────────────────────────────────
    st.subheader("👥 Investigator Workload")
    if "assigned_to" in cases_df.columns:
        workload = (
            cases_df.groupby("assigned_to")["case_id"]
            .count().reset_index()
            .rename(columns={"case_id":"Cases Assigned","assigned_to":"Investigator"})
            .sort_values("Cases Assigned", ascending=False)
        )
        if not workload.empty:
            import plotly.express as px
            fig_wl = px.bar(workload, x="Investigator", y="Cases Assigned",
                            color="Cases Assigned",
                            color_continuous_scale=["#1e2433","#a78bfa","#7c3aed"],
                            text="Cases Assigned")
            fig_wl.update_traces(textposition="outside")
            fig_wl.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                                 font_color="#c9d1e9", height=280, coloraxis_showscale=False,
                                 margin=dict(t=20,b=20),
                                 xaxis=dict(gridcolor="#1e2433"),
                                 yaxis=dict(gridcolor="#1e2433"))
            st.plotly_chart(fig_wl, use_container_width=True)
