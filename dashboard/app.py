import streamlit as st
import pandas as pd

from data import load_data
from filters import apply_filters
from charts import weekly_chart
from config import ROLLING_WINDOW, CTL_WINDOW, ATL_WINDOW


st.set_page_config(
    page_title="Strava Training Dashboard",
    layout="centered"
)

# mobile padding
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

st.caption(f"{len(df)} activities loaded")

# -------------------------
# WEEKLY AGGREGATION
# -------------------------

weekly = df.groupby("week", as_index=False)["hours"].sum()

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

current_week = weekly.iloc[-1]["hours"]
rolling = weekly.iloc[-1]["rolling"]

ctl = weekly.iloc[-1]["fitness"]
atl = weekly.iloc[-1]["fatigue"]

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

import plotly.graph_objects as go

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
        line=dict(
            width=2,
            dash="dot"
        )
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
