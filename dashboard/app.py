import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

from data import load_data
from filters import apply_filters
from charts import weekly_chart
from config import ROLLING_WINDOW, CTL_WINDOW, ATL_WINDOW


# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(
    page_title="Strava Training Dashboard",
    layout="centered"
)

st.set_option("client.showErrorDetails", True)

st.markdown("""
<style>
.block-container {
    padding-top:1rem;
    padding-bottom:1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🏃 Strava Training Dashboard")


# -------------------------
# LOAD DATA
# -------------------------

df = load_data()

if df.empty:
    st.warning("No activities available in database.")
    st.stop()


# -------------------------
# APPLY FILTERS
# -------------------------

df = apply_filters(df)

if df.empty:
    st.warning("No activities match selected filters.")
    st.stop()


# -------------------------
# PARSE RAW JSON
# -------------------------

if "raw_json" in df.columns:

    parsed = df["raw_json"].apply(
        lambda x: json.loads(x) if pd.notnull(x) else {}
    )

    df["max_watts"] = parsed.apply(lambda x: x.get("max_watts"))
    df["average_watts"] = parsed.apply(lambda x: x.get("average_watts"))

    df["max_heartrate"] = parsed.apply(lambda x: x.get("max_heartrate"))
    df["average_heartrate"] = parsed.apply(lambda x: x.get("average_heartrate"))


st.caption(f"{len(df)} activities loaded")


# -------------------------
# WEEKLY AGGREGATION
# -------------------------

weekly = (
    df.groupby("week", as_index=False)["hours"]
    .sum()
    .sort_values("week")
)

if weekly.empty:
    st.warning("No weekly data available.")
    st.stop()


weekly["rolling"] = weekly["hours"].rolling(
    ROLLING_WINDOW,
    min_periods=1
).mean()


# -------------------------
# FITNESS MODEL
# -------------------------

weekly["fitness"] = weekly["hours"].ewm(
    span=CTL_WINDOW,
    adjust=False
).mean()

weekly["fatigue"] = weekly["hours"].ewm(
    span=ATL_WINDOW,
    adjust=False
).mean()

weekly["form"] = weekly["fitness"] - weekly["fatigue"]


# -------------------------
# KPIs
# -------------------------

latest = weekly.iloc[-1]

current_week = latest["hours"]
rolling = latest["rolling"]

ctl = latest["fitness"]
atl = latest["fatigue"]

c1, c2 = st.columns(2)

with c1:
    st.metric("This week", f"{current_week:.1f} h")
    st.metric("Fitness (CTL)", f"{ctl:.0f}")

with c2:
    st.metric("4 week avg", f"{rolling:.1f} h")
    st.metric("Fatigue (ATL)", f"{atl:.0f}")


# -------------------------
# WEEKLY LOAD CHART
# -------------------------

st.subheader("Weekly Training Load")

fig = weekly_chart(weekly)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)


# -------------------------
# FITNESS MODEL CHART
# -------------------------

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
        line=dict(width=2, dash="dot")
    )
)

fig2.update_layout(
    height=300,
    margin=dict(l=5, r=5, t=30, b=5),
    legend=dict(
        orientation="h",
        y=1.02,
        x=0.5,
        xanchor="center"
    )
)

st.plotly_chart(
    fig2,
    use_container_width=True,
    config={"displayModeBar": False}
)


# -------------------------
# WEEKLY INSIGHT
# -------------------------

st.subheader("💡 Weekly Insight")

sessions_week = df[df["week"] == latest["week"]].shape[0]

load_diff = (
    (current_week - rolling) / rolling * 100
) if rolling > 0 else 0

trend = "increasing 📈" if weekly["fitness"].iloc[-1] > weekly["fitness"].iloc[-2] else "stable"

st.markdown(f"""
**Training load:** {current_week:.1f} hours  
**vs 4-week average:** {load_diff:+.0f}%  
**Sessions this week:** {sessions_week}  
**Fitness trend:** {trend}
""")


# -------------------------
# RUNNING PRs
# -------------------------

st.subheader("🏃 Running PRs")

runs = df[df["type"] == "Run"].copy()

if not runs.empty:

    runs["pace_sec_km"] = runs["moving_time"] / (runs["distance"] / 1000)

    def best(distance_km):

        target = distance_km * 1000
        subset = runs[runs["distance"] >= target]

        if subset.empty:
            return None

        best = subset.sort_values("pace_sec_km").iloc[0]

        pace = best["pace_sec_km"]

        minutes = int(pace // 60)
        seconds = int(pace % 60)

        return {
            "Distance": f"{distance_km} km",
            "Best pace": f"{minutes}:{seconds:02d}/km",
            "Date": best["date"].date(),
            "Location": best["location"]
        }

    prs = [best(d) for d in [1,5,10,21]]
    prs = [p for p in prs if p]

    if prs:
        st.dataframe(pd.DataFrame(prs), use_container_width=True)


# -------------------------
# CYCLING POWER RECORDS
# -------------------------

st.subheader("⚡ Cycling Power Records")

bike = df[df["type"] == "Ride"].copy()

records = []

if "max_watts" in bike.columns and bike["max_watts"].notna().any():

    row = bike.loc[bike["max_watts"].idxmax()]

    records.append({
        "Metric": "Max Power",
        "Value": f"{int(row['max_watts'])} W",
        "Date": row["date"].date(),
        "Location": row["location"]
    })

if "average_watts" in bike.columns and bike["average_watts"].notna().any():

    row = bike.loc[bike["average_watts"].idxmax()]

    records.append({
        "Metric": "Best Avg Power",
        "Value": f"{int(row['average_watts'])} W",
        "Date": row["date"].date(),
        "Location": row["location"]
    })

if records:
    st.dataframe(pd.DataFrame(records), use_container_width=True)


# -------------------------
# HEART RATE RECORDS
# -------------------------

st.subheader("❤️ Heart Rate Records")

hr = df.copy()

records = []

if "max_heartrate" in hr.columns and hr["max_heartrate"].notna().any():

    row = hr.loc[hr["max_heartrate"].idxmax()]

    records.append({
        "Metric": "Max Heart Rate",
        "Value": f"{int(row['max_heartrate'])} bpm",
        "Date": row["date"].date(),
        "Location": row["location"]
    })

if "average_heartrate" in hr.columns and hr["average_heartrate"].notna().any():

    row = hr.loc[hr["average_heartrate"].idxmax()]

    records.append({
        "Metric": "Highest Avg HR",
        "Value": f"{int(row['average_heartrate'])} bpm",
        "Date": row["date"].date(),
        "Location": row["location"]
    })

if records:
    st.dataframe(pd.DataFrame(records), use_container_width=True)
