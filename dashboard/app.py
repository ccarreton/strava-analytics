import sys
import os
import streamlit as st
import pandas as pd

from dashboard.data import load_data, load_performance_patterns
from dashboard.charts import weekly_chart, plot_performance_patterns
from dashboard.filters import apply_filters
from dashboard.training_status import training_status_gauge
from dashboard.config import ROLLING_WINDOW, CTL_WINDOW, ATL_WINDOW


st.set_page_config(
    page_title="Strava Training Dashboard",
    layout="wide"
)

st.title("🏃 Strava Training Dashboard")

df = load_data()
df = apply_filters(df)

# 🔹 NUEVO: cargar patrones
patterns = load_performance_patterns()

if df.empty:
    st.warning("No activities match filters.")
    st.stop()

weekly = df.groupby("week", as_index=False)["hours"].sum()

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

best_week = weekly["hours"].max()

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("This week", f"{current_week:.1f} h")
c2.metric("4 week avg", f"{rolling:.1f} h")
c3.metric("Fitness (CTL)", f"{ctl:.0f}")
c4.metric("Fatigue (ATL)", f"{atl:.0f}")
c5.metric("Best week", f"{best_week:.1f} h")

show_records = st.toggle("🏅 Show performance records")

achievements = {}

runs = df[df["type"] == "Run"].copy()

if not runs.empty:

    runs["pace"] = runs["moving_time"]/(runs["distance"]/1000)

    for d in [1,5,10,21]:

        subset = runs[runs["distance"] >= d*1000]

        if subset.empty:
            continue

        row = subset.sort_values("pace").iloc[0]

        achievements.setdefault(row["week"], []).append("run")

if df["max_watts"].notna().any():

    row = df.loc[df["max_watts"].idxmax()]

    achievements.setdefault(row["week"], []).append("power")

if df["max_hr"].notna().any():

    row = df.loc[df["max_hr"].idxmax()]

    achievements.setdefault(row["week"], []).append("hr")

main, side = st.columns([3,1])

with main:

    st.subheader("Weekly Training Load")

    fig = weekly_chart(weekly, achievements)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.subheader("Fitness / Fatigue Model")

    import plotly.graph_objects as go

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["fitness"], name="Fitness"))
    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["fatigue"], name="Fatigue"))
    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["form"], name="Form", line=dict(dash="dot")))

    fig2.update_layout(height=300)

    st.plotly_chart(fig2, use_container_width=True)

    # 🔹 NUEVO BLOQUE: patrones pre-PB
    st.subheader("🏁 Load Before PBs")

    if not patterns.empty:

        fig3 = plot_performance_patterns(patterns)

        st.plotly_chart(
            fig3,
            use_container_width=True,
            config={"displayModeBar": False}
        )

    else:
        st.info("No performance patterns available yet.")

with side:

    st.markdown("### 💡 Weekly Insight")

    sessions = df[df["week"] == latest["week"]].shape[0]

    load_diff = (current_week - rolling)/rolling*100

    trend = "improving" if weekly["fitness"].iloc[-1] > weekly["fitness"].iloc[-2] else "stable"

    st.write(f"Training load: **{current_week:.1f} h**")
    st.write(f"vs average: **{load_diff:+.0f}%**")
    st.write(f"Sessions: **{sessions}**")
    st.write(f"Fitness trend: **{trend}**")

    tsb = latest["form"]

    st.plotly_chart(
        training_status_gauge(tsb),
        use_container_width=True,
        config={"displayModeBar": False}
    )
