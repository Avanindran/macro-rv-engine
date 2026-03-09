import streamlit as st
import sys
import os
import feedparser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#local imports
from src.engine import calculate_rv_signal
from src.llm_processor import extract_macro_signals
from src.vector_store import recall_past_events

# --- Helper Function to Fetch Live News ---
@st.cache_data(ttl=300) # Caches the news for 5 minutes so it doesn't slow down your app
def fetch_live_news():
    try:
        # Pulls live market headlines from Yahoo Finance RSS
        # Tracking SP500, Dow, Nasdaq, and Crude Oil
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC,CL=F&region=US&lang=en-US"
        feed = feedparser.parse(url)
        # Extract the top 10 headlines
        headlines = [entry.title for entry in feed.entries[:10]]
        return headlines if headlines else ["No live news found. API might be blocked."]
    except Exception as e:
        return [f"Error fetching news: {e}"]

# --- UI Setup ---
st.set_page_config(page_title="Macro-RAG Board", layout='wide')

st.title("📈 Macro-RAG Relative Value Engine")
st.markdown("Automated Macroeconomic Tracking and Institutional Memory Retrieval")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📡 Live Market News Feed")
    
    # Let user toggle between live news and manual typing
    input_method = st.radio("Select News Source:", ["Live Feed (Yahoo Finance)", "Manual Entry"], horizontal=True)
    
    if input_method == "Live Feed (Yahoo Finance)":
        live_headlines = fetch_live_news()
        headline_input = st.selectbox("Select a breaking headline to analyze:", live_headlines)
    else:
        headline_input = st.text_area(
            "Enter a Breaking Macro Headline:",
            value="US CPI jumps to 4.5% in February, crushing estimates and triggering a massive selloff in Treasuries."
        )

    if st.button("Extract Insights", type="primary"):

        with st.spinner("Extracting Macro Insights...."):
            structured_data = extract_macro_signals(headline_input)

        st.success("Signals Extracted")
        st.json(structured_data)
        st.divider()

        st.subheader("🧠 Institutional Memory (RAG)")
        with st.spinner("Searching Vector Database for historical precedents..."):
            memory_results = recall_past_events(headline_input)

            if memory_results and memory_results['documents'] and len(memory_results["documents"][0]):

                # Loop through the matches and display them
                for i in range(len(memory_results['documents'][0])):
                    past_doc = memory_results['documents'][0][i]
                    past_meta = memory_results['metadatas'][0][i] 
                    distance = round(memory_results['distances'][0][i], 4)

                    with st.expander(f"Historical Match {i+1} (Math Distance: {distance})", expanded=True):
                        st.write(f"**Past Event:** {past_doc}")
                        st.write(f"**Theme:** {past_meta.get('theme', 'N/A')}")
                        st.write(f"**Action Taken by Desk:** {past_meta.get('action', 'N/A')}")
            else:
                st.info("No highly relevant historical precedents found in the data")

with col2:
    st.subheader("⚙️ RV Engine")

    if 'structured_data' in locals() and structured_data:
        with st.spinner('Calculating Statistical Deviation...'):
            result = calculate_rv_signal(structured_data)

        # 1. Check if the engine specifically threw an error
        if "error" in result:
            st.warning(result["error"])
            
        # 2. THE FIX: Explicitly verify the spread data exists before drawing the UI
        elif "spread_name" in result:
            st.metric(
                label=result['spread_name'],
                value=f"{result['current_value']} bps",
                delta=f"Z-Score: {result['z_score']}",
                delta_color="inverse"
            )

            st.write(f"**Historical Mean:** {result['historical_mean']}")
                
            if result["action_colour"] == "red":
                st.error(f"**Actionable Signal:** {result['trade_idea']}")
            elif result["action_colour"] == "green":
                st.success(f"**Actionable Signal:** {result['trade_idea']}")
            else:
                st.info(f"**Actionable Signal:** {result['trade_idea']}")
                
        # 3. Catch-all for irrelevant news (e.g., tech earnings, random headlines)
        else:
            st.info("This news event does not trigger any tracked macroeconomic spread models.")
    else:
        st.info("Awaiting live news signal to calculate risk implications...")