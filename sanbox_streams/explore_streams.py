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
        "watts",
        "grade_smooth",
        "altitude"
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
        df["pace_min_km"] = (1000/df["velocity_smooth"])/60

    return df


# --------------------------
# DISTRIBUTION
# --------------------------

def compute_distribution(series, rounding=2):

    series = series.replace([float("inf")],None).dropna()

    return series.round(rounding).value_counts().sort_index()


# --------------------------
# BEST EFFORTS
# --------------------------

def best_efforts(series, durations):

    results = {}

    for d in durations:

        rolling = series.rolling(d).mean()

        best = rolling.max()

        results[d] = best

    return results


def format_pace(value):

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

        print("\n==============================")
        print(act["name"],"|",act["type"])
        print("distance:",round(act["distance"]/1000,2),"km")

        streams = get_streams(act["id"],headers)

        if not streams:
            continue

        df = streams_to_dataframe(streams)

        print("points:",len(df))

        # ------------------
        # DISTRIBUTIONS
        # ------------------

        if "pace_min_km" in df:

            print("\nPACE DISTRIBUTION (top 10)")

            dist = compute_distribution(df["pace_min_km"])

            top = dist.sort_values(ascending=False).head(10)

            for pace,sec in top.items():
                print(format_pace(pace),"→",sec,"sec")


        if "watts" in df:

            print("\nPOWER DISTRIBUTION (top 10)")

            dist = compute_distribution(df["watts"],0)

            top = dist.sort_values(ascending=False).head(10)

            for w,sec in top.items():
                print(int(w),"W →",sec,"sec")


        if "heartrate" in df:

            print("\nHR DISTRIBUTION (top 10)")

            dist = compute_distribution(df["heartrate"],0)

            top = dist.sort_values(ascending=False).head(10)

            for hr,sec in top.items():
                print(int(hr),"bpm →",sec,"sec")


        # ------------------
        # BEST EFFORTS
        # ------------------

        if "watts" in df:

            efforts = best_efforts(df["watts"],EFFORT_WINDOWS)

            print("\nBEST POWER EFFORTS")

            for d,v in efforts.items():
                print(d,"sec →",round(v,1),"W")


        if "velocity_smooth" in df:

            efforts = best_efforts(df["velocity_smooth"],EFFORT_WINDOWS)

            print("\nBEST SPEED EFFORTS")

            for d,v in efforts.items():

                pace = (1000/v)/60

                print(d,"sec →",format_pace(pace),"/km")


if __name__ == "__main__":
    main()
