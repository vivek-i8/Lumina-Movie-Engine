import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import re

class ContentEngine:
    def __init__(self):
        self.model = self._load_model()

    @st.cache_resource
    def _load_model(_self):
        return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def rank_candidates(self, candidates, query):
        """
        Total System Recode: Title Boosting & Lower Threshold.
        """
        if not candidates: return []
        
        # Baseline: Popularity
        if not query or query.strip() == "":
            return sorted(candidates, key=lambda x: x.get('popularity', 0), reverse=True)

        # 1. PREPARE TEXTS (Richer Context)
        texts = [
            f"Movie Title: {movie.get('title', '')}. Year: {movie.get('release_date', '')[:4]}. Plot Summary: {movie.get('overview', '')}" 
            for movie in candidates
        ]
        
        # 2. ENCODE
        query_vec = self.model.encode([query])
        candidate_vecs = self.model.encode(texts)
        
        # 3. COSINE SIMILARITY
        similarity = cosine_similarity(query_vec, candidate_vecs).flatten()
        
        ranked_results = []
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        for idx, movie in enumerate(candidates):
            sim_score = float(similarity[idx])
            title_lower = movie['title'].lower()
            
            # Base Score
            final_score = sim_score
            
            # TITLE BOOSTING (+0.25)
            # If any significant word from query is in title
            if any(w in title_lower for w in query_words if len(w) > 3):
                final_score += 0.10
                
            # Exact Match Super Boost
            if query_lower == title_lower:
                final_score = 2.0
            
            # 4. LOWER THRESHOLD (0.22)
            # Allow slightly looser semantic matches since we have a title boost for relevance
            if final_score < 0.22 and final_score < 1.0:
                continue
                
            movie['match_score'] = final_score
            ranked_results.append(movie)
            
        # Sort
        return sorted(ranked_results, key=lambda x: x['match_score'], reverse=True)


@st.cache_resource
def load_data():
    """
    Robust Data Loader with Self-Healing Embeddings.
    1. Checks for 'tmdb_5000_movies.csv'. If missing -> Stops App.
    2. Checks for 'embeddings.pkl'. 
       - If missing -> Generates them using ContentEngine (Self-Healing).
       - Saves them to disk for next time.
    """
    import pandas as pd
    import pickle
    import os
    
    # 1. CSV CHECK
    if not os.path.exists("tmdb_5000_movies.csv"):
        st.error("🚨 Critical Error: 'tmdb_5000_movies.csv' not found!")
        st.info("ℹ️ Please download the dataset from Kaggle and place it in the project root.")
        st.stop()
        
    df = pd.read_csv("tmdb_5000_movies.csv")
    
    # 2. EMBEDDINGS CHECK (Self-Healing)
    embeddings = None
    if os.path.exists("embeddings.pkl"):
        print("✅ Loading embeddings from disk...")
        with open("embeddings.pkl", "rb") as f:
            embeddings = pickle.load(f)
    else:
        print("⚠️ Embeddings not found. Generating now (Self-Healing)...")
        with st.spinner("⚙️ First-run setup: Generating AI embeddings... (This takes ~1 minute)"):
            # Initialize engine temporarily to use its model
            engine = ContentEngine()
            
            # Prepare Text
            # Naive fillna to prevent errors
            df['overview'] = df['overview'].fillna('')
            df['combined_text'] = df.apply(lambda x: f"Movie: {x['title']}. Plot: {x['overview']}", axis=1)
            
            # Encode
            embeddings = engine.model.encode(df['combined_text'].tolist(), show_progress_bar=True)
            
            # Save
            with open("embeddings.pkl", "wb") as f:
                pickle.dump(embeddings, f)
            print("✅ Embeddings saved successfully.")
            
    return df, embeddings
