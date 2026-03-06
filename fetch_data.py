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
# Date range: Fetch content from START_YEAR/START_MONTH to present
START_YEAR = 1990        # Year to start fetching from
START_MONTH = 1          # Month to start fetching from (1-12)

MAX_PAGES_PER_TYPE = 1000 # Max pages to fetch per content type (movies/TV) - 1000 pages = ~20,000 items

# Rate limiting - AGGRESSIVE (risk of throttling but much faster)
REQUESTS_PER_10_SEC = 80  # Double the default (was 40)
DELAY_BETWEEN_REQUESTS = 10.0 / REQUESTS_PER_10_SEC  # 0.125 seconds

# ============= THRESHOLD FUNCTIONS (EDIT THESE) =============
CURRENT_YEAR = datetime.now().year

def get_min_votes_for_year(year):
    """
    Calculate minimum votes based on year.
    Formula: 25 * (CURRENT_YEAR - year + 1)
    
    Examples:
    - 2026: 25 * 1 = 25
    - 2025: 25 * 2 = 50
    - 2024: 25 * 3 = 75
    - 2020: 25 * 7 = 175
    - 2010: 25 * 17 = 425
    - 2006: 25 * 21 = 525
    - 2000: 25 * 27 = 675
    - 1990: 25 * 37 = 925
    """
    if year is None:
        return 25
    if year > CURRENT_YEAR:
        return 25
    return 25 * (CURRENT_YEAR - year + 1)

def get_min_rating_for_year(year):
    """
    Calculate minimum rating based on year to account for rating inflation.
    Formula: 6.0 + (years_old * 0.05)
    
    Examples:
    - 2026: 6.0 + (0 * 0.05) = 6.0
    - 2020: 6.0 + (6 * 0.05) = 6.3
    - 2010: 6.0 + (16 * 0.05) = 6.8
    - 2006: 6.0 + (20 * 0.05) = 7.0
    - 2000: 6.0 + (26 * 0.05) = 7.3
    - 1990: 6.0 + (36 * 0.05) = 7.8
    """
    if year is None or year >= CURRENT_YEAR:
        return 6.0
    years_old = CURRENT_YEAR - year
    return min(10.0, 6.0 + (years_old * 0.05))  # Cap at 10.0

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

print(f"🚀 Starting TMDB data fetch")
print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"📆 Fetching from: {START_YEAR}-{START_MONTH:02d} to present\n")

# Print threshold table for transparency
print("📊 THRESHOLD TABLE:")
print("=" * 60)
print(f"{'Year':<8} {'Min Votes':<12} {'Min Rating':<12}")
print("=" * 60)
for year in range(START_YEAR, CURRENT_YEAR + 1, 5):  # Show every 5 years
    votes = get_min_votes_for_year(year)
    rating = get_min_rating_for_year(year)
    print(f"{year:<8} {votes:<12} {rating:<12.2f}")
print("=" * 60)
print()

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
print("📽️  FETCHING MOVIES (YEAR BY YEAR)...")
print()

all_movies = []

# Fetch year by year with appropriate thresholds
for year in range(START_YEAR, CURRENT_YEAR + 1):
    min_votes = get_min_votes_for_year(year)
    min_rating = get_min_rating_for_year(year)
    
    print(f"🎬 {year}: Min {min_votes} votes, Min {min_rating:.2f} rating", end=" ")
    
    movies_url = (
        f"{API_BASE}/discover/movie"
        f"?sort_by=popularity.desc"
        f"&primary_release_date.gte={year}-01-01"
        f"&primary_release_date.lte={year}-12-31"
        f"&vote_count.gte={min_votes}"
        f"&vote_average.gte={min_rating}"
    )
    
    year_movies = fetch_all_pages(movies_url, max_pages=100)  # Limit per year
    print(f"→ {len(year_movies)} movies")
    all_movies.extend(year_movies)

print(f"\n✅ Total movies across all years: {len(all_movies)}\n")

print("📥 Fetching movie details (credits + providers)...")
movies_data = []

