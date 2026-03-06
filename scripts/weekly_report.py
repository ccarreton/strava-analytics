import pandas as pd
import requests

BOT_TOKEN="8467992856:AAExZnsZCLS9S5y-KktePsQD2KACXRsJfC0"
CHAT_ID="195248378"

df=pd.read_json("data/strava_full_history.json")

df["date"]=pd.to_datetime(df["start_date"])
df["week"]=df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

df["hours"]=df["moving_time"]/3600
df["km"]=df["distance"]/1000

week=df["week"].max()

current=df[df["week"]==week]

run=current[current["type"]=="Run"]["km"].sum()
bike=current[current["type"].str.contains("Ride")]["km"].sum()
swim=current[current["type"]=="Swim"]["km"].sum()

hours=current["hours"].sum()

msg=f"""
📊 Weekly Training

⏱ Hours: {hours:.1f}

🏃 Run: {run:.1f} km
🚴 Bike: {bike:.1f} km
🏊 Swim: {swim:.1f} km
"""

url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url,data={
"chat_id":CHAT_ID,
"text":msg
})
