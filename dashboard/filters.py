import pandas as pd
import streamlit as st


def apply_filters(df):

    with st.expander("Filters"):

        sports = st.multiselect(
            "Sport",
            sorted(df["type"].unique()),
            default=sorted(df["type"].unique()),
        )

        time_range = st.radio(
            "Time range",
            ["All time", "YTD", "2YTD", "4YTD"],
        )

    df = df[df["type"].isin(sports)]

    now = pd.Timestamp.now()

    if time_range == "YTD":
        cutoff = now - pd.DateOffset(months=12)

    elif time_range == "2YTD":
        cutoff = now - pd.DateOffset(years=2)

    elif time_range == "4YTD":
        cutoff = now - pd.DateOffset(years=4)

    else:
        cutoff = None

    if cutoff is not None:
        df = df[df["date"] >= cutoff]

    return df
