import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Strava Training Dashboard", layout="wide")

st.title("🏃 Método ArmaTOSTE Dashboard")

# -----------------------------
# Load database
# -----------------------------

conn = sqlite3.connect("data/activities.db")
df = pd.read_sql_query("SELECT * FROM activities", conn)
conn.close()

# -----------------------------
# Feature engineering
# -----------------------------

df["date"] = pd.to_datetime(df["start_date"])
df["km"] = df["distance"] / 1000
df["hours"] = df["moving_time"] / 3600
df["year"] = df["date"].dt.year

# Monday based week
df["week"] = df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------

st.sidebar.header("Filters")

# Sport filter
sports = sorted(df["type"].unique())

selected_sports = st.sidebar.multiselect(
    "Sport",
    options=sports,
    default=sports
)

# Year filter
years = sorted(df["year"].unique())

selected_years = st.sidebar.multiselect(
    "Year",
    options=years,
    default=years
)

# Quick selector
if st.sidebar.button("Last 12 months"):
    last_year = df["year"].max()
    selected_years = [last_year]

# Apply filters
df = df[
    (df["type"].isin(selected_sports)) &
    (df["year"].isin(selected_years))
]

# -----------------------------
# KPIs
# -----------------------------

total_km = df["km"].sum()
total_hours = df["hours"].sum()
sessions = len(df)

col1, col2, col3 = st.columns(3)

col1.metric("Total Distance (km)", f"{total_km:,.0f}")
col2.metric("Total Hours", f"{total_hours:,.0f}")
col3.metric("Sessions", f"{sessions:,}")

st.divider()

# -----------------------------
# WEEKLY TRAINING LOAD
# -----------------------------

weekly = df.groupby("week").agg({
    "hours": "sum",
    "km": "sum"
}).reset_index()

weekly = weekly.sort_values("week")

# color condition
weekly["color"] = weekly["hours"].apply(
    lambda x: "Low load" if x < 7.5 else "Normal load"
)

fig = px.bar(
    weekly,
    x="week",
    y="hours",
    color="color",
    color_discrete_map={
        "Normal load": "#3b82f6",
        "Low load": "#ef4444"
    },
    title="Weekly Training Hours"
)

fig.update_layout(
    xaxis_title="Week",
    yaxis_title="Training Hours",
    legend_title=""
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# DISTANCE BY SPORT
# -----------------------------

sport_dist = df.groupby("type")["km"].sum().reset_index()

fig2 = px.pie(
    sport_dist,
    names="type",
    values="km",
    title="Distance by Sport"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# ACTIVITY TABLE
# -----------------------------

st.subheader("Activities")

table = df[[
    "date",
    "name",
    "type",
    "km",
    "hours"
]].sort_values("date", ascending=False)

table["km"] = table["km"].round(2)
table["hours"] = table["hours"].round(2)

st.dataframe(table, use_container_width=True)
