#!/usr/bin/env python3
"""
TMDB Data Fetcher - Hourly Updates
Fetches movies and TV shows from the last 365 days
"""

import os
import json
import requests
import time
import sys
from datetime import datetime, timedelta

# Flush output immediately for GitHub Actions visibility
sys.stdout.reconfigure(line_buffering=True)

# ============= CONFIGURATION (EDIT THESE) =============
MIN_VOTES = 1            # Minimum number of reviews/votes
MIN_RATING = 6.0         # Minimum TMDB rating (0-10)

# Date range: Fetch content from START_YEAR/START_MONTH to present
START_YEAR = 2024        # Year to start fetching from (e.g., 2024)
START_MONTH = 2          # Month to start fetching from (1-12, e.g., 2 = February)

MAX_PAGES_PER_TYPE = 500 # Max pages to fetch per content type (movies/TV) - 500 pages = ~10,000 items

# Rate limiting
REQUESTS_PER_10_SEC = 40
DELAY_BETWEEN_REQUESTS = 10.0 / REQUESTS_PER_10_SEC  # 0.25 seconds

# ============= SETUP =============
TMDB_TOKEN = os.environ.get('TMDB_TOKEN')
if not TMDB_TOKEN:
    raise ValueError("TMDB_TOKEN environment variable not set!")

API_BASE = 'https://api.themoviedb.org/3'
HEADERS = {
    'Authorization': f'Bearer {TMDB_TOKEN}',
    'Content-Type': 'application/json'
}

# Calculate date range from START_YEAR/START_MONTH to now
end_date = datetime.now()
start_date = datetime(START_YEAR, START_MONTH, 1)
START_DATE_STR = start_date.strftime('%Y-%m-%d')

print(f"🚀 Starting TMDB data fetch")
print(f"📅 Date range: {START_DATE_STR} to {end_date.strftime('%Y-%m-%d')}")
print(f"⭐ Min rating: {MIN_RATING}, Min votes: {MIN_VOTES}")
print(f"📆 Fetching from: {START_YEAR}-{START_MONTH:02d} to present\n")

# ============= RATE-LIMITED REQUEST =============
last_request_time = 0

def rate_limited_get(url):
    global last_request_time
    
    # Enforce rate limit
    elapsed = time.time() - last_request_time
    if elapsed < DELAY_BETWEEN_REQUESTS:
        time.sleep(DELAY_BETWEEN_REQUESTS - elapsed)
    
    last_request_time = time.time()
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

# ============= FETCH ALL PAGES =============
def fetch_all_pages(url, max_pages=MAX_PAGES_PER_TYPE):
    all_results = []
    page = 1
    total_pages = 1
    
    while page <= min(total_pages, max_pages):
        page_url = f"{url}&page={page}"
        print(f"  Fetching page {page}/{min(total_pages, max_pages)}...")
        
        data = rate_limited_get(page_url)
        
        if 'results' in data:
            all_results.extend(data['results'])
            total_pages = data.get('total_pages', 1)
        
        page += 1
    
    return all_results

# ============= FETCH DETAILS WITH OPTIMIZATION =============
def fetch_item_details(item_id, media_type):
    """Fetch credits and providers in ONE API call using append_to_response"""
    url = f"{API_BASE}/{media_type}/{item_id}?append_to_response=credits,watch/providers"
    return rate_limited_get(url)

# ============= PROCESS MOVIES =============
print("📽️  FETCHING MOVIES...")
movies_url = (
    f"{API_BASE}/discover/movie"
    f"?sort_by=popularity.desc"
    f"&primary_release_date.gte={START_DATE_STR}"
    f"&vote_count.gte={MIN_VOTES}"
    f"&vote_average.gte={MIN_RATING}"
)

movies = fetch_all_pages(movies_url)
print(f"✅ Found {len(movies)} movies\n")

print("📥 Fetching movie details (credits + providers)...")
movies_data = []

for i, movie in enumerate(movies):
    if i % 10 == 0:
        progress_pct = int((i / len(movies)) * 100) if len(movies) > 0 else 0
        print(f"  Movies: {i}/{len(movies)} ({progress_pct}%)", flush=True)
    
    details = fetch_item_details(movie['id'], 'movie')
    
    # Extract director
    director = 'N/A'
    if details.get('credits') and details['credits'].get('crew'):
        director_person = next((p for p in details['credits']['crew'] if p.get('job') == 'Director'), None)
        if director_person:
            director = director_person['name']
    
    # Extract top 3 actors
    actors = 'N/A'
    if details.get('credits') and details['credits'].get('cast'):
        top_actors = [actor['name'] for actor in details['credits']['cast'][:3]]
        if top_actors:
            actors = ', '.join(top_actors)
    
    # Extract streaming providers (US)
    streaming = []
    providers = details.get('watch/providers', {}).get('results', {}).get('US', {})
    if providers.get('flatrate'):
        streaming = [
            {
                'name': p['provider_name'],
                'logo': f"https://image.tmdb.org/t/p/original{p['logo_path']}"
            }
            for p in providers['flatrate']
        ]
    
    # Extract genres
    genres = 'N/A'
    genre_list = []
    if details.get('genres'):
        genre_list = [g['name'] for g in details['genres']]
        if genre_list:
            genres = ', '.join(genre_list)
    
    # Skip if Animation, Music, Documentary, Kids, or Reality genre
    if any(g in ['Animation', 'Music', 'Documentary', 'Kids', 'Reality'] for g in genre_list):
        continue
    
    movies_data.append({
        'id': movie['id'],
        'title': movie['title'],
        'overview': movie.get('overview', ''),
        'poster_path': movie.get('poster_path'),
        'release_date': movie.get('release_date'),
        'year': datetime.strptime(movie['release_date'], '%Y-%m-%d').year if movie.get('release_date') else None,
        'vote_average': movie['vote_average'],
        'vote_count': movie['vote_count'],
        'director': director,
        'actors': actors,
        'genres': genres,
        'providers': {'streaming': streaming},
        'type': 'movie'
    })

