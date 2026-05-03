import pandas as pd
import sqlite3


DISTANCES = {
    "5K": (3000, 7000),
    "10K": (8000, 12000),
    "21K": (18000, 25000),
}


# ---------------- FORMAT ----------------

def format_pace(sec_per_km):
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    return f"{minutes}:{seconds:02d}"


# ---------------- PB DETECTION ----------------

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


# ---------------- LOAD METRICS ----------------

def compute_rolling_km(df, date, days):
    start = date - pd.Timedelta(days=days)
    mask = (df["date"] >= start) & (df["date"] <= date)
    return df.loc[mask, "distance"].sum() / 1000


# ---------------- INTENSITY ----------------

def compute_intensity(df, date):
    start = date - pd.Timedelta(days=28)

    subset = df[(df["date"] >= start) & (df["date"] <= date)].copy()

    if subset.empty:
        return 0

    subset["pace"] = subset["moving_time"] / (subset["distance"] / 1000)

    threshold = subset["pace"].quantile(0.3)  # top 30% más rápidos

    fast_runs = subset[subset["pace"] <= threshold]

    return len(fast_runs) / len(subset)


# ---------------- CROSS LOAD ----------------

def compute_cross_load(df, date):
    start = date - pd.Timedelta(days=56)

    subset = df[(df["date"] >= start) & (df["date"] <= date)]

    run_km = subset[subset["type"] == "Run"]["distance"].sum() / 1000
    bike_km = subset[subset["type"] == "Ride"]["distance"].sum() / 1000

    # ponderación bici
    total = run_km + (bike_km * 0.3)

    return total


# ---------------- MAIN FUNCTION ----------------

def compute_pb_timeline():
    conn = sqlite3.connect("data/activities.db")

    df = pd.read_sql("SELECT * FROM activities WHERE type IN ('Run', 'Ride')", conn)
    conn.close()

    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["start_date"])

    run_df = df[df["type"] == "Run"].copy()

    pbs = get_pb_activities(run_df)

    records = []

    for _, row in pbs.iterrows():
        date = row["date"]

        km_8w = compute_rolling_km(run_df, date, 56)
        km_w1 = compute_rolling_km(run_df, date, 7)
        km_4w = compute_rolling_km(run_df, date, 28)

        intensity = compute_intensity(run_df, date)
        cross = compute_cross_load(df, date)

        records.append({
            "date": date,
            "distance": row["distance_label"],
            "pace": row["pace"],
            "km_8w": km_8w,
            "km_w1": km_w1,
            "km_4w": km_4w,
            "intensity": intensity,
            "cross_load": cross
        })

    result = pd.DataFrame(records)

    # ---------------- FORMAT FINAL ----------------

    result["pace_str"] = result["pace"].apply(format_pace)

    result["km_8w"] = result["km_8w"].round(0)
    result["km_w1"] = result["km_w1"].round(0)
    result["km_4w"] = result["km_4w"].round(0)
    result["cross_load"] = result["cross_load"].round(0)
    result["intensity"] = result["intensity"].round(2)

    result = result.sort_values(["distance", "pace"])
    result["rank"] = result.groupby("distance").cumcount() + 1

    result = result.sort_values(["distance", "rank"])

    return result


# ---------------- SUMMARY ----------------

def summarize_training_factors(df):
    return df.groupby("distance")[[
        "km_8w",
        "km_w1",
        "km_4w",
        "intensity",
        "cross_load"
    ]].mean().round(2)
