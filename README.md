# Spotify Top Songs & Artists Explorer (Dash)

Interactive Dash app to explore Spotify audio features by artist, year, and song.  
Built for **COMP 4433 – Project 2**. The app is explanatory and user-facing, with polished visuals and clear instructions.

---

##  Features

- **4+ user inputs**
  - Year **RangeSlider**
  - **Song** search (text input, debounce)
  - **Artist** dropdown (auto-updates based on year/search)
  - **Metric** selector (radio: danceability, energy, valence, tempo, + extras if present)
- **Interactive callbacks**
  - One callback updates the 3 charts
  - Another callback dynamically rebuilds the Artist list
- **3 Plotly visuals**
  1) Metric **trend over time** (line)
  2) **Energy vs. Tempo** (scatter; bubble size = popularity when available)
  3) **Top tracks** (horizontal bar, ranked by popularity)
- **Built-in guidance** (collapsible “How to use” panel + footer)
- **Deployment-ready** (`server = app.server`, works with gunicorn)

---

## Rubric mapping 

- **Dash Core Components (≥4):** RangeSlider, Input, Dropdown, RadioItems.  
- **Interactivity:** ≥1 callback (I have 2).  
- **Plotly plots (≥3):** line, scatter, bar.  
- **Narrative / instructions:** on-page help + footer.  
- **Polish:** titles, labels, axis ranges, hover info, consistent layout.  
- **Repo contains what’s needed to run locally:** `requirements.txt`, `README.md`, `data/` notes.  
Source: COMP 4433 Project 2 brief

---

## Project structure
```text  
.
├── app.py
├── requirements.txt
├── README.md
├── assets/
│   └── style.css
├── data/
│   ├── original_data.csv        # original Kaggle CSV (ignored; too large)
│   └── spotify_data.csv.gz      # compressed CSV (tracked)
└── .devcontainer/
    └── devcontainer.json
```
```text
.gitignore
---------
.venv/
__pycache__/
.DS_Store
data/*.csv
!data/*.csv.gz
```


## Quickstart (GitHub Codespaces)

1. Open this repo in **Codespaces**.
2. If prompted, **Rebuild Container** (runs the postCreate command to set up Python + venv).
3. Run the app:
```bash
   python app.py 
```
4. Click the forwarded port 8050 → app opens in your browser. 



## Quickstart (Local)
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate

pip install -U pip
pip install -r requirements.txt

python app.py
# visit http://127.0.0.1:8050
```



## Data

- Expected columns (Kaggle schema):  
    `artist_name, track_name, year, popularity, danceability, energy, valence, tempo, (optional: acousticness, speechiness, instrumentalness, liveness, loudness, genre, …)`

- CSV was found from Kaggle at this URL:
  `https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks?resource=download&select=spotify_data.csv`
    
- Put your CSV in `data/` (e.g., `data/spotify_data.csv`).
    
- The app auto-detects `*.csv` and `*.csv.gz`.
    

### Data size note (GitHub’s 100 MB limit)

If your CSV is larger than 100 MB, **don’t commit it**. Either:

- Add it to `.gitignore` and keep it local/only in Codespaces, **or**
    
- Commit a compressed subset (This is what I did):

```bash
# in repo root
gzip -k data/spotify_data.csv          # makes data/spotify_data.csv.gz (keeps original)
# or with Python:
# python - << 'PY'
# import pandas as pd; pd.read_csv("data/spotify_data.csv", low_memory=False)\
#   .to_csv("data/spotify_data.csv.gz", index=False, compression="gzip")
# PY

# ignore the big uncompressed file so you don’t push it by accident
echo "data/*.csv" >> .gitignore

git add data/spotify_data.csv.gz .gitignore
git commit -m "data: add compressed spotify csv"
git push
```


Update your repo to include the smaller `data/spotify_subset.csv.gz`.

The app already supports `.csv.gz` since it uses the loader with `compression="infer"`.
```python
pd.read_csv(path, low_memory=False, compression="infer")
```

## Configuration

- The app binds to `0.0.0.0` and respects `PORT` (good for Codespaces/Render/Heroku):

```python
# app.py (at bottom)
import os
port = int(os.environ.get("PORT", 8050))
app.run(debug=True, host="0.0.0.0", port=port)
```

- WSGI server export for deployment:

```python
app = Dash(__name__)
server = app.server
```



## How to use the app (in-app instructions)

- Pick a **Year range** to scope the dataset.
    
- Type part of a **Song** title to filter results.
    
- The **Artist** list auto-updates to match your filters.
    
- Choose a **Metric** to change the trend plot.
    
- Hover any point/bar for song details.



## Troubleshooting

- **“No module named dash”** → `pip install -r requirements.txt` (inside your venv).
    
- **Port already in use** → set `PORT=8051` before running, or kill existing process.
    
- **Artist dropdown empty** → verify your CSV column names and that `year` is within 1950–2030.
    
- **Push fails due to file size** → don’t commit the large CSV; commit the gzipped subset.



## Credits

- Dataset: Spotify audio features (Kaggle). 
	- https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks?resource=download&select=spotify_data.csv
    
- Built with: **Dash 3**, **Plotly**, **Pandas**.
    
- Course requirements summarized from COMP 4433 Project 2 brief
