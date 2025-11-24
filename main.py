import requests
import pandas as pd
import numpy as np
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIG ===
API_KEY = os.getenv("SETLISTFM_API_KEY")
ARTIST_MBID = "a74b1b7f-71a5-4011-9441-d0b5e4122711"  # MusicBrainz ID for Radiohead
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

# Spotify Config
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
PLAYLIST_NAME = "Radiohead - London Night 4 Prediction"

# === STEP 1: Get all setlists for Radiohead ===
all_setlists = []
page = 1
while True:
    url = f"https://api.setlist.fm/rest/1.0/artist/{ARTIST_MBID}/setlists?p={page}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    if "setlist" not in data or not data["setlist"]:
        break
    
    all_setlists.extend(data["setlist"])
    
    # Check if there are more pages
    total = int(data.get("total", 0))
    items_per_page = int(data.get("itemsPerPage", 20))
    if page * items_per_page >= total:
        break
    
    page += 1

print(f"📥 Fetched {len(all_setlists)} total setlists")

# === STEP 2: Filter for 2025 European tour ===
setlists = {}
for s in all_setlists:
    event_date = s["eventDate"]  # e.g. "04-11-2025"
    venue = s["venue"]["name"]
    city = s["venue"]["city"]["name"]
    country = s["venue"]["city"]["country"]["code"]
    if "2025" in event_date and country in ["ES", "FR", "DE", "GB", "IT", "NL", "BE", "SE"]:  # Europe (GB = UK)
        date_label = f"{event_date} ({city})"
        songs = []
        for set_part in s["sets"]["set"]:
            for song in set_part["song"]:
                songs.append(song["name"])
        setlists[date_label] = songs

print(f"🎸 Found {len(setlists)} European 2025 shows")

# === STEP 3: Create table where each column = date ===
# Filter out any empty setlists just in case
filtered_setlists = {date: songs for date, songs in setlists.items() if songs}

# Find the maximum number of songs
max_len = max(len(songs) for songs in filtered_setlists.values())

# Pad shorter setlists with empty strings
for date, songs in filtered_setlists.items():
    if len(songs) < max_len:
        filtered_setlists[date] += [""] * (max_len - len(songs))

# Create DataFrame for setlists
df = pd.DataFrame(filtered_setlists)

# === STEP 4: Calculate song counts ===
# Count occurrences of each song across all setlists
song_counts = {}
for songs in filtered_setlists.values():
    for song in songs:
        if song and song.strip():  # Only count non-empty songs
            if song in song_counts:
                song_counts[song] += 1
            else:
                song_counts[song] = 1

# Create a summary table sorted by occurrence (most to least)
sorted_songs = sorted(song_counts.items(), key=lambda x: x[1], reverse=True)
song_count_df = pd.DataFrame(sorted_songs, columns=["Song", "Times Played"])

# Print summary
print("\n=== Song Count Summary (sorted by occurrence) ===")
for song, count in sorted_songs:
    print(f"{song}: {count} times")

# Save both tables to Excel
with pd.ExcelWriter("radiohead_2025_european_tour_setlists.xlsx") as writer:
    df.to_excel(writer, sheet_name="Setlists", index=False)
    song_count_df.to_excel(writer, sheet_name="Song Counts", index=False)

print(f"\n✅ Saved to Excel with 2 sheets:")
print(f"   - 'Setlists': Show-by-show setlists")
print(f"   - 'Song Counts': All {len(song_counts)} songs sorted by frequency")

# === STEP 5: PREDICT SETLIST FOR LONDON NIGHT 4 ===
print("\n" + "="*60)
print("🔮 PREDICTING SETLIST FOR LONDON NIGHT 4")
print("="*60)

# Get London shows specifically
london_shows = {date: songs for date, songs in filtered_setlists.items() if "London" in date}
print(f"\n📍 Found {len(london_shows)} London shows in data")

# Analyze variety patterns across multi-night locations
print("\n📊 Analyzing variety patterns across multi-night stands...")

# Group shows by city
city_shows = {}
for date, songs in filtered_setlists.items():
    city = date.split("(")[1].rstrip(")") if "(" in date else "Unknown"
    if city not in city_shows:
        city_shows[city] = []
    city_shows[city].append(songs)

