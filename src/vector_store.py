import os
import json
import uuid
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import datetime

# --- File System Setup ---
# Ensure we save the file in your 'data' folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'memory_bank.json')

# Create the data folder if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory storage for our statistical vector engine
memory_bank = {
    "documents": [],
    "metadatas": [],
    "ids": []
}

macro_event_log = []

# Initialize the text-to-vector math model
vectorizer = TfidfVectorizer(stop_words='english')


def log_macro_event(event_json):
    event_json["timestamp"] = datetime.datetime.now().isoformat()
    macro_event_log.append(event_json)



# --- Persistence Functions ---
def save_memory_to_disk():
    """Writes the current memory dictionary to a JSON file."""
    with open(DB_PATH, 'w') as f:
        json.dump(memory_bank, f, indent=4)

def load_memory_from_disk():
    """Loads the memory from JSON. Returns True if successful, False if file doesn't exist."""
    global memory_bank
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            memory_bank = json.load(f)
        return True
    return False

# --- Core Logic ---
def add_to_memory(article_text: str, metadata: dict):
    """Saves an article and its AI tags into the memory bank AND saves to disk."""
    doc_id = str(uuid.uuid4())
    memory_bank["documents"].append(article_text)
    memory_bank["metadatas"].append(metadata)
    memory_bank["ids"].append(doc_id)
    
    # Save to physical file immediately
    save_memory_to_disk()
    print(f"Saved to memory & disk: {article_text[:40]}...")



BLOTTER_PATH = os.path.join(DATA_DIR, 'trade_blotter.json')
trade_blotter = []

def load_trade_blotter():
    global trade_blotter
    if os.path.exists(BLOTTER_PATH):
        with open(BLOTTER_PATH, 'r') as f:
            trade_blotter = json.load(f)

def save_to_trade_blotter(ticker: str, action: str, thesis: str, critique: dict):
    load_trade_blotter() # Ensure we have the latest
    
    trade_record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "action": action.upper(),
        "thesis": thesis,
        "pm_approval": critique.get("approval_status", "Unknown"),
        "pm_critique": critique.get("senior_pm_critique", ""),
        "risk_identified": critique.get("key_risk", "")
    }
    
    trade_blotter.append(trade_record)
    
    with open(BLOTTER_PATH, 'w') as f:
        json.dump(trade_blotter, f, indent=4)

# Run this once on startup to load history
load_trade_blotter()

def recall_past_events(current_event: str, n_results: int = 2) -> dict:
    """Searches the memory bank using Cosine Similarity"""
    if not memory_bank["documents"]:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    all_texts = memory_bank["documents"] + [current_event]
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    historical_vectors = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    similarities = cosine_similarity(query_vector, historical_vectors).flatten()

    top_indices = similarities.argsort()[-n_results:][::-1]

    results = {
        "documents": [[memory_bank["documents"][i] for i in top_indices]],
        "metadatas": [[memory_bank["metadatas"][i] for i in top_indices]],
        "distances": [[round(1.0 - similarities[i], 4) for i in top_indices]] 
    }
    return results

# --- Auto-Load or Initialize ---
# 1. Try to load existing permanent memory
if not load_memory_from_disk():
    # 2. If no file exists, inject the mock data to start, which will auto-create the file
    print("No existing database found. Generating initial seed data...")
    past_events = [
        {"text": "August 2024: US inflation prints at 5.0%, shocking the market. We rotated out of tech equities and bought 2-Year US Treasuries.", "meta": {"theme": "Inflation", "action": "Bought 2Y Treasuries"}},
        {"text": "October 2025: Geopolitical tensions in the Middle East disrupt supply chains. Oil rallies 10%. We went long Brent Crude.", "meta": {"theme": "Geopolitics", "action": "Long Brent"}},
        {"text": "January 2024: CPI data comes in unexpectedly hot. Portfolio took a 2% hit on duration exposure.", "meta": {"theme": "Inflation", "action": "Reduced Duration"}}
    ]

    for event in past_events:
        add_to_memory(event["text"], event["meta"])




# --- Testing the Module ---
if __name__ == "__main__":
    print(f"Total memories stored locally: {len(memory_bank['documents'])}\n")