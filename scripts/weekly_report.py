import json
import pandas as pd
import requests

BOT_TOKEN="8467992856:AAExZnsZCLS9S5y-KktePsQD2KACXRsJfC0"
CHAT_ID="195248378"

# abrir archivo
with open("data/strava_full_history.json") as f:
    text = f.read()

# arreglar JSON concatenado
text = text.replace("][", ",")

data = json.loads(text)

df = pd.DataFrame(data)

df["date"]=pd.to_datetime(df["start_date"])
df["week"]=df["date"].dt.to_period("W-MON").apply(lambda r: r.start_time)

df["hours"]=df["moving_time"]/3600
df["km"]=df["distance"]/1000

week=df["week"].max()

current=df[df["week"]==week]

run=current[current["type"]=="Run"]["km"].sum()
bike=current[current["type"].str.contains("Ride",na=False)]["km"].sum()
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
