import pandas as pd
import streamlit as st


def apply_filters(df):

    # aseguramos tipo datetime SIEMPRE
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    with st.expander("Filters"):

        sports = st.multiselect(
            "Sport",
            sorted(df["type"].dropna().unique()),
            default=sorted(df["type"].dropna().unique())
        )

        time_range = st.radio(
            "Time range",
            ["All time", "YTD", "2YTD", "4YTD"]
        )

    # filtro deporte
    if sports:
        df = df[df["type"].isin(sports)]

    # fecha actual
    now = pd.Timestamp.now()

    # definimos cutoff
    cutoff = None

    if time_range == "YTD":
        cutoff = now - pd.DateOffset(months=12)

    elif time_range == "2YTD":
        cutoff = now - pd.DateOffset(years=2)

    elif time_range == "4YTD":
        cutoff = now - pd.DateOffset(years=4)

    # aplicamos filtro si procede
    if cutoff is not None:

        # volvemos a asegurar datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        df = df[df["date"] >= cutoff]

    return df
