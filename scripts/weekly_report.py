import sqlite3
import pandas as pd
import os
import requests
import json

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# -------------------------
# LOAD DATA
# -------------------------

conn = sqlite3.connect("data/activities.db")
df = pd.read_sql_query("SELECT * FROM activities", conn)
conn.close()

if df.empty:
    msg = "📊 Weekly Training\n\nNo data available."
else:

    # -------------------------
    # DATE (timezone correcto)
    # -------------------------

    df["date"] = pd.to_datetime(
        df["start_date"],
        utc=True
    ).dt.tz_convert("Europe/Madrid").dt.tz_localize(None)

    # -------------------------
    # EXTRACT ELAPSED TIME (CLAVE)
    # -------------------------

    def extract_elapsed(row):
        try:
            raw = json.loads(row["raw_json"]) if pd.notna(row["raw_json"]) else {}
            return raw.get("elapsed_time", row["moving_time"])
        except:
            return row["moving_time"]

    df["elapsed_time"] = df.apply(extract_elapsed, axis=1)

    # -------------------------
    # DURATION ROBUSTA
    # -------------------------

    df["duration"] = df.apply(
        lambda row: row["moving_time"]
        if row["moving_time"] > 0
        else row["elapsed_time"],
        axis=1
    )

    df["hours"] = df["duration"] / 3600
    df["km"] = df["distance"] / 1000

    # -------------------------
    # SPORT GROUPS
    # -------------------------

    RUN_TYPES = ["Run", "TrailRun"]
    RIDE_TYPES = ["Ride", "VirtualRide"]
    SWIM_TYPES = ["Swim"]
    GYM_TYPES = ["WeightTraining", "Workout"]

    # -------------------------
    # WEEK RANGE (NO usar df["week"])
    # -------------------------

    now = pd.Timestamp.now(tz="Europe/Madrid").tz_localize(None)

    start_week = now.to_period("W-MON").start_time
    end_week = start_week + pd.Timedelta(days=7)

    start_prev = start_week - pd.Timedelta(days=7)
    end_prev = start_week

    current = df[
        (df["date"] >= start_week) &
        (df["date"] < end_week)
    ]

    previous = df[
        (df["date"] >= start_prev) &
        (df["date"] < end_prev)
    ]

    # -------------------------
    # CALCULATIONS
    # -------------------------

    # Distancias
    run_km = current[current["type"].isin(RUN_TYPES)]["km"].sum()
    bike_km = current[current["type"].isin(RIDE_TYPES)]["km"].sum()
    swim_m = current[current["type"].isin(SWIM_TYPES)]["distance"].sum()

    # Horas por deporte
    run_hours = current[current["type"].isin(RUN_TYPES)]["hours"].sum()
    bike_hours = current[current["type"].isin(RIDE_TYPES)]["hours"].sum()
    gym_hours = current[current["type"].isin(GYM_TYPES)]["hours"].sum()

    # Totales
    total_hours = current["hours"].sum()
    sessions = len(current)

    # Long sessions
    long_run = current[current["type"].isin(RUN_TYPES)]["km"].max()
    long_ride = current[current["type"].isin(RIDE_TYPES)]["km"].max()

    long_run = 0 if pd.isna(long_run) else long_run
    long_ride = 0 if pd.isna(long_ride) else long_ride

    # Comparativa
    prev_hours = previous["hours"].sum()
    delta_hours = total_hours - prev_hours

    # -------------------------
    # MESSAGE
    # -------------------------

    if sessions == 0:

        msg = f"""
📊 Weekly Training

😴 No activities this week
"""

    else:

        msg = f"""
📊 Weekly Training

⏱ Hours: {total_hours:.1f}
   🏃 {run_hours:.1f}h | 🚴 {bike_hours:.1f}h | 🏋️ {gym_hours:.1f}h

🏃 Run: {run_km:.1f} km
🚴 Bike: {bike_km:.1f} km
🏊 Swim: {swim_m:.0f} m

📈 Sessions: {sessions}

🔥 Long run: {long_run:.1f} km
🔥 Long ride: {long_ride:.1f} km

📉 vs last week: {delta_hours:+.1f} h
"""

# -------------------------
# SEND TELEGRAM
# -------------------------

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})
