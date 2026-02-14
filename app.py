import streamlit as st
import time
import random
from streamlit_lottie import st_lottie
import requests
import os

from utils import fetch_smart_candidates, fetch_extended_details, fetch_trending
from recommender import ContentEngine, load_data

# --- CONFIG & STYLES ---
st.set_page_config(page_title="Lumina", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* 1. BACKGROUND */
    .stApp {
        background: radial-gradient(circle at center, #1e1e2f 0%, #0f0f0f 100%);
        color: #ffffff;
    }
    
    /* 2. GLASSMORPHISM */
    .movie-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .movie-card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
        border-color: rgba(0, 255, 255, 0.5);
        z-index: 10;
    }
    
    /* TEXT STYLES */
    .movie-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: #fff;
        margin-top: 8px;
        height: 40px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    
    .rating-text {
        color: #aaa;
        font-size: 0.75rem;
        margin-top: 4px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    /* 4. BUTTONS */
    .stButton button {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 6px 15px;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(37, 117, 252, 0.5);
        filter: brightness(1.2);
    }
    
    /* CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* CUSTOM HERO TITLE */
    .hero-title {
        font-family: 'Arial Black', sans-serif;
        font-size: 4rem; 
        font-weight: 900;
        letter-spacing: 5px;
        text-transform: uppercase;
        background: -webkit-linear-gradient(top, #fff, #aaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        text-shadow: 0 5px 20px rgba(0,0,0,0.5);
        line-height: 1;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: #ccc;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 5px;
    }
    
    .stTextInput > div > div > input {
        background-color: rgba(0, 0, 0, 0.3);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 30px;
        padding: 10px 20px;
        text-align: center;
        transition: border-color 0.3s;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2575fc;
        box-shadow: 0 0 10px rgba(37, 117, 252, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION & DATA LOADING ---
data_load_state = st.text('Loading data...')
# 1. LOAD DATA (Self-Healing)
try:
    movies_df, embeddings = load_data()
    data_load_state.text("") # Clear loading text
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

@st.cache_resource
def get_engine(): return ContentEngine()
engine = get_engine()

# --- SECURITY ---
try: api_key = st.secrets["TMDB_API_KEY"]
except: api_key = os.getenv("TMDB_API_KEY")

if not api_key:
    st.error("⚠️ Security Error: TMDB_API_KEY not found in secrets.")
    st.stop()

# --- STATE MANAGEMENT ---
if 'search_query' not in st.session_state: st.session_state.search_query = ""
if 'results' not in st.session_state: st.session_state.results = []
if 'trigger_random' not in st.session_state: st.session_state.trigger_random = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # INSTANT RERUN SAFESEARCH
    # Link widget directly to state key for persistence + rerun callback
    safe_search = st.toggle("🛡️ Safe Search", value=True, key="safe_search_toggle")
    
    # STATE WATCHER: INSTANT SYNC FIX
    if "last_safe_search" not in st.session_state:
        st.session_state.last_safe_search = safe_search

    # If the user flipped the switch
    if st.session_state.last_safe_search != safe_search:
        st.session_state.last_safe_search = safe_search
        
        # If there is text in the search bar, re-run the search immediately
        if st.session_state.search_query:
            with st.spinner("Refiltering results..."):
                st.cache_data.clear()
                # Re-fetch candidates with the new safe_search setting
                # Note: Correct arg order is (api_key, safe_search, query)
                candidates = fetch_smart_candidates(api_key, safe_search, st.session_state.search_query)
                if candidates:
                    st.session_state.results = engine.rank_candidates(candidates, st.session_state.search_query)
                else:
                    st.session_state.results = []
        else:
            # If no query, just clear results
            st.session_state.results = []
            st.cache_data.clear()
            
        st.rerun()
    
    st.markdown("---")
    
    # NAVIGATION
    if st.button("🏠 Back to Trending"):
        st.session_state.search_query = ""
        st.session_state.results = []
        st.rerun()
        
    st.write("") # Spacer

    if st.button("🎲 Surprise Me"):
        # THE ELITE 25 LIST
        PROMPTS = [
            "A movie where the setting feels like a character itself",
            "Technicolor dreams and 80s synth-wave vibes",
            "Movies that feel like a warm hug on a rainy Sunday",
            "Something that will make me question my own reality",
            "Visually stunning masterpieces with very little dialogue",
            "A gritty story of redemption in a cold city",
            "Movies about the beauty and terror of the deep ocean",
            "Mind-bending puzzles that require a second viewing",
            "The feeling of being lost in a massive, futuristic metropolis",
            "Small-town mysteries with a dark, supernatural undertone",
            "Heartbreaking stories about the passage of time",
            "High-stakes heist movies with a sophisticated plan",
            "Something to watch when I want to feel inspired to change the world",
            "Isolation in space where silence is the loudest sound",
            "Coming-of-age stories that feel painfully nostalgic",
            "Dark comedies that make you laugh at things you shouldn't",
            "Epic historical journeys across vast, beautiful landscapes",
            "The chaotic energy of a high-pressure kitchen or workplace",
            "Quiet movies about a simple life in the countryside",
            "Cyberpunk aesthetics and the blurred line between man and machine",
            "Psychological thrillers where the protagonist is unreliable",
            "A movie that captures the feeling of a long, lonely road trip",
            "Vibrant animation that feels like a living painting",
            "Stories of unexpected friendship in impossible circumstances",
            "A movie that feels like a slow-burn fever dream"
        ]
        st.session_state.search_query = random.choice(PROMPTS)
        st.session_state.trigger_random = True 
        st.rerun()

# --- HERO ---
col_hero_1, col_hero_2 = st.columns([1, 2])
with col_hero_1:
    lottie_url = "https://assets2.lottiefiles.com/private_files/lf30_bb9bkg1h.json"
    try:
        r = requests.get(lottie_url)
        if r.status_code == 200:
            st_lottie(r.json(), height=160, key="hero_anim")
    except: pass
with col_hero_2:
    st.markdown("<h1 class='hero-title'>LUMINA</h1>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Stop Scrolling. Start Watching.</div>", unsafe_allow_html=True)

# --- SEARCH FORM ---
st.write("") 
st.write("") 

with st.container():
    with st.form(key='search_form'):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_query = st.text_input("Search", value=st.session_state.search_query, placeholder="Describe your mood or a plot...", label_visibility="collapsed")
        with col2:
             submit_btn = st.form_submit_button("🔍")

# --- LOGIC ---
should_search = submit_btn or st.session_state.trigger_random

if should_search:
    # 1. RESET STATE
    st.cache_data.clear() 
    st.session_state.results = []
    
    st.session_state.search_query = user_query
    st.session_state.trigger_random = False 
    
    results_container = st.empty()
    with results_container.container():
        with st.spinner("✨ Lumina is finding your vibe..."):
            # Use SMART FETCH
            candidates = fetch_smart_candidates(api_key, safe_search, st.session_state.search_query)
            
            # 2. LOG POOL SIZE
            print(f"POOL SIZE: {len(candidates)}")
            
            # Rank
            ranked = engine.rank_candidates(candidates, st.session_state.search_query)
            st.session_state.results = ranked

# --- DISPLAY ---
if not st.session_state.results and not st.session_state.search_query:
    st.session_state.results = fetch_trending(api_key, safe_search)
    st.markdown("### 🔥 Trending Globally")
elif not st.session_state.results:
    if safe_search and st.session_state.search_query:
         st.warning("⚠️ High-intensity content filtered. Try toggling Safe Search off if you are looking for specific gritty thrillers.")
    else:
         st.info("No close vibe matches found. Try loosening your filters!")

if st.session_state.results:
    with st.container():
        cols = st.columns(5)
        for i, movie in enumerate(st.session_state.results[:20]): # Show Top 20
            col = cols[i % 5]
            with col:
                poster = movie.get('poster_path_full')
                if poster:
                    st.image(poster, width="stretch")
                else:
                    st.markdown('<div style="width:100%; height:250px; background:rgba(0,0,0,0.5); border-radius:8px;"></div>', unsafe_allow_html=True)
                
                # INFO: Star Rating & Year
                rating = movie.get('vote_average', 0)
                year = movie.get('release_date', 'N/A')[:4]
                
                # RENDER CARD
                st.markdown(f"""
                <div class="movie-card">
                    <div class="movie-title">{movie['title']}</div>
                    <div class="rating-text">
                        <span>⭐ {rating:.1f}</span>
                        <span>•</span>
                        <span>{year}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Details", key=f"btn_{movie['id']}"):
                    @st.dialog("Movie Details", width="large")
                    def show_details():
                        with st.spinner("Loading..."):
                            d = fetch_extended_details(movie['id'], api_key)
                        
                        # BEAUTIFUL DETAILS LAYOUT
                        if d:
                            st.title(d.get('title', movie['title']))
                            if d.get('tagline'):
                                st.caption(f"_{d['tagline']}_")
                            
                            st.divider()
                            
                            c1, c2 = st.columns([1, 2])
                            with c1:
                                if movie.get('poster_path_full'):
                                    st.image(movie['poster_path_full'], width="stretch")
                            with c2:
                                st.markdown("### Synopsis")
                                st.write(d.get('overview', movie.get('overview', '')))
                                
                                st.markdown("---")
                                
                                # METADATA GRID
                                mc1, mc2, mc3 = st.columns(3)
                                with mc1: st.metric("Rating", f"⭐ {d.get('vote_average', rating):.1f}")
                                with mc2: st.metric("Year", year)
                                with mc3: st.metric("Runtime", f"{d.get('runtime', 'N/A')} min")
                            
                            if d.get('cast'):
                                st.info(f"**Starring:** {', '.join(d['cast'])}")
                            
                    show_details()
