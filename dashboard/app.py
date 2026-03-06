import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Strava Training Dashboard", layout="wide")

st.title("🏃 Strava Training Dashboard")

# -------------------------
# Load data
# -------------------------

@st.cache_data
def load_data():

    conn = sqlite3.connect("data/activities.db")
    df = pd.read_sql_query("SELECT * FROM activities", conn)
    conn.close()

    return df

df = load_data()

# -------------------------
# Feature engineering
# -------------------------

df["date"] = pd.to_datetime(df["start_date"], utc=True).dt.tz_localize(None)

# filtramos histórico antiguo
df = df[df["date"] >= "2022-01-01"]

df["km"] = df["distance"] / 1000
df["hours"] = df["moving_time"] / 3600

df["year"] = df["date"].dt.year

df["week"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="d")
df["week"] = df["week"].dt.normalize()

# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters")

sports = sorted(df["type"].dropna().unique())

selected_sports = st.sidebar.multiselect(
    "Sport",
    options=sports,
    default=sports
)

time_mode = st.sidebar.radio(
    "Time range",
    [
        "All time",
        "Last 6 weeks",
        "Last 3 months",
        "YTD",
        "2YTD",
        "4YTD"
    ]
)

today = pd.Timestamp.today()

if time_mode == "Last 6 weeks":

    cutoff = today - pd.DateOffset(weeks=6)

elif time_mode == "Last 3 months":

    cutoff = today - pd.DateOffset(months=3)

elif time_mode == "YTD":

    cutoff = pd.Timestamp(year=today.year, month=1, day=1)

elif time_mode == "2YTD":

    cutoff = pd.Timestamp(year=today.year-2, month=1, day=1)

elif time_mode == "4YTD":

    cutoff = pd.Timestamp(year=today.year-4, month=1, day=1)

else:

    cutoff = df["date"].min()

df = df[df["date"] >= cutoff]

df = df[df["type"].isin(selected_sports)]

# -------------------------
# KPIs
# -------------------------

total_km = df["km"].sum()
total_hours = df["hours"].sum()
sessions = len(df)

col1,col2,col3 = st.columns(3)

col1.metric("Total Distance (km)",f"{total_km:,.0f}")
col2.metric("Total Hours",f"{total_hours:,.0f}")
col3.metric("Sessions",f"{sessions:,}")

st.divider()

# -------------------------
# Weekly training load
# -------------------------

weekly = df.groupby("week").agg({
    "hours":"sum",
    "km":"sum"
}).reset_index()

weekly = weekly.sort_values("week")

weekly["rolling"] = weekly["hours"].rolling(4).mean()

target = st.sidebar.slider(
    "Weekly target hours",
    min_value=2,
    max_value=20,
    value=8
)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=weekly["week"],
        y=weekly["hours"],
        marker_color=[
            "#ef4444" if h < target else "#3b82f6"
            for h in weekly["hours"]
        ],
        name="Weekly hours"
    )
)

fig.add_trace(
    go.Scatter(
        x=weekly["week"],
        y=weekly["rolling"],
        mode="lines",
        line=dict(width=3),
        name="4 week avg"
    )
)

fig.add_hline(
    y=target,
    line_dash="dash",
    line_color="green",
    annotation_text="target"
)

fig.update_layout(
    title="Weekly Training Load",
    xaxis_title="Week",
    yaxis_title="Hours",
    height=450
)

st.plotly_chart(fig,use_container_width=True)

# -------------------------
# Distance by sport
# -------------------------

sport_dist = df.groupby("type")["km"].sum().reset_index()

sport_dist = sport_dist.sort_values("km",ascending=False)

fig2 = px.pie(
    sport_dist,
    names="type",
    values="km",
    title="Distance by Sport"
)

st.plotly_chart(fig2,use_container_width=True)

# -------------------------
# Activity table
# -------------------------

st.subheader("Activities")

table = df[[
    "date",
    "name",
    "type",
    "km",
    "hours"
]].sort_values("date",ascending=False)

table["km"] = table["km"].round(2)
table["hours"] = table["hours"].round(2)

st.dataframe(table,use_container_width=True)
