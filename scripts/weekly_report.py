import sqlite3
import pandas as pd
import os
import requests

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
    # DATE (CLAVE: timezone correcto)
    # -------------------------

    df["date"] = pd.to_datetime(
        df["start_date"],
        utc=True
    ).dt.tz_convert("Europe/Madrid").dt.tz_localize(None)

    # -------------------------
    # WEEK (lunes → domingo)
    # -------------------------

    df["week"] = df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

    # -------------------------
    # METRICS BASE
    # -------------------------

    df["hours"] = df["moving_time"] / 3600
    df["km"] = df["distance"] / 1000

    # -------------------------
    # SPORT GROUPS (IMPORTANTE)
    # -------------------------

    RUN_TYPES = ["Run", "TrailRun"]
    RIDE_TYPES = ["Ride", "VirtualRide"]
    SWIM_TYPES = ["Swim"]
    GYM_TYPES = ["WeightTraining", "Workout"]

    # -------------------------
    # CURRENT WEEK
    # -------------------------

    now = pd.Timestamp.now(tz="Europe/Madrid").tz_localize(None)

    current_week = now.to_period("W-MON").start_time
    previous_week = current_week - pd.Timedelta(days=7)

    current = df[df["week"] == current_week]
    previous = df[df["week"] == previous_week]

    # -------------------------
    # CALCULATIONS
    # -------------------------

    # Distancias
    run_km = current[current["type"].isin(RUN_TYPES)]["km"].sum()
    bike_km = current[current["type"].isin(RIDE_TYPES)]["km"].sum()
    swim_m = current[current["type"].isin(SWIM_TYPES)]["distance"].sum()

    # Horas
    run_hours = current[current["type"].isin(RUN_TYPES)]["hours"].sum()
    bike_hours = current[current["type"].isin(RIDE_TYPES)]["hours"].sum()
    gym_hours = current[current["type"].isin(GYM_TYPES)]["hours"].sum()

    total_hours = current["hours"].sum()
    sessions = len(current)

    # Long sessions
    long_run = current[current["type"].isin(RUN_TYPES)]["km"].max()
    long_ride = current[current["type"].isin(RIDE_TYPES)]["km"].max()

    long_run = 0 if pd.isna(long_run) else long_run
    long_ride = 0 if pd.isna(long_ride) else long_ride

    # Comparativa semana anterior
    prev_hours = previous["hours"].sum()
    delta_hours = total_hours - prev_hours

    # -------------------------
    # MENSAJE
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
