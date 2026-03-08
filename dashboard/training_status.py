import plotly.graph_objects as go


def training_status_gauge(tsb):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=tsb,
            title={"text": "Training Status"},
            gauge={
                "axis": {"range": [-20, 20]},
                "bar": {"color": "#2563EB"},
                "steps": [

                    {"range": [-20, -10], "color": "#FCA5A5"},
                    {"range": [-10, -5], "color": "#FCD34D"},
                    {"range": [-5, 5], "color": "#86EFAC"},
                    {"range": [5, 10], "color": "#34D399"},
                    {"range": [10, 20], "color": "#60A5FA"},

                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "value": tsb
                }
            }
        )
    )

    fig.update_layout(

        height=300,

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )

    )

    return fig
