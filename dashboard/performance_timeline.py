import pandas as pd
import sqlite3


DISTANCES = {
    "5K": (4000, 6000),
    "10K": (9000, 11000),
    "21K": (20000, 23000),
}


def get_pb_activities(conn):
    df = pd.read_sql("SELECT * FROM activities WHERE type='Run'", conn)

    df["pace"] = df["moving_time"] / (df["distance"] / 1000)
    df["date"] = pd.to_datetime(df["start_date"])

    results = []

    for label, (min_d, max_d) in DISTANCES.items():
        subset = df[(df["distance"] >= min_d) & (df["distance"] <= max_d)]

        if subset.empty:
            continue

        top = subset.sort_values("pace").head(5).copy()
        top["distance_label"] = label

        results.append(top)

    return pd.concat(results)


def compute_rolling_km(df, date):
    start = date - pd.Timedelta(days=56)

    mask = (df["date"] >= start) & (df["date"] <= date)

    return df.loc[mask, "distance"].sum() / 1000


def compute_pb_timeline():
    conn = sqlite3.connect("data/activities.db")

    df = pd.read_sql("SELECT * FROM activities WHERE type='Run'", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["start_date"])

    pbs = get_pb_activities(sqlite3.connect("data/activities.db"))

    records = []

    for _, row in pbs.iterrows():
        km_8w = compute_rolling_km(df, row["date"])

        records.append({
            "date": row["date"],
            "distance": row["distance_label"],
            "pace": row["pace"],
            "km_8w": km_8w
        })

    return pd.DataFrame(records)
