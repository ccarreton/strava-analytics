import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

from data import load_data
from filters import apply_filters
from charts import weekly_chart
from config import ROLLING_WINDOW, CTL_WINDOW, ATL_WINDOW


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Strava Training Dashboard",
    layout="wide"
)

# --------------------------------------------------
# STYLE (DARK SPORTS THEME)
# --------------------------------------------------

st.markdown("""
<style>

body {
    background-color: #0e1117;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* KPI CARDS */

.metric-card {
    background: #161b22;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}

.metric-title {
    font-size: 13px;
    color: #8b949e;
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
}

/* SIDEBAR CARDS */

.side-card {
    background: #161b22;
    padding: 18px;
    border-radius: 10px;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🏃 Strava Training Dashboard")


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = load_data()

if df.empty:
    st.warning("No activities available.")
    st.stop()

df = apply_filters(df)

if df.empty:
    st.warning("No activities match filters.")
    st.stop()


# --------------------------------------------------
# PARSE RAW JSON
# --------------------------------------------------

if "raw_json" in df.columns:

    def parse_raw(row):
        try:
            return json.loads(row)
        except:
            return {}

    parsed = df["raw_json"].apply(parse_raw)

    df["max_watts"] = parsed.apply(lambda x: x.get("max_watts"))
    df["avg_watts"] = parsed.apply(
        lambda x: x.get("average_watts") or x.get("weighted_average_watts")
    )

    df["max_hr"] = parsed.apply(lambda x: x.get("max_heartrate"))
    df["avg_hr"] = parsed.apply(lambda x: x.get("average_heartrate"))

else:

    df["max_watts"] = None
    df["avg_watts"] = None
    df["max_hr"] = None
    df["avg_hr"] = None


# --------------------------------------------------
# WEEKLY AGGREGATION
# --------------------------------------------------

weekly = (
    df.groupby("week", as_index=False)["hours"]
    .sum()
    .sort_values("week")
)

weekly["rolling"] = weekly["hours"].rolling(
    ROLLING_WINDOW,
    min_periods=1
).mean()

weekly["fitness"] = weekly["hours"].ewm(
    span=CTL_WINDOW,
    adjust=False
).mean()

weekly["fatigue"] = weekly["hours"].ewm(
    span=ATL_WINDOW,
    adjust=False
).mean()

weekly["form"] = weekly["fitness"] - weekly["fatigue"]


latest = weekly.iloc[-1]

current_week = latest["hours"]
rolling = latest["rolling"]
ctl = latest["fitness"]
atl = latest["fatigue"]


# --------------------------------------------------
# KPI ROW
# --------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"""
<div class="metric-card">
<div class="metric-title">THIS WEEK</div>
<div class="metric-value">{current_week:.1f} h</div>
</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="metric-card">
<div class="metric-title">4 WEEK AVG</div>
<div class="metric-value">{rolling:.1f} h</div>
</div>
""", unsafe_allow_html=True)

c3.markdown(f"""
<div class="metric-card">
<div class="metric-title">FITNESS (CTL)</div>
<div class="metric-value">{ctl:.0f}</div>
</div>
""", unsafe_allow_html=True)

c4.markdown(f"""
<div class="metric-card">
<div class="metric-title">FATIGUE (ATL)</div>
<div class="metric-value">{atl:.0f}</div>
</div>
""", unsafe_allow_html=True)


st.markdown("---")


# --------------------------------------------------
# LAYOUT
# --------------------------------------------------

main, side = st.columns([3,1])


# ==================================================
# MAIN AREA
# ==================================================

with main:

    st.subheader("Weekly Training Load")

    fig = weekly_chart(weekly)

    fig.update_layout(height=300)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )


    st.subheader("Fitness / Fatigue Model")

    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["fitness"],
            name="Fitness (CTL)",
            line=dict(width=3)
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["fatigue"],
            name="Fatigue (ATL)",
            line=dict(width=3)
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["form"],
            name="Form (TSB)",
            line=dict(dash="dot")
        )
    )

    fig2.update_layout(height=300)

    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ==================================================
# SIDEBAR ANALYTICS
# ==================================================

with side:

    st.markdown('<div class="side-card">', unsafe_allow_html=True)

    st.markdown("### 💡 Weekly Insight")

    sessions = df[df["week"] == latest["week"]].shape[0]

    load_diff = (current_week - rolling) / rolling * 100

    trend = "📈 improving" if weekly["fitness"].iloc[-1] > weekly["fitness"].iloc[-2] else "stable"

    st.write(f"Training load: **{current_week:.1f} h**")
    st.write(f"vs average: **{load_diff:+.0f}%**")
    st.write(f"Sessions: **{sessions}**")
    st.write(f"Fitness trend: **{trend}**")

    st.markdown("</div>", unsafe_allow_html=True)


    # --------------------------------------------------

    st.markdown('<div class="side-card">', unsafe_allow_html=True)

    st.markdown("### 🏃 Running PRs")

    runs = df[df["type"] == "Run"].copy()

    if not runs.empty:

        runs["pace"] = runs["moving_time"] / (runs["distance"]/1000)

        def best(d):

            subset = runs[runs["distance"] >= d*1000]

            if subset.empty:
                return None

            row = subset.sort_values("pace").iloc[0]

            p = row["pace"]

            return f"{int(p//60)}:{int(p%60):02d}/km"

        st.write(f"1 km — **{best(1)}**")
        st.write(f"5 km — **{best(5)}**")
        st.write(f"10 km — **{best(10)}**")
        st.write(f"21 km — **{best(21)}**")

    st.markdown("</div>", unsafe_allow_html=True)


    # --------------------------------------------------

    st.markdown('<div class="side-card">', unsafe_allow_html=True)

    st.markdown("### ⚡ Power Records")

    bike = df[df["type"] == "Ride"]

    if bike["max_watts"].notna().any():

        row = bike.loc[bike["max_watts"].idxmax()]

        st.write(f"Max power: **{int(row['max_watts'])} W**")

    if bike["avg_watts"].notna().any():

        row = bike.loc[bike["avg_watts"].idxmax()]

        st.write(f"Best avg: **{int(row['avg_watts'])} W**")

    st.markdown("</div>", unsafe_allow_html=True)


    # --------------------------------------------------

    st.markdown('<div class="side-card">', unsafe_allow_html=True)

    st.markdown("### ❤️ Heart Rate")

    if df["max_hr"].notna().any():

        row = df.loc[df["max_hr"].idxmax()]

        st.write(f"Max HR: **{int(row['max_hr'])} bpm**")

    if df["avg_hr"].notna().any():

        row = df.loc[df["avg_hr"].idxmax()]

        st.write(f"Best avg HR: **{int(row['avg_hr'])} bpm**")

    st.markdown("</div>", unsafe_allow_html=True)
