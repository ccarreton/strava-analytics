import requests
import sqlite3
import os
import json
from datetime import datetime

CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

# Obtener access token nuevo

auth_url = "https://www.strava.com/oauth/token"

payload = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "grant_type": "refresh_token"
}

res = requests.post(auth_url, data=payload)
tokens = res.json()

access_token = tokens["access_token"]

print("Access token obtained")

# Conectar base de datos

conn = sqlite3.connect("data/activities.db")
cursor = conn.cursor()

cursor.execute("SELECT MAX(start_date) FROM activities")
row = cursor.fetchone()

timestamp = 0

if row and row[0]:
    last_date = row[0]
    timestamp = int(datetime.fromisoformat(last_date.replace("Z","")).timestamp())

print("Timestamp used:", timestamp)

# Llamar API Strava

url = "https://www.strava.com/api/v3/athlete/activities"

headers = {
    "Authorization": f"Bearer {access_token}"
}

params = {
    "after": timestamp,
    "per_page": 200
}

page = 1
new_count = 0

while True:

    params["page"] = page

    r = requests.get(url, headers=headers, params=params)
    activities = r.json()

    if not activities:
        break

    print("Fetched activities:", len(activities))

    for a in activities:

        cursor.execute("""
        INSERT OR IGNORE INTO activities
        (id,start_date,type,name,distance,moving_time,total_elevation_gain,raw_json)
        VALUES (?,?,?,?,?,?,?,?)
        """,(
            a["id"],
            a["start_date"],
            a["type"],
            a["name"],
            a["distance"],
            a["moving_time"],
            a.get("total_elevation_gain",0),
            json.dumps(a)
        ))

        new_count += 1

    page += 1

conn.commit()
conn.close()

print("New activities inserted:", new_count)
