import sqlite3
import pandas as pd
import os
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

conn = sqlite3.connect("data/activities.db")

df = pd.read_sql_query("SELECT * FROM activities", conn)

conn.close()

df["date"] = pd.to_datetime(df["start_date"])
df["week"] = df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

df["hours"] = df["moving_time"] / 3600
df["km"] = df["distance"] / 1000

today = pd.Timestamp.today()

current_week = today.to_period("W-MON").start_time
previous_week = current_week - pd.Timedelta(days=7)

current = df[df["week"] == current_week]
previous = df[df["week"] == previous_week]

run_km = current[current["type"] == "Run"]["km"].sum()
bike_km = current[current["type"].str.contains("Ride", na=False)]["km"].sum()
swim_m = current[current["type"] == "Swim"]["distance"].sum()

hours = current["hours"].sum()
sessions = len(current)

long_run = current[current["type"] == "Run"]["km"].max()
long_ride = current[current["type"].str.contains("Ride", na=False)]["km"].max()

prev_hours = previous["hours"].sum()

delta_hours = hours - prev_hours

msg = f"""
📊 Weekly Training

⏱ Hours: {hours:.1f}
🏃 Run: {run_km:.1f} km
🚴 Bike: {bike_km:.1f} km
🏊 Swim: {swim_m:.0f} m
📈 Sessions: {sessions}

🔥 Long run: {long_run if pd.notna(long_run) else 0:.1f} km
🔥 Long ride: {long_ride if pd.notna(long_ride) else 0:.1f} km

📉 vs last week: {delta_hours:+.1f} h
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})
