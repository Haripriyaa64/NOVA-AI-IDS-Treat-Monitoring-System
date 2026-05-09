import sqlite3
import time
import pandas as pd
import streamlit as st
import plotly.express as px

DB_PATH = "nova.db"   # change this if your db name is different

st.set_page_config(
    page_title="IDS Admin Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# ---------- Enhanced Cybersecurity-Themed CSS ----------
st.markdown("""
<style>
:root{
  --bg-1: #020617;
  --bg-2: #07111f;
  --card-glow: rgba(58,134,255,0.12);
  --accent-1: #3b82f6;
  --accent-2: #06b6d4;
  --muted: #94a3b8;
  --glass: rgba(255,255,255,0.04);
  --glass-2: rgba(255,255,255,0.02);
  --danger: #ef4444;
  --warn: #f59e0b;
  --safe: #22c55e;
}

/* animated background */
.stApp {
    background: radial-gradient(1200px 600px at 10% 10%, rgba(6,95,255,0.06), transparent 8%),
                radial-gradient(900px 500px at 90% 90%, rgba(3,193,197,0.04), transparent 8%),
                linear-gradient(135deg, var(--bg-1), var(--bg-2));
    color: #e6eef7;
    min-height: 100vh;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    padding: 18px;
}

/* Page level main card */
.main-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 6px 30px rgba(2,6,23,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    backdrop-filter: blur(6px) saturate(120%);
}

/* Metric cards */
.metric-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(4,12,35,0.55);
    text-align: left;
    transition: transform .18s ease, box-shadow .18s ease;
    border-left: 3px solid rgba(255,255,255,0.03);
    color: #e6eef7;
}
.metric-card:hover{
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(4,12,35,0.7);
}

/* Small icon circle */
.metric-icon {
    display:inline-flex;
    width:48px;
    height:48px;
    border-radius:12px;
    align-items:center;
    justify-content:center;
    margin-right:12px;
    background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(6,182,212,0.06));
    border: 1px solid rgba(255,255,255,0.03);
}

/* Metric text */
.metric-title {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 6px;
    font-weight: 600;
    letter-spacing: 0.4px;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #fff;
}

/* Alert badges and cards */
.alert-high {
    background: linear-gradient(90deg, rgba(239,68,68,0.08), rgba(239,68,68,0.03));
    border-left: 4px solid var(--danger);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    color: #ffecec;
    transition: transform .12s ease;
}
.alert-medium {
    background: linear-gradient(90deg, rgba(245,158,11,0.08), rgba(245,158,11,0.03));
    border-left: 4px solid var(--warn);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    color: #fff7ed;
}
.alert-low {
    background: linear-gradient(90deg, rgba(34,197,94,0.06), rgba(34,197,94,0.02));
    border-left: 4px solid var(--safe);
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    color: #f0fff4;
}

/* Card headings */
.stsubheader, h1 {
    color: #e6eef7;
}

/* Pretty titles inside cards */
.card-title {
    display:flex;
    align-items:center;
    gap:10px;
    font-size:16px;
    font-weight:700;
    color:#e6eef7;
    margin-bottom:10px;
}

/* Dataframe styling hint (Streamlit controlled) */
.stDataFrame table {
    border-radius: 8px;
    overflow: hidden;
}

/* Plotly dark mode override for hover */
[data-testid="stPlotlyChart"] .plotly {
    border-radius: 12px;
}

/* Suspicious IP table look */
.ip-table {
    border-radius: 10px;
    padding: 10px;
    background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.03);
}

/* Sidebar improvements */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.01));
    padding: 18px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.02);
}

/* small badges for risk level labels used inline */
.badge {
    display:inline-block;
    padding: 4px 8px;
    font-size:12px;
    border-radius:999px;
    font-weight:700;
    color:#041022;
}
.badge-high { background: linear-gradient(90deg, #ff7a7a, #ff4949); color: white; }
.badge-med  { background: linear-gradient(90deg, #ffcc80, #f59e0b); color:#081018; }
.badge-low  { background: linear-gradient(90deg, #99f6c4, #34d399); color:#042018; }

/* tighten spacing for sections */
section.main > div[role="list"] { gap: 10px; }

/* small responsive tweaks */
@media (max-width: 800px) {
  .metric-value { font-size: 22px; }
  .metric-icon { width:40px; height:40px; }
}
</style>
""", unsafe_allow_html=True)


# ---------- Load Data ----------
def load_table(table):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


try:
    alerts_df = load_table("alerts")
    logs_df = load_table("login_logs")
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()


# ---------- Sidebar ----------
st.sidebar.title("🛡️ IDS Controls")

auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_sec = st.sidebar.slider("Refresh Every", 5, 60, 10)

risk_options = alerts_df["risk_level"].unique().tolist() if not alerts_df.empty else []
attack_options = alerts_df["attack_type"].unique().tolist() if not alerts_df.empty else []

risk_filter = st.sidebar.multiselect("Risk Level", risk_options, default=risk_options)
attack_filter = st.sidebar.multiselect("Attack Type", attack_options, default=attack_options)

filtered_alerts = alerts_df.copy()

if not filtered_alerts.empty:
    filtered_alerts = filtered_alerts[
        filtered_alerts["risk_level"].isin(risk_filter) &
        filtered_alerts["attack_type"].isin(attack_filter)
    ]


# ---------- Header ----------
st.markdown("""
<div class="main-card">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div>
      <h1 style="margin:0; font-size:26px;">🛡️ Intelligent IDS Admin Monitoring Dashboard</h1>
      <div style="color: #9fb0c8; margin-top:6px;">Real-time monitoring for rule-based and signature-based intrusion detection.</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:12px; color: #9fb0c8;">Status</div>
      <div style="margin-top:6px;">
        <span class="badge badge-high">Live</span>
        <span style="margin-left:8px; color:var(--muted); font-size:12px;">Updated: just now</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")


# ---------- Metrics ----------
total_alerts = len(alerts_df)
high_alerts = len(alerts_df[alerts_df["risk_level"] == "HIGH"]) if not alerts_df.empty else 0
medium_alerts = len(alerts_df[alerts_df["risk_level"] == "MEDIUM"]) if not alerts_df.empty else 0
failed_logins = len(logs_df[logs_df["login_status"] == "FAILED"]) if not logs_df.empty else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; align-items:center;">
            <div class="metric-icon">🛰️</div>
            <div>
                <div class="metric-title">Total Alerts</div>
                <div class="metric-value">{total_alerts}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; align-items:center;">
            <div class="metric-icon">🔥</div>
            <div>
                <div class="metric-title">High Risk</div>
                <div class="metric-value">{high_alerts}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; align-items:center;">
            <div class="metric-icon">⚠️</div>
            <div>
                <div class="metric-title">Medium Risk</div>
                <div class="metric-value">{medium_alerts}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; align-items:center;">
            <div class="metric-icon">🔐</div>
            <div>
                <div class="metric-title">Failed Logins</div>
                <div class="metric-value">{failed_logins}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")


# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📊 Attack Type Distribution</div>', unsafe_allow_html=True)

    if not alerts_df.empty:
        attack_counts = alerts_df["attack_type"].value_counts().reset_index()
        attack_counts.columns = ["Attack Type", "Count"]

        fig = px.bar(
            attack_counts,
            x="Attack Type",
            y="Count",
            text="Count",
            title="Detected Attack Types"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            margin=dict(l=0,r=0,t=30,b=0)
        )
        fig.update_traces(marker_color='rgba(59,130,246,0.9)', marker_line_color='rgba(255,255,255,0.03)', marker_line_width=1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No attack data available.")

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">⚠️ Risk Level Summary</div>', unsafe_allow_html=True)

    if not alerts_df.empty:
        risk_counts = alerts_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]

        fig = px.pie(
            risk_counts,
            names="Risk Level",
            values="Count",
            hole=0.45,
            title="Risk Distribution"
        )
        fig.update_traces(marker=dict(colors=['#ff6b6b','#ffb86b','#6ee7b7']))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            margin=dict(l=0,r=0,t=30,b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No risk data available.")

    st.markdown('</div>', unsafe_allow_html=True)


# ---------- Login Activity ----------
st.write("")
st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.subheader("🔐 Login Activity")

if not logs_df.empty:
    login_counts = logs_df["login_status"].value_counts().reset_index()
    login_counts.columns = ["Login Status", "Count"]

    fig = px.bar(
        login_counts,
        x="Login Status",
        y="Count",
        text="Count",
        title="Success vs Failed Login Attempts"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        margin=dict(l=0,r=0,t=30,b=0)
    )
    # color mapping: success -> teal, failed -> red (fallback if two categories)
    colors = ['#06b6d4', '#ff6b6b'] if len(login_counts) == 2 else ['#06b6d4']
    fig.update_traces(marker_color=colors)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No login logs available.")

st.markdown('</div>', unsafe_allow_html=True)


# ---------- Recent Alerts ----------
st.write("")
st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.subheader("🚨 Recent Security Alerts")

if not filtered_alerts.empty:
    # try converting created_at to datetime for proper sorting if possible
    recent_alerts = filtered_alerts.copy()
    if "created_at" in recent_alerts.columns:
        try:
            recent_alerts["created_at_parsed"] = pd.to_datetime(recent_alerts["created_at"])
            recent_alerts = recent_alerts.sort_values(by="created_at_parsed", ascending=False)
        except Exception:
            recent_alerts = recent_alerts.sort_values(by="created_at", ascending=False)
    else:
        recent_alerts = recent_alerts.head(10)

    recent_alerts = recent_alerts.head(10)

    for _, row in recent_alerts.iterrows():
        risk = row.get("risk_level", "")

        css_class = "alert-low"
        badge = '<span class="badge badge-low">LOW</span>'
        if str(risk).upper() == "HIGH":
            css_class = "alert-high"
            badge = '<span class="badge badge-high">HIGH</span>'
        elif str(risk).upper() == "MEDIUM":
            css_class = "alert-medium"
            badge = '<span class="badge badge-med">MED</span>'

        attack_type = row.get('attack_type', 'Unknown')
        message = row.get('message', '')
        email = row.get('email', 'N/A')
        source_ip = row.get('source_ip', 'N/A')
        created_at = row.get('created_at', '')

        st.markdown(f"""
        <div class="{css_class}">
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div><b style="font-size:15px;">{attack_type}</b> — <small style="color:var(--muted);">{message}</small></div>
              <div style="text-align:right;">{badge}<div style="font-size:11px; color:var(--muted); margin-top:6px;">{created_at}</div></div>
            </div>
            <div style="margin-top:6px;">
              <small style="color:var(--muted);">Email: {email} | Source IP: {source_ip}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No alerts found.")

st.markdown('</div>', unsafe_allow_html=True)


# ---------- Suspicious IP Table ----------
st.write("")
st.markdown('<div class="main-card ip-table">', unsafe_allow_html=True)
st.subheader("🌐 Suspicious IP Ranking")

if not alerts_df.empty:
    ip_df = alerts_df["source_ip"].value_counts().reset_index()
    ip_df.columns = ["Source IP", "Alert Count"]
    st.dataframe(ip_df, use_container_width=True)
else:
    st.info("No suspicious IPs found.")

st.markdown('</div>', unsafe_allow_html=True)


# ---------- Auto Refresh ----------
if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
