from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd

app = Dash(__name__)
app.title = "Spotify Explorer"

app.layout = html.Div([
    html.H1("Spotify Top Songs & Artists Explorer"),
    html.P("Once data is added to /data, use the controls below to explore."),

    html.Div([
        html.Div([
            html.Label("Artist"),
            dcc.Dropdown(id="artist", options=[], placeholder="Choose an artist"),
        ], style={"flex": "1", "minWidth": "260px"}),

        html.Div([
            html.Label("Metric"),
            dcc.RadioItems(
                id="metric",
                options=[
                    {"label": "Danceability", "value": "danceability"},
                    {"label": "Energy", "value": "energy"},
                    {"label": "Tempo", "value": "tempo"},
                    {"label": "Valence", "value": "valence"},
                ],
                value="danceability",
                inline=True,
            ),
        ], style={"flex": "2", "minWidth": "320px"}),

        html.Div([
            html.Label("Year range"),
            dcc.RangeSlider(
                id="years", min=2015, max=2025, step=1, value=[2018, 2024],
                marks={y: str(y) for y in range(2015, 2026, 2)}
            ),
        ], style={"flex": "2", "minWidth": "280px"}),

        html.Div([
            html.Label("Song search"),
            dcc.Input(id="query", type="text", placeholder="Type a song title…", debounce=True),
        ], style={"flex": "1", "minWidth": "240px"}),
    ], style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"}),

    html.Hr(),

    html.Div([
        dcc.Graph(id="trend-graph", figure=px.scatter(x=[0], y=[0], title="Trend (placeholder)")),
        dcc.Graph(id="scatter-graph", figure=px.scatter(x=[0], y=[0], title="Energy vs Tempo (placeholder)")),
        dcc.Graph(id="bar-graph", figure=px.bar(x=["Example"], y=[1], title="Top Tracks (placeholder)")),
    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
        "gap": "1rem"
    }),
])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)  