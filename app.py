# ------------------------------------------------------------
# Spotify Explorer (Dash + Plotly)
# - Loads a Spotify/Kaggle CSV (supports .csv or .csv.gz)
# - Lets you filter by year range, search tracks, pick an artist
# - Plots: metric trend by year, Energy vs Tempo, Top tracks bar
# - Safe to paste and run as-is 
# ------------------------------------------------------------

from dash import Dash, dcc, html, Input, Output, State, callback, no_update
import plotly.express as px
import pandas as pd
from pathlib import Path
from functools import lru_cache

# Plotly defaults for a consistent, clean look across figures
px.defaults.template = "plotly_white"
px.defaults.height = 420

# Directory where we expect the Kaggle CSV to live (e.g., ./data/spotify_data.csv)
DATA_DIR = Path(__file__).parent / "data"

# ---------- Data ----------
@lru_cache(maxsize=1)  # Cache the loaded DataFrame once per process run
def load_spotify() -> pd.DataFrame:
    """
    Find a Spotify CSV in ./data (supports .csv or .csv.gz), load it into a DataFrame,
    perform light cleaning, verify required columns, and return the cleaned DataFrame.

    Returns:
        pd.DataFrame: Cleaned Spotify dataset.
    Raises:
        FileNotFoundError: If no CSV found in ./data.
        ValueError: If required columns are missing from the CSV.
    """
    # Look for the most likely file names first (spotify*.csv / .gz),
    # then fall back to any CSVs in the folder.
    candidates = (
        sorted(DATA_DIR.glob("spotify*.csv")) +
        sorted(DATA_DIR.glob("spotify*.csv.gz")) +
        sorted(DATA_DIR.glob("*.csv")) +
        sorted(DATA_DIR.glob("*.csv.gz"))
    )
    if not candidates:
        raise FileNotFoundError("Put your Kaggle CSV in /data (e.g., data/spotify_data.csv)")

    # compression="infer" lets pandas detect .gz automatically
    df = pd.read_csv(candidates[0], low_memory=False, compression="infer")
    print("Loaded:", candidates[0])

    # Columns we need for the app to work
    needed = ["artist_name", "track_name", "year", "danceability", "energy", "valence", "tempo"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Check your CSV.")

    # ---- Light cleanup ----
    # Normalize text columns (strip spaces, ensure str)
    df["artist_name"] = df["artist_name"].astype(str).str.strip()
    df["track_name"] = df["track_name"].astype(str).str.strip()

    # Coerce numeric columns; non-numeric values become NaN (then we drop where needed)
    for c in ["year", "popularity", "danceability", "energy", "valence", "tempo",
              "acousticness", "speechiness", "instrumentalness", "liveness", "loudness"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Keep reasonable year range (avoids weird outliers)
    df = df[df["year"].between(1950, 2030)]

    # Drop rows missing the essentials used in visuals/filters
    df = df.dropna(subset=["artist_name", "track_name", "year", "danceability", "energy", "valence", "tempo"])

    # Year should be integer (helps with sliders/labels)
    df["year"] = df["year"].astype(int)
    return df

# Load once 
df = load_spotify()

# Metric options will depend on which columns exist in the CSV you supplied
_possible_metrics = [
    "danceability","energy","valence","tempo","acousticness",
    "speechiness","instrumentalness","liveness","loudness","popularity"
]
_available_metrics = [m for m in _possible_metrics if m in df.columns]

# Labels for metrics
_label_map = {
    "danceability":"Danceability", "energy":"Energy", "valence":"Valence",
    "tempo":"Tempo (BPM)", "acousticness":"Acousticness", "speechiness":"Speechiness",
    "instrumentalness":"Instrumentalness", "liveness":"Liveness",
    "loudness":"Loudness (dB)", "popularity":"Popularity"
}

# Build RadioItems options for the Metric picker
metric_options = [{"label": _label_map.get(m, m.title()), "value": m} for m in _available_metrics]

# Default to danceability if present; otherwise the first available metric
default_metric = "danceability" if "danceability" in _available_metrics else _available_metrics[0]

# Year slider bounds derived from data
years = df["year"]
year_min, year_max = int(years.min()), int(years.max())

# ---------- Helpers ----------
def filter_data(dfin, artist, years_range, query_text):
    """
    Apply all filters to the DataFrame (year range, optional artist, optional track name query).
    Returns a copy filtered to the current UI selections.
    """
    lo, hi = years_range
    out = dfin[(dfin["year"] >= lo) & (dfin["year"] <= hi)].copy()

    # Filter to selected artist (if any)
    if artist:
        out = out[out["artist_name"] == artist]

    # Text search on track_name (case-insensitive contains)
    if query_text:
        qt = query_text.strip().lower()
        if qt:
            out = out[out["track_name"].str.lower().str.contains(qt)]
    return out

# ---------- App ----------
app = Dash(__name__)
server = app.server  # exposes Flask server for deployment platforms
app.title = "Spotify Explorer"

# --- Layout ---
# A simple 2-row page: controls at top, then three responsive charts.
app.layout = html.Div([
    html.H1("Spotify Top Songs & Artists Explorer"),

    # Collapsible "How to use" instructions
    html.Details([
        html.Summary("How to use"),
        dcc.Markdown(
            "- Pick a **Year range** to scope the dataset.\n"
            "- Start typing a **Song** title to filter.\n"
            "- The **Artist** list updates to the current filters.\n"
            "- Choose a **Metric** to change the trend plot.\n"
            "- Hover any point/bar for details."
        )
    ], open=False),

    # ---- Controls row ----
    html.Div([
        # Year range slider
        html.Div([
            html.Label("Year range"),
            dcc.RangeSlider(
                id="years", min=year_min, max=year_max, step=1,
                # Default to last ~8 years (or clamp to min)
                value=[max(year_min, year_max - 8), year_max],
                # Sparse ticks to keep it readable across wide ranges
                marks={y: str(y) for y in range(year_min, year_max + 1, max(1, (year_max-year_min)//10 or 1))},
                persistence=True,  # remember user selection on refresh
            ),
        ], style={"flex": "2", "minWidth": "280px"}),

        # Free-text search on track_name
        html.Div([
            html.Label("Song search"),
            dcc.Input(
                id="query", type="text", placeholder="Type a song title…",
                debounce=True,            # wait until user stops typing
                persistence=True
            ),
        ], style={"flex": "1", "minWidth": "240px"}),

        # Artist dropdown (options update based on current filters)
        html.Div([
            html.Label("Artist (auto-filters by year/search)"),
            dcc.Dropdown(id="artist", options=[], placeholder="Choose an artist", persistence=True),
        ], style={"flex": "1", "minWidth": "260px"}),

        # Metric picker (radio buttons)
        html.Div([
            html.Label("Metric"),
            dcc.RadioItems(id="metric", options=metric_options, value=default_metric, inline=True, persistence=True),
        ], style={"flex": "2", "minWidth": "320px"}),
    ], style={"display": "flex", "gap": "1rem", "flexWrap": "wrap", "marginTop": "0.75rem"}),

    html.Hr(),

    # ---- Charts grid ----
    # Responsive grid that wraps to 1 or 2 columns depending on viewport width
    html.Div([
        dcc.Graph(id="trend-graph"),    # metric-by-year (mean)
        dcc.Graph(id="scatter-graph"),  # Energy vs Tempo scatter
        dcc.Graph(id="bar-graph"),      # Top tracks by popularity/metric
    ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))", "gap": "1rem"}),

    # Footer with usage notes/source
    html.Footer([
        html.Small(
            "Data: https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks?resource=download&select=spotify_data.csv . "
            "Use the year range and search to narrow results; the artist list auto-updates. "
            "Metric selection changes the trend plot; hover points/bars for details."
        )
    ], style={"marginTop": "0.5rem", "color": "#555"})
])

# ---------- Callbacks ----------

# A) Dynamic artist options based on current filters (year range + song search)
@callback(
    Output("artist", "options"),  # Update dropdown choices
    Output("artist", "value"),    # And possibly clear/keep current selection
    Input("years", "value"),
    Input("query", "value"),
    State("artist", "value"),
)
def update_artist_options(years_range, query_text, current_artist):
    """
    Recompute the list of artist options whenever the year range or search query changes.
    If the currently selected artist is still valid, keep it; else clear selection.
    """
    lo, hi = years_range
    d = df[(df["year"] >= lo) & (df["year"] <= hi)]

    # Apply track name search filter if provided
    if query_text and (qt := query_text.strip().lower()):
        d = d[d["track_name"].str.lower().str.contains(qt)]

    # Rank artists by frequency within the current filtered set
    counts = d["artist_name"].value_counts()
    options = [{"label": a, "value": a} for a in counts.head(300).index.tolist()]  # cap to 300 to keep list responsive

    # Keep the current selection only if it's still present in the new options
    if current_artist and any(opt["value"] == current_artist for opt in options):
        return options, current_artist
    return options, None  # otherwise clear selection

# B) Main figures callback (depends on artist, metric, year range, and search query)
@callback(
    Output("trend-graph", "figure"),
    Output("scatter-graph", "figure"),
    Output("bar-graph", "figure"),
    Input("artist", "value"),
    Input("metric", "value"),
    Input("years", "value"),
    Input("query", "value"),
)
def update_figures(artist, metric, years_range, query_text):
    """
    Build three figures based on current filters:
      1) Trend over time (mean metric by year)
      2) Energy vs Tempo scatter (bubble size = popularity if present)
      3) Top tracks bar chart ranked by popularity (fallback to chosen metric)
    """
    dff = filter_data(df, artist, years_range, query_text)

    # --- 1) Trend over time (mean metric per year) ---
    if len(dff):
        trend = dff.groupby("year", as_index=False)[metric].mean().sort_values("year")
        fig_trend = px.line(
            trend, x="year", y=metric, markers=True,
            title=f"{_label_map.get(metric, metric.title())} Trend {years_range[0]}–{years_range[1]}"
                  + (f" — {artist}" if artist else "")
        )
        fig_trend.update_layout(xaxis_title="Year", yaxis_title=_label_map.get(metric, metric.title()))

        # If metric is a 0–1 feature, fix the y-axis to that range for interpretability
        if metric in {"danceability","energy","valence","acousticness","speechiness","instrumentalness","liveness"}:
            fig_trend.update_yaxes(range=[0, 1])
    else:
        # Empty-state figure
        fig_trend = px.scatter(title="No data for current filters")

    # --- 2) Energy vs Tempo scatter ---
    # Only keep rows with required columns present
    dff_scatter = dff[["track_name","artist_name","year","energy","tempo","popularity"]].dropna()
    if len(dff_scatter) > 5000:
        dff_scatter = dff_scatter.sample(5000, random_state=7)
    if len(dff_scatter):
        fig_scatter = px.scatter(
            dff_scatter, x="tempo", y="energy",
            hover_data=["track_name","artist_name","year","popularity"],
            size="popularity" if "popularity" in dff_scatter.columns else None,
            title="Energy vs Tempo"
                  + (f" — {artist}" if artist else "")
                  + f" ({years_range[0]}–{years_range[1]})"
        )
        fig_scatter.update_layout(xaxis_title="Tempo (BPM)", yaxis_title="Energy", hovermode="closest")
        fig_scatter.update_yaxes(range=[0, 1])  # Energy is 0–1
    else:
        fig_scatter = px.scatter(title="No data for current filters")

    # --- 3) Top tracks bar chart ---
    # Prefer to rank by popularity if available; else fallback to chosen metric
    rank_metric = "popularity" if "popularity" in dff.columns else metric
    top = dff.sort_values(rank_metric, ascending=False).head(15)[["track_name","artist_name",rank_metric]]
    if len(top):
        # Reverse order so the highest bar appears at the top (typical horizontal bar style)
        fig_bar = px.bar(
            top.iloc[::-1], x=rank_metric, y="track_name",
            orientation="h", text=rank_metric,
            title=f"Top Tracks by {_label_map.get(rank_metric, rank_metric.title())}"
                  + (f" — {artist}" if artist else "")
        )
        fig_bar.update_layout(xaxis_title=_label_map.get(rank_metric, rank_metric.title()), yaxis_title="Track")
        fig_bar.update_traces(textposition="outside", cliponaxis=False)  # show labels outside bars
    else:
        fig_bar = px.bar(title="No top tracks for current filters")

    # Apply consistent layout polish to all figures
    for fig in (fig_trend, fig_scatter, fig_bar):
        fig.update_layout(
            margin=dict(l=40, r=16, t=60, b=40),
            legend_title_text="",
            hoverlabel=dict(namelength=-1),  # don't truncate hover labels
        )

    return fig_trend, fig_scatter, fig_bar

# ---------- Run ----------
if __name__ == "__main__":
    # debug=True for live reload during development
    # host="0.0.0.0" exposes the app for Docker/Codespaces; change to "127.0.0.1" for local-only
    app.run(debug=True, host="0.0.0.0", port=8050)