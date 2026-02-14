
<div align="center">

# 🎬 Lumina: Discovery Engine
**A Hybrid Semantic Movie Recommender built with Dual-Pass Vector Logic.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![BERT](https://img.shields.io/badge/Sentence--Transformers-BERT-orange?style=for-the-badge)](https://www.sbert.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

*(Local development version. Web deployment in progress.)*

</div>

## 📖 Table of Contents
* [What the Project Does](#-what-the-project-does)
* [Why It's Useful](#-why-its-useful)
* [Engineering Highlights](#-engineering-highlights)
* [How to Get Started](#-how-to-get-started)
* [Who Maintains This](#-who-maintains-this)

---

## 🚀 What the Project Does
Lumina is a specialized discovery engine that moves beyond simple keyword matching. By mapping movie metadata into a high-dimensional vector space using **Sentence-BERT**, it identifies thematic and emotional connections, solving the "semantic gap" found in traditional search engines.

---

## 💡 Why It's Useful
Most recommenders rely on "Users who liked X also liked Y" (Collaborative Filtering), which fails for new users or niche tastes. Lumina uses **Content-Based Semantic Filtering**:

* **Thematic Search:** Find movies by describing a "vibe" (e.g., "space exploration with a lonely atmosphere").
* **Hybrid Logic:** Combines deep learning embeddings with deterministic title-boosting.
* **Cold-Start Ready:** Works instantly without needing historical user data.

---

## 🧠 Engineering Highlights

### 🛠️ Core Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Vector Engine** | `all-MiniLM-L6-v2` | Maps text metadata to 384D vector space. |
| **Relevancy Metric** | `Cosine Similarity` | Measures semantic distance. |
| **Backend** | `Python / Streamlit` | Handles real-time inference and state management. |
| **Data Hydration** | `TMDB API` | Asynchronous fetching of rich media (Posters/Trailers). |

> **Note on Self-Healing:** To keep the repository lightweight, vector embeddings are generated on the first run. If you see a "First-run setup" message, please allow ~60 seconds for the engine to initialize the high-dimensional space.

### 🎯 The "Dual-Pass" Strategy
To ensure high precision, Lumina implements a two-stage retrieval pipeline:
1. **Semantic Pass:** Broad retrieval via S-BERT embeddings to find conceptual matches.
2. **Deterministic Pass:** A title-boost layer that ensures exact keyword matches appear at the top, preventing "AI hallucination" in search results.

---

## 🛠️ How to Get Started

### Prerequisites
* Python 3.9+
* A TMDB API Key ([Get one here](https://www.themoviedb.org/documentation/api))

### Installation

1. **Clone the Repository**
    ```bash
    git clone [https://github.com/vivek-i8/Lumina-Movie-Engine.git](https://github.com/vivek-i8/Lumina-Movie-Engine.git)
    cd Lumina-Movie-Engine
    ```

2. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Secrets**
    Create a `.streamlit/secrets.toml` file in the root directory:
    ```toml
    TMDB_API_KEY = "your_tmdb_api_key_here"
    ```

4. **Add Dataset**
    Download the [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) and place the `tmdb_5000_movies.csv` in the root directory.

5. **Run the Application**
    ```bash
    streamlit run app.py
    ```

---

## 🤝 Where to Get Help
* **Documentation:** See the `recommender.py` comments for detailed logic on the vector transformations.
* **Issues:** Please use the GitHub Issues tab for bug reports or feature requests.

<div align="center">

### 🛠️ Core Competencies Demonstrated
**NLP • Vector Search • Information Retrieval • System Design**

**Maintained by Vivek Kumawat**
*Open for Internships and Technical Collaborations.*

</div>