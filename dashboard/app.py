import streamlit as st
import pandas as pd
from data import load_data
from filters import apply_filters
from charts import weekly_chart
from config import ROLLING_WINDOW, CTL_WINDOW, ATL_WINDOW

st.set_page_config(
    page_title="Armatostes Training Dashboard",
    layout="centered",
)

# CSS mobile

st.markdown("""
<style>
.block-container {
padding:1rem;
}
</style>
""", unsafe_allow_html=True)

# load

df = load_data()

if df.empty:
    st.warning("No activities in database")
    st.stop()

# filters

df = apply_filters(df)

if df.empty:
    st.warning("No activities match selected filters")
    st.stop()

st.caption(f"{len(df)} activities loaded")

# weekly aggregation

weekly = df.groupby("week", as_index=False)["hours"].sum()

weekly["rolling"] = weekly["hours"].rolling(ROLLING_WINDOW, min_periods=1).mean()

# fitness model

weekly["fitness"] = weekly["hours"].ewm(span=CTL_WINDOW).mean()
weekly["fatigue"] = weekly["hours"].ewm(span=ATL_WINDOW).mean()
weekly["form"] = weekly["fitness"] - weekly["fatigue"]

# KPIs

current_week = weekly.iloc[-1]["hours"]
rolling = weekly.iloc[-1]["rolling"]

ctl = weekly.iloc[-1]["fitness"]
atl = weekly.iloc[-1]["fatigue"]

c1, c2 = st.columns(2)

with c1:
    st.metric("This week", f"{current_week:.1f} h")
    st.metric("Fitness", f"{ctl:.0f}")

with c2:
    st.metric("4 week avg", f"{rolling:.1f} h")
    st.metric("Fatigue", f"{atl:.0f}")

# chart

st.subheader("Weekly Training Load")

fig = weekly_chart(weekly)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False},
)
