import json
import pandas as pd
import requests
from json import JSONDecoder
import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
# -----------------------------
# Leer JSON robustamente
# -----------------------------

with open("data/strava_full_history.json") as f:
    text = f.read()

decoder = JSONDecoder()
idx = 0
items = []

while idx < len(text):
    slice_text = text[idx:].lstrip()
    if not slice_text:
        break
    try:
        obj, end = decoder.raw_decode(slice_text)
        if isinstance(obj, list):
            items.extend(obj)
        else:
            items.append(obj)
        idx += len(text[idx:]) - len(slice_text) + end
    except:
        idx += 1

df = pd.DataFrame(items)

# -----------------------------
# Preparar datos
# -----------------------------

df["date"] = pd.to_datetime(df["start_date"])
df["week"] = df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

df["hours"] = df["moving_time"] / 3600
df["km"] = df["distance"] / 1000

# -----------------------------
# Semana actual y anterior
# -----------------------------

today = pd.Timestamp.today()

current_week = today.to_period("W-MON").start_time
previous_week = current_week - pd.Timedelta(days=7)

current = df[df["week"] == current_week]
previous = df[df["week"] == previous_week]

# -----------------------------
# Métricas semana actual
# -----------------------------

run_km = current[current["type"] == "Run"]["km"].sum()

bike_km = current[current["type"].str.contains("Ride", na=False)]["km"].sum()

swim_m = current[current["type"] == "Swim"]["distance"].sum()

hours = current["hours"].sum()

sessions = len(current)

long_run = current[current["type"] == "Run"]["km"].max()

long_ride = current[current["type"].str.contains("Ride", na=False)]["km"].max()

# -----------------------------
# Semana anterior
# -----------------------------

prev_hours = previous["hours"].sum()

delta_hours = hours - prev_hours

# -----------------------------
# Formatear mensaje
# -----------------------------

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

# -----------------------------
# Enviar Telegram
# -----------------------------

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})
