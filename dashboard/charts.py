import plotly.graph_objects as go


def weekly_chart(weekly, achievements=None):

    if achievements is None:
        achievements = {}

    best_week_index = weekly["hours"].idxmax()

    colors = []

    for i in range(len(weekly)):
        if i == best_week_index:
            colors.append("#FFD700")
        else:
            colors.append("#3B82F6")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weekly["week"],
            y=weekly["hours"],
            name="Weekly hours",
            marker_color=colors
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=weekly["rolling"],
            name="4 week avg",
            line=dict(color="#2563EB", width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weekly["week"],
            y=[7] * len(weekly),
            name="target",
            line=dict(color="#10B981", dash="dash")
        )
    )

    best_week = weekly.loc[best_week_index]

    fig.add_annotation(
        x=best_week["week"],
        y=best_week["hours"] + 0.6,
        text="⭐",
        showarrow=False
    )

    for week, medals in achievements.items():

        row = weekly[weekly["week"] == week]

        if row.empty:
            continue

        y = row["hours"].values[0]

        if "run" in medals:

            fig.add_trace(
                go.Scatter(
                    x=[week],
                    y=[y + 0.5],
                    mode="markers",
                    marker=dict(size=12, color="#16A34A", symbol="circle"),
                    showlegend=False
                )
            )

        if "power" in medals:

            fig.add_trace(
                go.Scatter(
                    x=[week],
                    y=[y + 0.9],
                    mode="markers",
                    marker=dict(size=12, color="#F97316", symbol="diamond"),
                    showlegend=False
                )
            )

        if "hr" in medals:

            fig.add_trace(
                go.Scatter(
                    x=[week],
                    y=[y + 1.3],
                    mode="markers",
                    marker=dict(size=12, color="#DC2626", symbol="x"),
                    showlegend=False
                )
            )

    fig.update_layout(
        height=330,
        margin=dict(l=5, r=5, t=20, b=5),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.5,
            xanchor="center"
        )
    )

    return fig
