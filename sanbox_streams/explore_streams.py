import os
import requests
import pandas as pd
import datetime as dt

BASE_URL = "https://www.strava.com/api/v3"

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")


# -----------------------------------
# AUTH
# -----------------------------------

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


# -----------------------------------
# ACTIVITIES
# -----------------------------------

def get_activities(headers):

    r = requests.get(
        f"{BASE_URL}/athlete/activities",
        headers=headers,
        params={"per_page": 30}
    )

    return r.json()


# -----------------------------------
# STREAMS
# -----------------------------------

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
            "keys": ",".join(keys),
            "key_by_type": "true"
        }
    )

    if r.status_code != 200:
        return None

    return r.json()


# -----------------------------------
# DATAFRAME
# -----------------------------------

def streams_to_dataframe(streams):

    data = {}

    for k in streams:
        data[k] = streams[k]["data"]

    df = pd.DataFrame(data)

    if "velocity_smooth" in df:

        df["pace_min_km"] = (1000 / df["velocity_smooth"]) / 60

    return df


# -----------------------------------
# DISTRIBUTION
# -----------------------------------

def compute_distribution(series, rounding=2):

    series = series.replace([float("inf")], None).dropna()

    dist = series.round(rounding).value_counts().sort_index()

    return dist


def format_pace(value):

    minutes = int(value)
    seconds = int((value - minutes) * 60)

    return f"{minutes}:{seconds:02d}"


# -----------------------------------
# ANALYSIS
# -----------------------------------

def analyze_activity(df):

    results = {}

    if "pace_min_km" in df:

        pace_dist = compute_distribution(df["pace_min_km"])

        results["pace"] = pace_dist

    if "watts" in df:

        power_dist = compute_distribution(df["watts"],0)

        results["power"] = power_dist

    if "heartrate" in df:

        hr_dist = compute_distribution(df["heartrate"],0)

        results["hr"] = hr_dist

    return results


# -----------------------------------
# MAIN
# -----------------------------------

def main():

    print("Refreshing token")

    access_token = get_access_token()

    headers = {"Authorization": f"Bearer {access_token}"}

    activities = get_activities(headers)

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)

    for act in activities:

        start = dt.datetime.fromisoformat(
            act["start_date"].replace("Z","+00:00")
        )

        if start < cutoff:
            continue

        print("\n============================")
        print(act["name"], act["type"])

        streams = get_streams(act["id"], headers)

        if not streams:
            continue

        df = streams_to_dataframe(streams)

        print("points:", len(df))

        results = analyze_activity(df)

        # ---------------------
        # PRINT RESULTS
        # ---------------------

        if "pace" in results:

            print("\nPACE DISTRIBUTION (top 10)")

            top = results["pace"].sort_values(ascending=False).head(10)

            for pace,sec in top.items():

                print(format_pace(pace), sec,"sec")


        if "power" in results:

            print("\nPOWER DISTRIBUTION (top 10)")

            top = results["power"].sort_values(ascending=False).head(10)

            for watts,sec in top.items():

                print(watts,"W →",sec,"sec")


        if "hr" in results:

            print("\nHR DISTRIBUTION (top 10)")

            top = results["hr"].sort_values(ascending=False).head(10)

            for hr,sec in top.items():

                print(hr,"bpm →",sec,"sec")


if __name__ == "__main__":
    main()
