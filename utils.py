import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
import os
import re

# Constants
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"
BASE_BACKDROP_URL = "https://image.tmdb.org/t/p/w1280/"

def get_session():
    """Create a robust requests session with retries."""
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        "User-Agent": "Lumina-Desktop-App/1.0",
        "Accept": "application/json"
    })
    return session

@st.cache_data(ttl=3600)
def fetch_trending(api_key, safe_search=True):
    """Fetch global trending movies."""
    if not api_key: return []
    session = get_session()
    try:
        url = f"{TMDB_API_BASE_URL}/trending/movie/day"
        # DOUBLE WALL: API DEFENSE
        params = {"api_key": api_key, "language": "en-US", "include_adult": "false"}
        resp = session.get(url, params=params)
        if resp.status_code == 200:
            return _process_results(resp.json().get('results', []), safe_search)
    except: pass
    return []

@st.cache_data(ttl=3600) 
def fetch_smart_candidates(api_key, safe_search, query=None):
    """
    V1.2 Final: High-Recall Multi-Fetch without Genres.
    """
    if not api_key: return []
    session = get_session()
    candidates = {} # Deduplication Dict

    # 1. FETCH 1: DIRECT SEARCH
    if query and query.strip():
        try:
            url = f"{TMDB_API_BASE_URL}/search/movie"
            # DOUBLE WALL: API DEFENSE
            params = {"api_key": api_key, "query": query, "include_adult": "false", "region": "US", "page": 1}
            resp = session.get(url, params=params)
            if resp.status_code == 200:
                for m in resp.json().get('results', []):
                    candidates[m['id']] = m
        except: pass

        # 2. FETCH 2: KEYWORD DISCOVERY
        try:
            words = query.lower().split()
            useful_words = [w for w in words if len(w) > 3]
            keyword_ids = []
            
            for w in useful_words:
                try:
                    k_url = f"{TMDB_API_BASE_URL}/search/keyword"
                    k_resp = session.get(k_url, params={"api_key": api_key, "query": w})
                    if k_resp.status_code == 200:
                        k_data = k_resp.json().get('results', [])
                        if k_data:
                            # Take top 2 keyword IDs per word
                            keyword_ids.extend([str(x['id']) for x in k_data[:2]])
                except: pass
            
            if keyword_ids:
                keywords_pipe = "|".join(keyword_ids[:10])
                disc_url = f"{TMDB_API_BASE_URL}/discover/movie"
                disc_params = {
                    "api_key": api_key, 
                    "with_keywords": keywords_pipe,
                    "language": "en-US",
                    "sort_by": "popularity.desc",
                    "include_adult": "false", # DOUBLE WALL
                    "page": 1
                }
                # Fetch 2 pages of keyword matches
                for p in range(1, 4): # Bumped to 3 pages for better recall
                    disc_params['page'] = p
                    d_resp = session.get(disc_url, params=disc_params)
                    if d_resp.status_code == 200:
                        for m in d_resp.json().get('results', []):
                            if m['id'] not in candidates:
                                candidates[m['id']] = m
        except: pass

    # 3. FETCH 3: DEEP HISTORY (The "Classics" Pool)
    dh_url = f"{TMDB_API_BASE_URL}/discover/movie"
    dh_params = {
        "api_key": api_key,
        "language": "en-US",
        "sort_by": "vote_count.desc",
        "vote_count.gte": "1000",
        "include_adult": "false" # DOUBLE WALL
    }
    
    for p in range(1, 6): # 5 Pages -> 100 Movies
        dh_params['page'] = p
        try:
            dh_resp = session.get(dh_url, params=dh_params)
            if dh_resp.status_code == 200:
                for m in dh_resp.json().get('results', []):
                    if m['id'] not in candidates:
                        candidates[m['id']] = m
        except: pass

    # Filter & Process
    final_candidates = list(candidates.values())
    return _process_results(final_candidates, safe_search)

def _process_results(candidates, safe_search=True):
    final_results = []
    
    # NUCLEAR BLACKLIST (V1.6 Expanded)
    blacklist = [
        "xxx", "sex", "porn", "erotica", "adult", "nude", "nudity", "sensual", "lust", 
        "seductress", "playboy", "penthouse", "hardcore", "softcore", "escort", 
        "prostitute", "orgasm", "kink", "fetish", "desire", "naked", "topless", 
        "erotic", "voyeur", "striptease", "bordello"
    ]
    
    for movie in candidates:
        if not movie.get('overview'): continue
        
        # IRON SHIELD PROTOCOL (V1.6)
        if safe_search:
            # A. Block the "Adult" flag from TMDb
            if movie.get('adult'): continue
            
            # B. Block the "Romance/Erotica" Genre ID (10749)
            # This is the single most important filter for preventing leaks.
            if 10749 in movie.get('genre_ids', []): continue
            
            # C. Keyword Scrubbing (Title & Overview)
            text_to_scan = (movie.get('title', '') + " " + movie.get('overview', '')).lower()
            if any(word in text_to_scan for word in blacklist):
                continue

        movie['poster_path_full'] = f"{BASE_IMAGE_URL}{movie['poster_path']}" if movie.get('poster_path') else None
        movie['backdrop_path_full'] = f"{BASE_BACKDROP_URL}{movie['backdrop_path']}" if movie.get('backdrop_path') else None
        final_results.append(movie)
    return final_results

@st.cache_data(ttl=3600)
def fetch_extended_details(movie_id, api_key):
    """Fetch Credits and Certification."""
    session = get_session()
    url = f"{TMDB_API_BASE_URL}/movie/{movie_id}"
    params = {"api_key": api_key, "append_to_response": "credits,release_dates"}
    
    try:
        r = session.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            cert = "NR"
            release_dates = data.get('release_dates', {}).get('results', [])
            for region in ["IN", "US"]:
                rel_data = next((item for item in release_dates if item["iso_3166_1"] == region), None)
                if rel_data:
                    for rel in rel_data['release_dates']:
                        if rel.get('certification'):
                            cert = rel['certification']
                            break
                if cert != "NR": break
            
            cast = [p['name'] for p in data.get('credits', {}).get('cast', [])[:5]]
            crew = data.get('credits', {}).get('crew', [])
            directors = [p['name'] for p in crew if p['job'] == 'Director']
            
            return {
                "certification": cert,
                "cast": cast,
                "directors": directors,
                "runtime": data.get('runtime', 0),
                "title": data.get('title', ''),
                "tagline": data.get('tagline', ''),
                "overview": data.get('overview', ''),
                "vote_average": data.get('vote_average', 0),
                "imdb_id": data.get('imdb_id', '')
            }
    except Exception: return None
    return None
