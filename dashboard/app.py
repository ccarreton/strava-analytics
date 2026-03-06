import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Strava Training Dashboard", layout="wide")

st.title("🏃 Strava Training Dashboard")

# -------------------------
# LOAD DATA
# -------------------------

@st.cache_data
def load_data():

    conn = sqlite3.connect("data/activities.db")
    df = pd.read_sql_query("SELECT * FROM activities", conn)
    conn.close()

    return df


df = load_data()

# -------------------------
# FEATURE ENGINEERING
# -------------------------

df["date"] = pd.to_datetime(df["start_date"], utc=True).dt.tz_localize(None)

# ignoramos histórico antiguo
df = df[df["date"] >= "2022-01-01"]

df["km"] = df["distance"] / 1000
df["hours"] = df["moving_time"] / 3600

df["week"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="d")
df["week"] = df["week"].dt.normalize()

# copia para cálculos históricos
df_original = df.copy()

# -------------------------
# SIDEBAR FILTERS
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
        "YTD (12M moving)",
        "2YTD",
        "4YTD"
    ]
)

today = pd.Timestamp.today()

if time_mode == "Last 6 weeks":

    cutoff = today - pd.DateOffset(weeks=6)

elif time_mode == "Last 3 months":

    cutoff = today - pd.DateOffset(months=3)

elif time_mode == "YTD (12M moving)":

    cutoff = today - pd.DateOffset(months=12)

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

col1, col2, col3 = st.columns(3)

col1.metric("Total Distance (km)", f"{total_km:,.0f}")
col2.metric("Total Hours", f"{total_hours:,.0f}")
col3.metric("Sessions", f"{sessions:,}")

st.divider()

# -------------------------
# WEEKLY AGGREGATION
# -------------------------

weekly_full = df_original.groupby("week").agg({
    "hours":"sum",
    "km":"sum"
}).reset_index()

weekly_full = weekly_full.sort_values("week")

# rolling promedio
weekly_full["rolling"] = weekly_full["hours"].rolling(4).mean()

# FITNESS / FATIGUE MODEL
weekly_full["ATL"] = weekly_full["hours"].ewm(span=7, adjust=False).mean()
weekly_full["CTL"] = weekly_full["hours"].ewm(span=42, adjust=False).mean()

weekly_full["TSB"] = weekly_full["CTL"] - weekly_full["ATL"]

# aplicar filtro
weekly = weekly_full[weekly_full["week"] >= cutoff]

# -------------------------
# RECORD WEEK
# -------------------------

record_hours = weekly["hours"].max()

# -------------------------
# TARGET
# -------------------------

target = st.sidebar.slider(
    "Weekly target hours",
    min_value=2,
    max_value=20,
    value=8
)

# -------------------------
# WEEKLY LOAD CHART
# -------------------------

colors = []

for h in weekly["hours"]:

    if h == record_hours:
        colors.append("#f59e0b")

    elif h < target:
        colors.append("#ef4444")

    else:
        colors.append("#3b82f6")

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=weekly["week"],
        y=weekly["hours"],
        marker_color=colors,
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

record_row = weekly.loc[weekly["hours"].idxmax()]

fig.add_annotation(
    x=record_row["week"],
    y=record_row["hours"],
    text=f"⭐ {record_row['hours']:.1f}h record",
    showarrow=True
)

fig.update_layout(
    title="Weekly Training Load",
    xaxis_title="Week",
    yaxis_title="Hours",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# FITNESS / FATIGUE CHART
# -------------------------

st.subheader("Fitness / Fatigue Model")

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=weekly["week"],
        y=weekly["CTL"],
        name="Fitness (CTL)",
        line=dict(width=3)
    )
)

fig2.add_trace(
    go.Scatter(
        x=weekly["week"],
        y=weekly["ATL"],
        name="Fatigue (ATL)",
        line=dict(width=3)
    )
)

fig2.add_trace(
    go.Scatter(
        x=weekly["week"],
        y=weekly["TSB"],
        name="Form (TSB)",
        line=dict(width=2, dash="dot")
    )
)

fig2.update_layout(
    height=400,
    xaxis_title="Week",
    yaxis_title="Load"
)

st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# DISTANCE BY SPORT
# -------------------------

sport_dist = df.groupby("type")["km"].sum().reset_index()

sport_dist = sport_dist.sort_values("km", ascending=False)