print(f"✅ Processed {len(movies_data)} movies\n")

# ============= PROCESS TV SHOWS =============
print("📺 FETCHING TV SHOWS...")
tv_url = (
    f"{API_BASE}/discover/tv"
    f"?sort_by=popularity.desc"
    f"&first_air_date.gte={START_DATE_STR}"
    f"&vote_count.gte={MIN_VOTES}"
    f"&vote_average.gte={MIN_RATING}"
)

tv_shows = fetch_all_pages(tv_url)
print(f"✅ Found {len(tv_shows)} TV shows\n")

print("📥 Fetching TV show details (credits + providers)...")
tv_data = []

for i, show in enumerate(tv_shows):
    if i % 10 == 0:
        progress_pct = int((i / len(tv_shows)) * 100) if len(tv_shows) > 0 else 0
        print(f"  TV Shows: {i}/{len(tv_shows)} ({progress_pct}%)", flush=True)
    
    details = fetch_item_details(show['id'], 'tv')
    
    # Extract top 3 actors
    actors = 'N/A'
    if details.get('credits') and details['credits'].get('cast'):
        top_actors = [actor['name'] for actor in details['credits']['cast'][:3]]
        if top_actors:
            actors = ', '.join(top_actors)
    
    # Extract streaming providers (US)
    streaming = []
    providers = details.get('watch/providers', {}).get('results', {}).get('US', {})
    if providers.get('flatrate'):
        streaming = [
            {
                'name': p['provider_name'],
                'logo': f"https://image.tmdb.org/t/p/original{p['logo_path']}"
            }
            for p in providers['flatrate']
        ]
    
    # Extract genres
    genres = 'N/A'
    genre_list = []
    if details.get('genres'):
        genre_list = [g['name'] for g in details['genres']]
        if genre_list:
            genres = ', '.join(genre_list)
    
    # Skip if Animation, Music, Documentary, Kids, or Reality genre
    if any(g in ['Animation', 'Music', 'Documentary', 'Kids', 'Reality'] for g in genre_list):
        continue
    
    # Extract TV show status and episodes
    tv_status_info = {
        'status': details.get('status', 'N/A'),
        'in_production': details.get('in_production', False),
        'last_episode': None,
        'next_episode': None
    }
    
    if details.get('last_episode_to_air'):
        last_ep = details['last_episode_to_air']
        tv_status_info['last_episode'] = {
            'season': last_ep.get('season_number'),
            'episode': last_ep.get('episode_number'),
            'air_date': last_ep.get('air_date'),
            'name': last_ep.get('name')
        }
    
    if details.get('next_episode_to_air'):
        next_ep = details['next_episode_to_air']
        tv_status_info['next_episode'] = {
            'season': next_ep.get('season_number'),
            'episode': next_ep.get('episode_number'),
            'air_date': next_ep.get('air_date'),
            'name': next_ep.get('name')
        }
    
    tv_data.append({
        'id': show['id'],
        'title': show['name'],
        'overview': show.get('overview', ''),
        'poster_path': show.get('poster_path'),
        'first_air_date': show.get('first_air_date'),
        'year': datetime.strptime(show['first_air_date'], '%Y-%m-%d').year if show.get('first_air_date') else None,
        'vote_average': show['vote_average'],
        'vote_count': show['vote_count'],
        'actors': actors,
        'genres': genres,
        'tv_status': tv_status_info,
        'providers': {'streaming': streaming},
        'type': 'tv'
    })

print(f"✅ Processed {len(tv_data)} TV shows\n")

# ============= SAVE DATA =============
output_data = {
    'movies': movies_data,
    'tv_shows': tv_data,
    'metadata': {
        'generated_at': datetime.now().isoformat(),
        'start_date': START_DATE_STR,
        'end_date': end_date.strftime('%Y-%m-%d'),
        'start_year': START_YEAR,
        'start_month': START_MONTH,
        'min_votes': MIN_VOTES,
        'min_rating': MIN_RATING,
        'total_movies': len(movies_data),
        'total_tv': len(tv_data),
        'total_items': len(movies_data) + len(tv_data)
    }
}

# Write to data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

file_size_mb = os.path.getsize('data.json') / 1024 / 1024

print("=" * 50)
print("✅ SUCCESS!")
print(f"📊 Movies: {len(movies_data)}")
print(f"📊 TV Shows: {len(tv_data)}")
print(f"📊 Total: {len(movies_data) + len(tv_data)}")
print(f"💾 Saved to: data.json")
print(f"📦 File size: {file_size_mb:.2f} MB")
print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)
