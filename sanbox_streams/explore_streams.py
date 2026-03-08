import os
import requests
import pandas as pd
import datetime as dt

BASE_URL = "https://www.strava.com/api/v3"

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

EFFORT_WINDOWS = [5,30,60,300,600,1200]


# --------------------------
# AUTH
# --------------------------

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
        raise Exception(tokens)

    return tokens["access_token"]


# --------------------------
# ACTIVITIES
# --------------------------

def get_activities(headers):

    r = requests.get(
        f"{BASE_URL}/athlete/activities",
        headers=headers,
        params={"per_page":30}
    )

    return r.json()


# --------------------------
# STREAMS
# --------------------------

def get_streams(activity_id, headers):

    keys = [
        "time",
        "distance",
        "velocity_smooth",
        "heartrate",
        "cadence",
        "watts"
    ]

    r = requests.get(
        f"{BASE_URL}/activities/{activity_id}/streams",
        headers=headers,
        params={
            "keys":",".join(keys),
            "key_by_type":"true"
        }
    )

    if r.status_code != 200:
        return None

    return r.json()


# --------------------------
# DATAFRAME
# --------------------------

def streams_to_dataframe(streams):

    data = {}

    for k in streams:
        data[k] = streams[k]["data"]

    df = pd.DataFrame(data)

    if "velocity_smooth" in df:
        df["speed_kmh"] = df["velocity_smooth"] * 3.6
        df["pace_min_km"] = (1000/df["velocity_smooth"])/60

    return df


# --------------------------
# BEST EFFORTS
# --------------------------

def best_efforts(series, durations):

    series = series.replace([float("inf")],None).dropna()

    results = {}

    for d in durations:

        if len(series) < d:
            continue

        rolling = series.rolling(d).mean()

        best = rolling.max()

        results[d] = best

    return results


def format_pace(value):

    if value is None:
        return None

    minutes = int(value)
    seconds = int((value-minutes)*60)

    return f"{minutes}:{seconds:02d}"


# --------------------------
# MAIN
# --------------------------

def main():

    print("Refreshing token")

    access_token = get_access_token()

    headers = {"Authorization":f"Bearer {access_token}"}

    activities = get_activities(headers)

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)

    for act in activities:

        start = dt.datetime.fromisoformat(
            act["start_date"].replace("Z","+00:00")
        )

        if start < cutoff:
            continue

        sport = act["type"]

        print("\n==============================")
        print(act["name"],"|",sport)
        print("distance:",round(act["distance"]/1000,2),"km")

        streams = get_streams(act["id"],headers)

        if not streams:
            continue

        df = streams_to_dataframe(streams)

        print("points:",len(df))

        # --------------------------
        # RUN
        # --------------------------

        if sport == "Run":

            if "pace_min_km" in df:

                efforts = best_efforts(df["pace_min_km"],EFFORT_WINDOWS)

                print("\nBEST PACE")

                for d,v in efforts.items():
                    print(d,"sec →",format_pace(v),"/km")

            if "watts" in df:

                efforts = best_efforts(df["watts"],EFFORT_WINDOWS)

                print("\nBEST RUNNING POWER")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"W")

            if "heartrate" in df:

                efforts = best_efforts(df["heartrate"],EFFORT_WINDOWS)

                print("\nBEST HR")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"bpm")


        # --------------------------
        # CYCLING
        # --------------------------

        if sport in ["Ride","VirtualRide"]:

            if "watts" in df:

                efforts = best_efforts(df["watts"],EFFORT_WINDOWS)

                print("\nBEST POWER")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"W")

            if "speed_kmh" in df:

                efforts = best_efforts(df["speed_kmh"],EFFORT_WINDOWS)

                print("\nBEST SPEED")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"km/h")

            if "heartrate" in df:

                efforts = best_efforts(df["heartrate"],EFFORT_WINDOWS)

                print("\nBEST HR")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"bpm")


        # --------------------------
        # SWIM
        # --------------------------

        if sport == "Swim":

            if "pace_min_km" in df:

                efforts = best_efforts(df["pace_min_km"],EFFORT_WINDOWS)

                print("\nBEST SWIM PACE")

                for d,v in efforts.items():
                    print(d,"sec →",format_pace(v),"/km")

            if "heartrate" in df:

                efforts = best_efforts(df["heartrate"],EFFORT_WINDOWS)

                print("\nBEST HR")

                for d,v in efforts.items():
                    print(d,"sec →",round(v,1),"bpm")


if __name__ == "__main__":
    main()
