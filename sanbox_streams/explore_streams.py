import os
import requests

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# refresh token
r = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
)

tokens = r.json()
access_token = tokens["access_token"]

headers = {"Authorization": f"Bearer {access_token}"}

# descargar actividades
r = requests.get(
    "https://www.strava.com/api/v3/athlete/activities",
    headers=headers,
    params={"per_page": 5}
)

activities = r.json()

print("Actividades:", len(activities))

activity_id = activities[0]["id"]

# obtener streams
r = requests.get(
    f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
    headers=headers,
    params={
        "keys": "time,distance,velocity_smooth,heartrate",
        "key_by_type": "true"
    }
)

streams = r.json()

print("Streams disponibles:", streams.keys())
