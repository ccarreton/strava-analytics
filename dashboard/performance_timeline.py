import pandas as pd
import sqlite3


DISTANCES = {
    "5K": (3000, 7000),
    "10K": (8000, 12000),
    "21K": (18000, 25000),
}


def format_pace(sec_per_km):
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def get_pb_activities(df):
    df = df.copy()

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

    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["start_date"])

    pbs = get_pb_activities(df)

    records = []

    for _, row in pbs.iterrows():
        date = row["date"]

        # 🔹 8 semanas
        start_8w = date - pd.Timedelta(days=56)
        km_8w = df[(df["date"] >= start_8w) & (df["date"] <= date)]["distance"].sum() / 1000

        # 🔹 semana -1 (taper real)
        start_w1 = date - pd.Timedelta(days=7)
        km_w1 = df[(df["date"] >= start_w1) & (df["date"] < date)]["distance"].sum() / 1000

        # 🔹 fitness proxy (últimas 4 semanas)
        start_4w = date - pd.Timedelta(days=28)
        km_4w = df[(df["date"] >= start_4w) & (df["date"] <= date)]["distance"].sum() / 1000

        records.append({
            "date": date,
            "distance": row["distance_label"],
            "pace": row["pace"],
            "km_8w": km_8w,
            "km_w1": km_w1,
            "km_4w": km_4w
        })

    result = pd.DataFrame(records)

    # 🧠 FORMATO
    result["pace_str"] = result["pace"].apply(format_pace)

    result["km_8w"] = result["km_8w"].round(0)
    result["km_w1"] = result["km_w1"].round(0)
    result["km_4w"] = result["km_4w"].round(0)

    result = result.sort_values(["distance", "pace"])
    result["rank"] = result.groupby("distance").cumcount() + 1

    result = result.sort_values(["distance", "rank"])

    return result
