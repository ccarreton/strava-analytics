import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Strava Analytics", layout="wide")

st.title("🏃 Strava Training Dashboard")

# -------------------------
# Load database
# -------------------------

conn = sqlite3.connect("data/activities.db")

df = pd.read_sql_query("SELECT * FROM activities", conn)

conn.close()

df["date"] = pd.to_datetime(df["start_date"])
df["km"] = df["distance"] / 1000
df["hours"] = df["moving_time"] / 3600

# -------------------------
# Sidebar filters
# -------------------------

sport = st.sidebar.multiselect(
    "Sport",
    options=df["type"].unique(),
    default=df["type"].unique()
)

df = df[df["type"].isin(sport)]

# -------------------------
# KPIs
# -------------------------

total_km = df["km"].sum()
total_hours = df["hours"].sum()
sessions = len(df)

col1, col2, col3 = st.columns(3)

col1.metric("Total Distance (km)", f"{total_km:.0f}")
col2.metric("Total Hours", f"{total_hours:.0f}")
col3.metric("Sessions", sessions)

st.divider()

# -------------------------
# Weekly training load
# -------------------------

df["week"] = df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

weekly = df.groupby("week").agg({
    "km": "sum",
    "hours": "sum"
}).reset_index()

fig = px.bar(
    weekly,
    x="week",
    y="hours",
    title="Weekly Training Hours"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Distance by sport
# -------------------------

sport_dist = df.groupby("type")["km"].sum().reset_index()

fig2 = px.pie(
    sport_dist,
    names="type",
    values="km",
    title="Distance by Sport"
)

st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# Activity table
# -------------------------

st.subheader("Activities")

st.dataframe(
    df[["date", "name", "type", "km", "hours"]]
    .sort_values("date", ascending=False)
)
