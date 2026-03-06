import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import polyline
import pydeck as pdk

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

df["date"] = pd.to_datetime(df["start_date"])
df["km"] = df["distance"] / 1000
df["hours"] = df["moving_time"] / 3600
df["year"] = df["date"].dt.year

df["week"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="d")
df["week"] = df["week"].dt.normalize()

# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters")

sports = sorted(df["type"].unique())

selected_sports = st.sidebar.multiselect(
    "Sport",
    options=sports,
    default=sports
)

# Quick time filter
time_mode = st.sidebar.radio(
    "Time range",
    ["All time","Last 6 weeks","Last 3 months","YTD"]
)

if time_mode == "Last 6 weeks":
    cutoff = pd.Timestamp.today() - pd.DateOffset(weeks=6)
    df = df[df["date"] >= cutoff]

elif time_mode == "Last 3 months":
    cutoff = pd.Timestamp.today() - pd.DateOffset(months=3)
    df = df[df["date"] >= cutoff]

elif time_mode == "YTD":
    year_start = pd.Timestamp.today().replace(month=1,day=1)
    df = df[df["date"] >= year_start]

df = df[df["type"].isin(selected_sports)]

# -------------------------
# KPI metrics
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
        name="4w avg"
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
# Heatmap of routes
# -------------------------

st.subheader("Training Heatmap")

points = []

for r in df["raw_json"].dropna():

    activity = json.loads(r)

    if "map" in activity and activity["map"]:

        poly = activity["map"].get("summary_polyline")

        if poly:

            coords = polyline.decode(poly)

            for lat,lon in coords:

                points.append([lon,lat])

if points:

    heat_df = pd.DataFrame(points,columns=["lon","lat"])

    layer = pdk.Layer(
        "HeatmapLayer",
        heat_df,
        get_position=["lon","lat"],
        radiusPixels=40
    )

    view = pdk.ViewState(
        latitude=heat_df["lat"].mean(),
        longitude=heat_df["lon"].mean(),
        zoom=6
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view
    ))

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
