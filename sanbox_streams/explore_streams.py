import os
import requests
import pandas as pd
import datetime as dt

BASE_URL = "https://www.strava.com/api/v3"

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")


# ---------------------------
# Obtener access token
# ---------------------------

def get_access_token():

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

    if "access_token" not in tokens:
        raise Exception(f"Token error: {tokens}")

    return tokens["access_token"]


# ---------------------------
# Descargar actividades
# ---------------------------

def get_activities(headers):

    r = requests.get(
        f"{BASE_URL}/athlete/activities",
        headers=headers,
        params={"per_page": 30}
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()


# ---------------------------
# Filtrar últimos 14 días
# ---------------------------

def filter_last_14_days(activities):

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)

    filtered = []

    for act in activities:

        start = dt.datetime.fromisoformat(
            act["start_date"].replace("Z","+00:00")
        )

        if start >= cutoff:
            filtered.append(act)

    return filtered


# ---------------------------
# Obtener streams
# ---------------------------

def get_streams(activity_id, headers):

    stream_keys = [
        "time",
        "distance",
        "latlng",
        "velocity_smooth",
        "heartrate",
        "cadence",
        "watts",
        "grade_smooth",
        "altitude"
    ]

    r = requests.get(
        f"{BASE_URL}/activities/{activity_id}/streams",
        headers=headers,
        params={
            "keys": ",".join(stream_keys),
            "key_by_type": "true"
        }
    )

    if r.status_code != 200:
        print("Error streams:", r.text)
        return None

    return r.json()


# ---------------------------
# Convertir streams a dataframe
# ---------------------------

def streams_to_dataframe(streams):

    data = {}

    for key in streams:

        data[key] = streams[key]["data"]

    df = pd.DataFrame(data)

    # métricas derivadas

    if "velocity_smooth" in df:
        df["pace_min_km"] = (1000 / df["velocity_smooth"]) / 60

    if "distance" in df:
        df["km"] = (df["distance"] // 1000) + 1

    return df


# ---------------------------
# MAIN
# ---------------------------

def main():

    print("Refreshing token...")

    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print("Descargando actividades...")

    activities = get_activities(headers)

    print("Actividades descargadas:", len(activities))

    recent = filter_last_14_days(activities)

    print("Actividades últimos 14 días:", len(recent))

    for act in recent:

        print("\n----------------------------------")
        print("Actividad:", act["name"])
        print("Tipo:", act["type"])
        print("Distancia:", round(act["distance"]/1000,2),"km")

        streams = get_streams(act["id"], headers)

        if not streams:
            continue

        print("Streams disponibles:", list(streams.keys()))

        df = streams_to_dataframe(streams)

        print("Puntos registrados:", len(df))

        print(df.head())

        # guardar CSV para análisis

        filename = f"streams_{act['id']}.csv"

        df.to_csv(filename, index=False)

        print("Guardado:", filename)


if __name__ == "__main__":
    main()
