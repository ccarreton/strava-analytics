import json
import requests
import pandas as pd
import os

CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

# -----------------------------
# obtener access token nuevo
# -----------------------------

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

# -----------------------------
# leer dataset actual
# -----------------------------

with open("data/strava_full_history.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

last_date = pd.to_datetime(df["start_date"]).max()

timestamp = int(last_date.timestamp())

# -----------------------------
# descargar nuevas actividades
# -----------------------------

url = "https://www.strava.com/api/v3/athlete/activities"

headers = {
    "Authorization": f"Bearer {access_token}"
}

params = {
    "after": timestamp,
    "per_page": 200
}

new_activities = []

page = 1

while True:

    params["page"] = page

    r = requests.get(url, headers=headers, params=params)

    activities = r.json()

    if len(activities) == 0:
        break

    new_activities.extend(activities)

    page += 1

print("New activities:", len(new_activities))

# -----------------------------
# actualizar dataset
# -----------------------------

data.extend(new_activities)

with open("data/strava_full_history.json", "w") as f:
    json.dump(data, f)
