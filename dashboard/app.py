import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Strava Training Dashboard",
    layout="centered"
)

# -----------------------------
# MOBILE CSS FIX
# -----------------------------

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
    padding-left: 0.6rem;
    padding-right: 0.6rem;
}

[data-testid="stPlotlyChart"] {
    width: 100%;
}

h2 {
    margin-top: 0.5rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------

@st.cache_data
def load_data():

    conn = sqlite3.connect("data/activities.db")

    df = pd.read_sql("""
        SELECT
        id,
        name,
        type,
        start_date,
        distance,
        moving_time,
        average_heartrate,
        max_heartrate,
        average_watts,
        max_watts,
        location_city,
        location_state,
        location_country
        FROM activities
    """, conn)

    conn.close()

    df["date"] = pd.to_datetime(df["start_date"])
    df["hours"] = df["moving_time"] / 3600
    df["km"] = df["distance"] / 1000

    df["year"] = df["date"].dt.year
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    df["location"] = (
        df["location_city"]
        .fillna(df["location_state"])
        .fillna(df["location_country"])
        .fillna(df["name"])
    )

    return df


df = load_data()

# -----------------------------
# FILTERS
# -----------------------------

with st.expander("Filters"):

    sports = st.multiselect(
        "Sport",
        df["type"].unique(),
        default=df["type"].unique()
    )

    time_range = st.radio(
        "Time range",
        ["All time", "YTD", "2YTD", "4YTD"]
    )

df = df[df["type"].isin(sports)]

now = pd.Timestamp.now()

if time_range == "YTD":
    df = df[df["date"] >= now - pd.DateOffset(months=12)]

elif time_range == "2YTD":
    df = df[df["date"] >= now - pd.DateOffset(years=2)]

elif time_range == "4YTD":
    df = df[df["date"] >= now - pd.DateOffset(years=4)]

# -----------------------------
# WEEKLY LOAD
# -----------------------------

weekly = df.groupby("week")["hours"].sum().reset_index()

weekly["rolling4"] = weekly["hours"].rolling(4).mean()

record_week = weekly.loc[weekly["hours"].idxmax()]

# -----------------------------
# FITNESS / FATIGUE MODEL
# -----------------------------

weekly["fitness"] = weekly["hours"].ewm(span=42).mean()
weekly["fatigue"] = weekly["hours"].ewm(span=7).mean()
weekly["form"] = weekly["fitness"] - weekly["fatigue"]

# -----------------------------
# KPIs
# -----------------------------

current_week = weekly.iloc[-1]["hours"]
rolling_4 = weekly.iloc[-1]["rolling4"]

ctl = weekly.iloc[-1]["fitness"]
atl = weekly.iloc[-1]["fatigue"]

c1, c2 = st.columns(2)

with c1:
    st.metric("This week", f"{current_week:.1f} h")
    st.metric("Fitness (CTL)", f"{ctl:.0f}")

with c2:
    st.metric("4 week avg", f"{rolling_4:.1f} h")
    st.metric("Fatigue (ATL)", f"{atl:.0f}")

# -----------------------------
# WEEKLY LOAD CHART
# -----------------------------

st.subheader("Weekly Training Load")

colors = np.where(weekly["hours"] < 7.5, "#ff4d4d", "#4A7DFF")

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=weekly["week"],
        y=weekly["hours"],
        name="Weekly hours",
        marker_color=colors
    )
)

fig.add_trace(
    go.Scatter(
        x=weekly["week"],
        y=weekly["rolling4"],
        name="4 week avg",
        line=dict(width=3)
    )
)

fig.add_hline(
    y=7.5,
    line_dash="dash",
    line_color="green",
    annotation_text="target"
)

fig.add_annotation(
    x=record_week["week"],
    y=record_week["hours"],
    text=f"⭐ {record_week['hours']:.1f}h record",
    showarrow=True
)

fig.update_layout(
    height=280,
    margin=dict(l=5, r=5, t=30, b=5),
    legend=dict(
        orientation="h",
        y=1.02,
        x=0.5,
        xanchor="center"
    ),
    xaxis_title="Week",
    yaxis_title="Hours"
)

fig.update_xaxes(nticks=6)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

# -----------------------------
# FITNESS FATIGUE CHART
# -----------------------------

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

fig2.update_layout(
    height=280,
    margin=dict(l=5, r=5, t=30, b=5),
    legend=dict(
        orientation="h",
        y=1.02,
        x=0.5,
        xanchor="center"
    )
)

fig2.update_xaxes(nticks=6)

st.plotly_chart(
    fig2,
    use_container_width=True,
    config={"displayModeBar": False}
)

# -----------------------------
# RUNNING PRS
# -----------------------------

run = df[df["type"].str.contains("Run", na=False)].copy()

run["pace"] = run["moving_time"] / run["distance"]

def pace_str(p):

    pace_sec = p * 1000
    m = int(pace_sec // 60)
    s = int(pace_sec % 60)

    return f"{m}:{s:02d} /km"


records = []

distances = {
    "1 km": 1,
    "5 km": 5,
    "10 km": 10,
    "21 km": 21
}

for label, dist in distances.items():

    subset = run[run["km"] >= dist]

    if len(subset) > 0:

        best = subset.loc[subset["pace"].idxmin()]

        records.append({
            "Distance": label,
            "Best pace": pace_str(best["pace"]),
            "Date": best["date"].date(),
            "Location": best["location"]
        })

running_pr = pd.DataFrame(records)

# -----------------------------
# POWER RECORDS
# -----------------------------

bike = df[df["type"].str.contains("Ride", na=False)]

power_records = pd.DataFrame([
    {
        "Metric": "Max Power",
        "Value": f"{bike['max_watts'].max():.0f} W",
        "Date": bike.loc[bike["max_watts"].idxmax()]["date"].date(),
        "Location": bike.loc[bike["max_watts"].idxmax()]["location"]
    },
    {
        "Metric": "Best Avg Power",
        "Value": f"{bike['average_watts'].max():.0f} W",
        "Date": bike.loc[bike["average_watts"].idxmax()]["date"].date(),
        "Location": bike.loc[bike["average_watts"].idxmax()]["location"]
    }
])

# -----------------------------
# HR RECORDS
# -----------------------------

hr_records = pd.DataFrame([
    {
        "Metric": "Max Heart Rate",
        "Value": f"{df['max_heartrate'].max():.0f} bpm",
        "Date": df.loc[df["max_heartrate"].idxmax()]["date"].date(),
        "Location": df.loc[df["max_heartrate"].idxmax()]["location"]
    },
    {
        "Metric": "Highest Avg Heart Rate",
        "Value": f"{df['average_heartrate'].max():.0f} bpm",
        "Date": df.loc[df["average_heartrate"].idxmax()]["date"].date(),
        "Location": df.loc[df["average_heartrate"].idxmax()]["location"]
    }
])

# -----------------------------
# RECORDS
# -----------------------------

st.subheader("Performance Records")

tab1, tab2, tab3 = st.tabs(["🏃 Running", "⚡ Power", "❤️ Heart Rate"])

with tab1:
    st.dataframe(running_pr, use_container_width=True)

with tab2:
    st.dataframe(power_records, use_container_width=True)

with tab3:
    st.dataframe(hr_records, use_container_width=True)