for i, movie in enumerate(all_movies):
    if i % 10 == 0:
        progress_pct = int((i / len(all_movies)) * 100) if len(all_movies) > 0 else 0
        print(f"  Movies: {i}/{len(all_movies)} ({progress_pct}%)", flush=True)
    
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
    
    # Skip Mexican titles
    origin_countries = details.get('origin_country', [])
    production_countries = details.get('production_countries', [])
    
    # Check if Mexico is in origin_country list
    if 'MX' in origin_countries:
        continue
    
    # Check if Mexico is in production_countries
    if any(pc.get('iso_3166_1') == 'MX' for pc in production_countries):
        continue
    
    # Skip Passionflix Amazon channel titles
    if details.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate'):
        provider_names = [p.get('provider_name', '') for p in details['watch/providers']['results']['US']['flatrate']]
        if 'Passionflix Amazon Channel' in provider_names:
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

print(f"✅ Processed {len(movies_data)} movies")

# Deduplicate movies by ID (keep first occurrence)
seen_ids = set()
unique_movies = []
for movie in movies_data:
    if movie['id'] not in seen_ids:
        seen_ids.add(movie['id'])
        unique_movies.append(movie)

movies_data = unique_movies
print(f"✅ After deduplication: {len(movies_data)} unique movies\n")

# ============= PROCESS TV SHOWS =============
print("📺 FETCHING TV SHOWS (YEAR BY YEAR)...")
print()

all_tv_shows = []

# Fetch year by year with appropriate thresholds
for year in range(START_YEAR, CURRENT_YEAR + 1):
    min_votes = get_min_votes_for_year(year)
    min_rating = get_min_rating_for_year(year)
    
    print(f"📺 {year}: Min {min_votes} votes, Min {min_rating:.2f} rating", end=" ")
    
    tv_url = (
        f"{API_BASE}/discover/tv"
        f"?sort_by=popularity.desc"
        f"&first_air_date.gte={year}-01-01"
        f"&first_air_date.lte={year}-12-31"
        f"&vote_count.gte={min_votes}"
        f"&vote_average.gte={min_rating}"
    )
    
    year_tv = fetch_all_pages(tv_url, max_pages=100)  # Limit per year
    print(f"→ {len(year_tv)} shows")
    all_tv_shows.extend(year_tv)

print(f"\n✅ Total TV shows across all years: {len(all_tv_shows)}\n")

print("📥 Fetching TV show details (credits + providers)...")
tv_data = []

for i, show in enumerate(all_tv_shows):
    if i % 10 == 0:
        progress_pct = int((i / len(all_tv_shows)) * 100) if len(all_tv_shows) > 0 else 0
        print(f"  TV Shows: {i}/{len(all_tv_shows)} ({progress_pct}%)", flush=True)
    
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
    
    # Skip Mexican titles
    origin_countries = details.get('origin_country', [])
    production_countries = details.get('production_countries', [])
    
    # Check if Mexico is in origin_country list
    if 'MX' in origin_countries:
        continue
    
    # Check if Mexico is in production_countries
    if any(pc.get('iso_3166_1') == 'MX' for pc in production_countries):
        continue
    
    # Skip Passionflix Amazon channel titles
    if providers.get('flatrate'):
        provider_names = [p.get('provider_name', '') for p in providers['flatrate']]
        if 'Passionflix Amazon Channel' in provider_names:
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

print(f"✅ Processed {len(tv_data)} TV shows")

# Deduplicate TV shows by ID (keep first occurrence)
seen_ids = set()
unique_tv = []
for show in tv_data:
    if show['id'] not in seen_ids:
        seen_ids.add(show['id'])
        unique_tv.append(show)

tv_data = unique_tv
print(f"✅ After deduplication: {len(tv_data)} unique TV shows\n")

# ============= SAVE DATA =============
output_data = {
    'movies': movies_data,
    'tv_shows': tv_data,
    'metadata': {
        'generated_at': datetime.now().isoformat(),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'start_year': START_YEAR,
        'start_month': START_MONTH,
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