# Calculate variety metrics for cities with multiple shows
variety_stats = {}
for city, shows in city_shows.items():
    if len(shows) > 1:
        # For each show pair, calculate how many songs changed
        changes = []
        for i in range(len(shows) - 1):
            set1 = set([s for s in shows[i] if s])
            set2 = set([s for s in shows[i+1] if s])
            
            # Songs that were in show i but not in show i+1
            removed = set1 - set2
            # Songs that were in show i+1 but not in show i
            added = set2 - set1
            
            change_count = len(removed) + len(added)
            change_pct = (change_count / len(set1)) * 100 if set1 else 0
            changes.append({
                'removed': len(removed),
                'added': len(added),
                'total_changed': change_count,
                'change_pct': change_pct
            })
        
        variety_stats[city] = {
            'num_shows': len(shows),
            'changes': changes,
            'avg_change_pct': np.mean([c['change_pct'] for c in changes])
        }

# Show variety analysis
for city, stats in variety_stats.items():
    print(f"   {city}: {stats['num_shows']} shows, avg {stats['avg_change_pct']:.1f}% setlist variation between nights")

# Expected setlist length (average from tour)
avg_setlist_length = int(np.mean([len([s for s in songs if s]) for songs in filtered_setlists.values()]))

# Calculate expected variety for London Night 4
if "London" in variety_stats:
    london_variety = variety_stats["London"]["avg_change_pct"]
    print(f"\n🎯 London variety pattern: ~{london_variety:.0f}% of setlist changes between nights")
    
    # How many songs likely to change
    expected_changes = int((london_variety / 100) * avg_setlist_length)
    print(f"   Expected changes for Night 4: ~{expected_changes} songs different from previous nights")
else:
    # Use tour average if no London data
    avg_variety = np.mean([s['avg_change_pct'] for s in variety_stats.values()]) if variety_stats else 25
    expected_changes = int((avg_variety / 100) * avg_setlist_length)
    print(f"\n🎯 Using tour average variety: ~{avg_variety:.0f}% setlist changes")
    print(f"   Expected changes for Night 4: ~{expected_changes} songs")

# Calculate prediction score for each song
total_shows = len(filtered_setlists)
prediction_scores = {}

for song, count in song_counts.items():
    # Base score: frequency across entire tour
    frequency_score = count / total_shows
    
    # Check if song was played in previous London shows
    london_plays = sum(1 for songs in london_shows.values() if song in songs)
    london_frequency = london_plays / len(london_shows) if london_shows else 0
    
    # VARIETY ADJUSTMENT based on multi-night patterns
    # If song was played at ALL London shows, reduce likelihood (they like variety)
    # If song was NOT played in London yet, increase likelihood (fresh for London crowd)
    variety_adjustment = 0
    if london_shows:
        if london_plays == 0:
            # Not played in London yet - BOOST for variety
            variety_adjustment = 0.2
        elif london_plays == len(london_shows):
            # Played at every London show - REDUCE (unless it's a staple)
            if frequency_score >= 0.9:  # Tour staple (90%+ of shows)
                variety_adjustment = 0.0  # Keep staples
            else:
                variety_adjustment = -0.15  # Reduce rotating songs that were played every London night
        else:
            # Played at some London shows - neutral to slight boost
            variety_adjustment = 0.05
    
    # Combined score: 60% overall frequency, 20% London-specific, 20% variety pattern
    prediction_score = (0.6 * frequency_score) + (0.2 * london_frequency) + variety_adjustment
    
    prediction_scores[song] = {
        'score': prediction_score,
        'tour_plays': count,
        'london_plays': london_plays,
        'probability': round(frequency_score * 100, 1),
        'variety_adj': variety_adjustment
    }

# Sort by prediction score
predicted_setlist = sorted(prediction_scores.items(), key=lambda x: x[1]['score'], reverse=True)

print(f"\n📊 Average setlist length: {avg_setlist_length} songs")
print(f"\n🎯 TOP {avg_setlist_length} MOST LIKELY SONGS FOR LONDON NIGHT 4:\n")

predicted_df_data = []
for i, (song, stats) in enumerate(predicted_setlist[:avg_setlist_length], 1):
    london_marker = "🔴" if stats['london_plays'] >= len(london_shows) else "🟢" if stats['london_plays'] == 0 else "🟡"
    print(f"{i:2d}. {london_marker} {song:40s} ({stats['probability']}% - played {stats['tour_plays']}/{total_shows} shows, {stats['london_plays']} in London)")
    
    predicted_df_data.append({
        'Rank': i,
        'Song': song,
        'Probability %': stats['probability'],
        'Tour Plays': stats['tour_plays'],
        'London Plays': stats['london_plays']
    })

print("\n🔴 = Played at ALL London shows (might need a break)")
print("🟡 = Played at SOME London shows (rotating)")  
print("🟢 = NOT played in London yet (fresh for tonight!)")