fig3 = px.pie(
    sport_dist,
    names="type",
    values="km",
    title="Distance by Sport"
)

st.plotly_chart(fig3, use_container_width=True)

# -------------------------
# ACTIVITY TABLE
# -------------------------

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
# =========================================================
# PERFORMANCE MODULE (final clean version)
# =========================================================

import json

st.divider()
st.header("🏆 Performance Records")

@st.cache_data
def extract_metrics(df_in):

    rows = []

    for _, r in df_in.iterrows():

        raw = r.get("raw_json")

        if not raw:
            continue

        try:

            j = json.loads(raw)

            place = j.get("location_city")

            # fallback si Strava no devuelve ciudad
            if not place:
                place = r.get("name")

            rows.append({
                "date": r["date"],
                "place": place,
                "type": r["type"],
                "distance": j.get("distance"),
                "moving_time": j.get("moving_time"),
                "avg_hr": j.get("average_heartrate"),
                "max_hr": j.get("max_heartrate"),
                "avg_watts": j.get("average_watts"),
                "max_watts": j.get("max_watts")
            })

        except:
            continue

    dfm = pd.DataFrame(rows)

    if len(dfm):

        dfm["km"] = dfm["distance"] / 1000
        dfm["pace"] = dfm["moving_time"] / dfm["km"]

    return dfm


metrics = extract_metrics(df)

# =========================================================
# RUNNING PRs
# =========================================================

st.subheader("🏃 Running PRs")

run_types = ["Run", "TrailRun"]

runs = metrics[metrics["type"].isin(run_types)]

records = []

targets = {
    "1 km": (0.9,1.2),
    "5 km": (4.8,5.3),
    "10 km": (9.5,10.5),
    "21 km": (20,22)
}

for label,(low,high) in targets.items():

    subset = runs[(runs["km"] > low) & (runs["km"] < high)]

    if len(subset)==0:
        continue

    best = subset.loc[subset["pace"].idxmin()]

    pace = best["pace"]

    pace_str = f"{int(pace//60)}:{int(pace%60):02d} /km"

    records.append({
        "Distance":label,
        "Best pace":pace_str,
        "Date":best["date"].date(),
        "Location":best["place"]
    })

records_df = pd.DataFrame(records)

if len(records_df):

    st.dataframe(records_df, use_container_width=True)

else:

    st.info("No running PRs found.")

# =========================================================
# CYCLING POWER
# =========================================================

st.subheader("⚡ Cycling Power Records")

bike_types = ["Ride","VirtualRide"]

power = metrics[metrics["type"].isin(bike_types)]

power = power.dropna(subset=["avg_watts","max_watts"])

if len(power):

    best_max = power.loc[power["max_watts"].idxmax()]
    best_avg = power.loc[power["avg_watts"].idxmax()]

    power_table = pd.DataFrame([
        {
            "Metric":"Max Power",
            "Value":f"{int(best_max['max_watts'])} W",
            "Date":best_max["date"].date(),
            "Location":best_max["place"]
        },
        {
            "Metric":"Best Avg Power",
            "Value":f"{int(best_avg['avg_watts'])} W",
            "Date":best_avg["date"].date(),
            "Location":best_avg["place"]
        }
    ])

    st.dataframe(power_table, use_container_width=True)

else:

    st.info("No cycling power data available.")

# =========================================================
# HEART RATE
# =========================================================

st.subheader("❤️ Heart Rate Records")

hr = metrics.dropna(subset=["avg_hr","max_hr"])

# filtro fisiológico básico
hr = hr[(hr["max_hr"] < 210) & (hr["max_hr"] > 40)]

if len(hr):

    best_max = hr.loc[hr["max_hr"].idxmax()]
    best_avg = hr.loc[hr["avg_hr"].idxmax()]

    hr_table = pd.DataFrame([
        {
            "Metric":"Max Heart Rate",
            "Value":f"{int(best_max['max_hr'])} bpm",
            "Date":best_max["date"].date(),
            "Location":best_max["place"]
        },
        {
            "Metric":"Highest Avg Heart Rate",
            "Value":f"{int(best_avg['avg_hr'])} bpm",
            "Date":best_avg["date"].date(),
            "Location":best_avg["place"]
        }
    ])

    st.dataframe(hr_table, use_container_width=True)

else:

    st.info("No heart rate data available.")
