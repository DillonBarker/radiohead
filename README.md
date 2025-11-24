# Radiohead Setlist Predictor 🎸

A data-driven tool to predict Radiohead's setlist for multi-night concert runs using historical tour data, variety pattern analysis, and machine learning insights.

## Overview

This project analyzes Radiohead's 2025 European tour setlists to predict what songs they're most likely to play at upcoming shows. It uses the Setlist.fm API to fetch real concert data and applies statistical analysis to identify patterns in how the band varies their setlists across multiple nights in the same city.

## How It Works

### 1. Data Collection
- Fetches all Radiohead setlists from the [Setlist.fm API](https://api.setlist.fm/)
- Filters for 2025 European tour dates (UK, Spain, France, Germany, Italy, Netherlands, Belgium, Sweden)
- Processes setlist data from all available shows

### 2. Variety Pattern Analysis
The key insight: **Radiohead varies their setlists significantly between nights in multi-night stands**.

The algorithm analyzes cities with multiple shows to calculate:
- **Setlist variation percentage**: How much the setlist changes between consecutive nights
- **Song rotation patterns**: Which songs get rotated vs. which are staples
- **City-specific patterns**: How London shows compare to other multi-night venues

**Current findings:**
- London shows: ~112% variation (essentially full setlist rotation possible!)
- Madrid (4 shows): ~115% variation
- Casalecchio di Reno (4 shows): ~125% variation

### 3. Prediction Algorithm

Each song receives a prediction score based on:

#### Weighted Factors:
- **60% - Tour Frequency**: How often the song appears across all tour dates
- **20% - London-Specific Patterns**: Historical frequency at London shows
- **20% - Variety Adjustment**: Based on multi-night rotation behavior

#### Variety Adjustments:
- **+0.2 boost**: Songs NOT yet played in London (fresh for the crowd)
- **-0.15 penalty**: Songs played at EVERY London show that aren't tour staples
- **No penalty**: Tour staples (>90% frequency) are exempt from variety penalties
- **+0.05 slight boost**: Songs played at some (but not all) London shows

#### Tour Staples Protection:
Songs played at 90%+ of shows (like "Paranoid Android", "Everything in Its Right Place") are considered staples and maintain high prediction scores regardless of London frequency.

### 4. Output

The tool generates:
1. **Excel file** with three sheets:
   - Setlists: Show-by-show breakdown
   - Song Counts: All songs ranked by frequency
   - London Night 4 Prediction: Predicted setlist with probabilities

2. **Spotify Playlist**: Auto-generated/updated playlist with predicted songs in order

3. **Console Analysis**: Real-time statistics and insights

## Setup

### Prerequisites
- Python 3.8+
- Spotify account (for playlist feature)

### Installation

1. **Clone/download this repository**

2. **Create virtual environment and install dependencies:**
```bash
python3 -m venv radiohead_env
source radiohead_env/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

3. **Set up API credentials:**

Create a `.env` file in the project root:
```bash
# Setlist.fm API (get from https://api.setlist.fm/docs/1.0/index.html)
SETLISTFM_API_KEY=your_setlistfm_api_key

# Spotify API (get from https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

#### Getting API Keys:

**Setlist.fm API:**
1. Go to https://api.setlist.fm/docs/1.0/index.html
2. Apply for a free API key
3. Add to `.env` file

**Spotify API:**
1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Set redirect URI to `http://localhost:8888/callback`
4. Copy Client ID and Client Secret to `.env` file
5. On first run, you'll authorize the app through your browser

### Requirements

Create a `requirements.txt` file:
```
requests>=2.25.0
pandas>=2.0.0
openpyxl>=3.0.0
numpy>=1.20.0
spotipy>=2.25.0
python-dotenv>=1.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the prediction:
```bash
python main.py
```

This will:
1. Fetch latest setlist data (including any new shows)
2. Analyze variety patterns
3. Generate predictions
4. Update Excel file
5. Create/update Spotify playlist

### Updating Predictions

After each new show, simply run the script again:
```bash
python main.py
```

The prediction model automatically:
- Incorporates new setlist data
- Recalculates probabilities
- Updates the Spotify playlist with fresh predictions

### Output Files

- `radiohead_2025_european_tour_setlists.xlsx`: Complete data and predictions
- `.cache`: Spotify authentication cache (auto-generated)

## Understanding the Predictions

### Markers in Output:
- 🔴 **Red**: Played at ALL London shows (might rotate out for variety)
- 🟡 **Yellow**: Played at SOME London shows (rotating favorites)
- 🟢 **Green**: NOT played in London yet (high variety boost!)

### Probability Percentages:
- **100%**: Tour staple - played at every show
- **70-90%**: Very likely - frequent tour rotation
- **50-60%**: Toss-up - rotating songs
- **<50%**: Wildcards - rare treats

### Expected Setlist Length:
Based on tour average: ~25 songs

## Methodology Notes

### Why >100% Variation?

The variation percentage can exceed 100% because it counts both:
- Songs **removed** from the previous setlist
- Songs **added** to the current setlist

Example: If 14 songs are swapped out and 14 new ones added = 28 changes = 112% of a 25-song setlist.

### Limitations

- Predictions are statistical - Radiohead is known for spontaneity!
- Fresh setlists (from shows on the day) may take time to appear on Setlist.fm
- Rare deep cuts and covers are hard to predict with limited data
- Band decisions based on factors we can't measure (technical issues, crowd energy, etc.)

## Project Structure

```
radiohead/
├── main.py                                      # Main prediction script
├── .env                                         # API credentials (gitignored)
├── .gitignore                                   # Git ignore rules
├── README.md                                    # This file
├── requirements.txt                             # Python dependencies
├── radiohead_2025_european_tour_setlists.xlsx  # Output data
└── radiohead_env/                              # Virtual environment (gitignored)
```

## Future Enhancements

Potential improvements:
- [ ] Position-based predictions (opener, closer, encore)
- [ ] Temporal patterns (recent vs. distant plays)
- [ ] Album era analysis (which albums are featured most)
- [ ] Venue size/type correlations
- [ ] Weather/time-of-week patterns
- [ ] Machine learning classification models

## Data Source

All setlist data is sourced from [Setlist.fm](https://www.setlist.fm/), a collaborative database of concert setlists contributed by fans worldwide.

## License

This is a personal project for educational and entertainment purposes. All Radiohead music and trademarks belong to their respective owners.

---

**Enjoy the show! 🎵**