# Deep cuts / wildcards
print(f"\n🎲 POSSIBLE WILDCARDS (rare songs that might appear):\n")
wildcards = [(song, stats) for song, stats in prediction_scores.items() 
             if stats['tour_plays'] <= 2 and stats['london_plays'] == 0]
wildcards_sorted = sorted(wildcards, key=lambda x: x[1]['tour_plays'], reverse=True)
for song, stats in wildcards_sorted[:10]:
    print(f"   • {song} (played {stats['tour_plays']} times)")

# Save prediction to Excel
predicted_df = pd.DataFrame(predicted_df_data)
with pd.ExcelWriter("radiohead_2025_european_tour_setlists.xlsx", mode='a', if_sheet_exists='replace') as writer:
    predicted_df.to_excel(writer, sheet_name="London Night 4 Prediction", index=False)

print(f"\n✅ Added 'London Night 4 Prediction' sheet to Excel file")

# === STEP 6: CREATE/UPDATE SPOTIFY PLAYLIST ===
print("\n" + "="*60)
print("🎵 CREATING SPOTIFY PLAYLIST")
print("="*60)

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("\n⚠️  Spotify credentials not configured!")
    print("To create a Spotify playlist, you need to:")
    print("1. Copy .env.example to .env")
    print("2. Go to https://developer.spotify.com/dashboard")
    print("3. Create an app and get your Client ID and Client Secret")
    print("4. Add them to your .env file")
    print("\nSkipping Spotify playlist creation...")
else:
    try:
        # Initialize Spotify client
        scope = "playlist-modify-public playlist-modify-private"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=scope
        ))
        
        user_id = sp.current_user()["id"]
        print(f"✅ Authenticated as: {sp.current_user()['display_name']}")
        
        # Get predicted song list
        predicted_songs = [song for song, _ in predicted_setlist[:avg_setlist_length]]
        
        # Search for tracks on Spotify
        print(f"\n🔍 Searching for {len(predicted_songs)} songs on Spotify...")
        track_uris = []
        not_found = []
        
        for song in predicted_songs:
            # Search for the song by Radiohead
            query = f"track:{song} artist:Radiohead"
            results = sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_uris.append(track['uri'])
                print(f"   ✅ {song}")
            else:
                not_found.append(song)
                print(f"   ❌ {song} (not found)")
        
        print(f"\n📊 Found {len(track_uris)}/{len(predicted_songs)} songs on Spotify")
        
        # Check if playlist already exists
        playlists = sp.current_user_playlists()
        existing_playlist = None
        
        for playlist in playlists['items']:
            if playlist['name'] == PLAYLIST_NAME:
                existing_playlist = playlist
                break
        
        if existing_playlist:
            # Update existing playlist
            print(f"\n♻️  Updating existing playlist: {PLAYLIST_NAME}")
            playlist_id = existing_playlist['id']
            
            # Update playlist description with new timestamp
            updated_description = f"Predicted setlist for Radiohead London Night 4 based on 2025 European tour data (12 shows analyzed). Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}. GitHub: https://github.com/DillonBarker/radiohead"
            sp.playlist_change_details(
                playlist_id,
                description=updated_description
            )
            
            # Clear existing tracks
            sp.playlist_replace_items(playlist_id, [])
            
            # Add new tracks
            if track_uris:
                sp.playlist_add_items(playlist_id, track_uris)
            
            print(f"✅ Updated playlist with {len(track_uris)} tracks")
            print(f"🔗 {existing_playlist['external_urls']['spotify']}")
        else:
            # Create new playlist
            print(f"\n🆕 Creating new playlist: {PLAYLIST_NAME}")
            playlist = sp.user_playlist_create(
                user=user_id,
                name=PLAYLIST_NAME,
                public=True,
                description=f"Predicted setlist for Radiohead London Night 4 based on 2025 European tour data (12 shows analyzed). Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}. GitHub: https://github.com/DillonBarker/radiohead"
            )
            
            # Add tracks
            if track_uris:
                sp.playlist_add_items(playlist['id'], track_uris)
            
            print(f"✅ Created playlist with {len(track_uris)} tracks")
            print(f"🔗 {playlist['external_urls']['spotify']}")
        
        if not_found:
            print(f"\n⚠️  Could not find {len(not_found)} songs on Spotify:")
            for song in not_found:
                print(f"   • {song}")
    
    except Exception as e:
        print(f"\n❌ Error creating Spotify playlist: {e}")
        print("Make sure you've set up your Spotify credentials correctly.")

