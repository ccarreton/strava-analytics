import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# módulos
data = load_module("data_local", DASHBOARD_DIR / "data.py")
charts = load_module("charts_local", DASHBOARD_DIR / "charts.py")
filters = load_module("filters_local", DASHBOARD_DIR / "filters.py")
training_status = load_module("training_status_local", DASHBOARD_DIR / "training_status.py")
config = load_module("config_local", DASHBOARD_DIR / "config.py")
performance_patterns = load_module("pp_local", DASHBOARD_DIR / "performance_patterns.py")
performance_timeline = load_module("pt_local", DASHBOARD_DIR / "performance_timeline.py")

# imports
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# funciones
load_data = data.load_data
load_performance_patterns = performance_patterns.load_patterns
weekly_chart = charts.weekly_chart
plot_performance_patterns = charts.plot_performance_patterns
apply_filters = filters.apply_filters
training_status_gauge = training_status.training_status_gauge

compute_pb_timeline = performance_timeline.compute_pb_timeline
summarize_training_factors = performance_timeline.summarize_training_factors

ROLLING_WINDOW = config.ROLLING_WINDOW
CTL_WINDOW = config.CTL_WINDOW
ATL_WINDOW = config.ATL_WINDOW


# ---------------- UI ----------------

st.set_page_config(page_title="Strava Training Dashboard", layout="wide")
st.title("🏃 Strava Training Dashboard")

df = load_data()
df = apply_filters(df)

patterns = load_performance_patterns()

if df.empty:
    st.warning("No activities match filters.")
    st.stop()

# ---------------- METRICS ----------------

weekly = df.groupby("week", as_index=False)["hours"].sum()

weekly["rolling"] = weekly["hours"].rolling(ROLLING_WINDOW, min_periods=1).mean()
weekly["fitness"] = weekly["hours"].ewm(span=CTL_WINDOW, adjust=False).mean()
weekly["fatigue"] = weekly["hours"].ewm(span=ATL_WINDOW, adjust=False).mean()
weekly["form"] = weekly["fitness"] - weekly["fatigue"]

latest = weekly.iloc[-1]

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("This week", f"{latest['hours']:.1f} h")
c2.metric("4 week avg", f"{latest['rolling']:.1f} h")
c3.metric("Fitness (CTL)", f"{latest['fitness']:.0f}")
c4.metric("Fatigue (ATL)", f"{latest['fatigue']:.0f}")
c5.metric("Best week", f"{weekly['hours'].max():.1f} h")


# ---------------- ACHIEVEMENTS ----------------

achievements = {}
runs = df[df["type"] == "Run"].copy()

if not runs.empty:
    runs["pace"] = runs["moving_time"] / (runs["distance"] / 1000)

    for d in [1, 5, 10, 21]:
        subset = runs[runs["distance"] >= d * 1000]
        if not subset.empty:
            row = subset.sort_values("pace").iloc[0]
            achievements.setdefault(row["week"], []).append("run")

if df["max_watts"].notna().any():
    row = df.loc[df["max_watts"].idxmax()]
    achievements.setdefault(row["week"], []).append("power")

if df["max_hr"].notna().any():
    row = df.loc[df["max_hr"].idxmax()]
    achievements.setdefault(row["week"], []).append("hr")


# ---------------- LAYOUT ----------------

main, side = st.columns([3, 1])

with main:

    # Weekly load
    st.subheader("Weekly Training Load")
    fig = weekly_chart(weekly, achievements)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Fitness model
    st.subheader("Fitness / Fatigue Model")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["fitness"], name="Fitness"))
    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["fatigue"], name="Fatigue"))
    fig2.add_trace(go.Scatter(x=weekly["week"], y=weekly["form"], name="Form", line=dict(dash="dot")))
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------- PB TABLE ----------------
    st.subheader("📊 PB Timeline (interpretable)")

    timeline_df = compute_pb_timeline()

    if not timeline_df.empty:

        display_df = timeline_df[[
    "distance",
    "rank",
    "date",
    "pace_str",
    "km_8w",
    "km_w1",
    "km_4w",
    "intensity",
    "cross_load"
]].rename(columns={
    "distance": "Distance",
    "rank": "Rank",
    "date": "Date",
    "pace_str": "Pace",
    "km_8w": "Km (8w)",
    "km_w1": "Km (week-1)",
    "km_4w": "Km (4w)",
    "intensity": "Intensity",
    "cross_load": "Total Load"
})

        st.dataframe(display_df, use_container_width=True, height=400)

        # ---------------- INSIGHT ----------------
        st.subheader("🧠 Training Pattern (PB averages)")
        summary = summarize_training_factors(timeline_df)
        st.dataframe(summary, use_container_width=True)

    else:
        st.warning("No PB timeline data found")

    # ---------------- OLD PATTERN ----------------
    st.subheader("🏁 Load Before PBs")

    if not patterns.empty:
        fig3 = plot_performance_patterns(patterns)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No performance patterns available yet.")


with side:

    st.markdown("### 💡 Weekly Insight")

    sessions = df[df["week"] == latest["week"]].shape[0]
    load_diff = (latest["hours"] - latest["rolling"]) / latest["rolling"] * 100
    trend = "improving" if weekly["fitness"].iloc[-1] > weekly["fitness"].iloc[-2] else "stable"

    st.write(f"Training load: **{latest['hours']:.1f} h**")
    st.write(f"vs average: **{load_diff:+.0f}%**")
    st.write(f"Sessions: **{sessions}**")
    st.write(f"Fitness trend: **{trend}**")

    st.plotly_chart(
        training_status_gauge(latest["form"]),
        use_container_width=True,
        config={"displayModeBar": False}
    )
