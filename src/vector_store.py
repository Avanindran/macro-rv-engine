import uuid
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# In-memory storage for our statistical vector engine
memory_bank = {
    "documents": [],
    "metadatas": [],
    "ids": []
}

# Initialize the text-to-vector math model
vectorizer = TfidfVectorizer(stop_words='english')

def add_to_memory(article_text: str, metadata: dict):
    """Saves an article and its AI tags into the memory bank"""
    doc_id = str(uuid.uuid4())
    memory_bank["documents"].append(article_text)
    memory_bank["metadatas"].append(metadata)
    memory_bank["ids"].append(doc_id)
    print(f"Saved to memory: {article_text[:40]}...")

def recall_past_events(current_event: str, n_results: int = 2) -> dict:
    """Searches the memory bank using Cosine Similarity"""
    if not memory_bank["documents"]:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    # 1. Mathematically map all historical docs + the new query into vector space
    all_texts = memory_bank["documents"] + [current_event]
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # 2. Separate the historical matrix from our current query vector
    historical_vectors = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    # 3. Calculate Cosine Similarity (The dot product of the normalized vectors)
    similarities = cosine_similarity(query_vector, historical_vectors).flatten()

    # 4. Sort by highest similarity (closest mathematical match)
    top_indices = similarities.argsort()[-n_results:][::-1]

    # 5. Format the output to perfectly match our existing dashboard UI logic
    results = {
        "documents": [[memory_bank["documents"][i] for i in top_indices]],
        "metadatas": [[memory_bank["metadatas"][i] for i in top_indices]],
        "distances": [[round(1.0 - similarities[i], 4) for i in top_indices]] 
    }
    return results


if not memory_bank["documents"]:
    past_events = [
        {"text": "August 2024: US inflation prints at 5.0%, shocking the market. We rotated out of tech equities and bought 2-Year US Treasuries.", "meta": {"theme": "Inflation", "action": "Bought 2Y Treasuries"}},
        {"text": "October 2025: Geopolitical tensions in the Middle East disrupt supply chains. Oil rallies 10%. We went long Brent Crude.", "meta": {"theme": "Geopolitics", "action": "Long Brent"}},
        {"text": "January 2024: CPI data comes in unexpectedly hot. Portfolio took a 2% hit on duration exposure.", "meta": {"theme": "Inflation", "action": "Reduced Duration"}}
    ]

    for event in past_events:
        add_to_memory(event["text"], event["meta"])
# --- Testing the Module ---
if __name__ == "__main__":
    print("Initializing Statistical Memory Bank...\n")

    print(f"\nTotal memories stored: {len(memory_bank['documents'])}\n")

    new_headline = "US CPI jumps to 4.5% in February, crushing estimates and triggering a massive selloff."
    print(f"NEW HEADLINE: {new_headline}")
    print("Searching memory for statistical precedents...\n")
    
    memory_results = recall_past_events(new_headline)
    
    for i in range(len(memory_results['documents'][0])):
        past_doc = memory_results['documents'][0][i]
        past_meta = memory_results['metadatas'][0][i]
        distance = memory_results['distances'][0][i]
        
        print(f"--- Memory Match {i+1} ---")
        print(f"Past Event: {past_doc}")
        print(f"Analyst Action Taken: {past_meta['action']}")
        print(f"Similarity Distance: {distance}\n")