import streamlit as st
import sys
import os
import feedparser
from collections import Counter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local imports
from src.engine import calculate_rv_signal
from src.llm_processor import extract_macro_signals
from src.vector_store import recall_past_events, add_to_memory, memory_bank

# --- Page Configuration & Bloomberg CSS ---
st.set_page_config(page_title="Macro-RAG Terminal", layout='wide', initial_sidebar_state="collapsed")

# Inject Custom CSS for the "Terminal" look
st.markdown("""
    <style>
    /* Dark mode terminal overrides */
    .stApp {
        background-color: #0d1117;
    }
    h1, h2, h3 {
        color: #ff9d00 !important; /* Bloomberg Orange */
        font-family: 'Courier New', Courier, monospace;
    }
    .stSelectbox label, .stTextArea label, .stRadio label {
        color: #58a6ff !important; /* Tech Blue */
        font-weight: bold;
    }
    .stMetric {
        background-color: #161b22;
        border-left: 4px solid #3fb950;
        padding: 10px;
        border-radius: 5px;
    }
    /* Style the tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff9d00 !important;
        color: black !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Function for Live News ---
@st.cache_data(ttl=300)
def fetch_live_news():
    try:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC,CL=F&region=US&lang=en-US"
        feed = feedparser.parse(url)
        headlines = [entry.title for entry in feed.entries[:15]]
        return headlines if headlines else ["No live news found."]
    except Exception as e:
        return [f"Error fetching news: {e}"]

# --- Header ---
st.title("📟 SCHRODERS MACRO-RAG TERMINAL v1.0")
st.markdown("`SYSTEM STATUS: ONLINE | ASSET CLASS: MULTI | ENGINE: TF-IDF & LLAMA-3`")
st.divider()

# --- Multi-Tab Layout ---
tab1, tab2, tab3 = st.tabs(["LIVE TERMINAL", "MACRO HEATMAP", "INSTITUTIONAL MEMORY"])

# ==========================================
# TAB 1: LIVE TERMINAL (The main engine)
# ==========================================
with tab1:
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("📡 LIVE DATA INGESTION")
        input_method = st.radio("SOURCE:", ["Live Feed (Yahoo Finance)", "Manual Entry"], horizontal=True)
        
        live_headlines = fetch_live_news()
        
        if input_method == "Live Feed (Yahoo Finance)":
            headline_input = st.selectbox("SELECT BREAKING HEADLINE:", live_headlines)
        else:
            headline_input = st.text_area("ENTER CUSTOM HEADLINE:", value="Middle East tensions escalate, causing Brent crude to spike 8% overnight.")

        if st.button("EXECUTE QUANTITATIVE PARSING", type="primary", use_container_width=True):
            
            with st.spinner("LLM Extracting Macro Entities..."):
                st.session_state.structured_data = extract_macro_signals(headline_input)
                st.session_state.current_headline = headline_input
            
            # --- The Schroders "Risk Implication" Chain ---
            st.subheader("MACRO RISK CHAIN")
            driver = st.session_state.structured_data.get('implied_driver', 'Unknown Event')
            asset = st.session_state.structured_data.get('asset_class', 'Unknown Asset')
            
            # Formatting exactly as the problem statement requested
            st.warning(f"**{headline_input}** ➔ *likely {driver}* ➔ **{asset} volatility ↑**")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.json(st.session_state.structured_data)
            
            with col_b:
                st.subheader("RAG PRECEDENTS")
                memory_results = recall_past_events(headline_input)
                if memory_results and memory_results['documents'] and len(memory_results["documents"][0]):
                    for i in range(len(memory_results['documents'][0])):
                        past_doc = memory_results['documents'][0][i]
                        past_meta = memory_results['metadatas'][0][i] 
                        distance = round(memory_results['distances'][0][i], 4)
                        with st.expander(f"Match {i+1} | Sim: {distance}", expanded=True):
                            st.caption(f"Desk Action: {past_meta.get('action', 'N/A')}")
                            st.write(f"*{past_doc}*")

    with col2:
        st.subheader("RELATIVE VALUE (RV) ENGINE")
        
        if 'structured_data' in st.session_state:
            result = calculate_rv_signal(st.session_state.structured_data)
            
            if "error" in result:
                st.info("News event does not trigger a mapped macro spread model.")
            elif "spread_name" in result:
                st.metric(
                    label=f"TARGET SPREAD: {result['spread_name']}",
                    value=f"{result['current_value']} bps",
                    delta=f"Z-Score Deviation: {result['z_score']}",
                    delta_color="inverse"
                )
                st.write(f"`Historical Mean: {result['historical_mean']} bps`")
                
                if result["action_color"] == "red":
                    st.error(f"**TRADE SIGNAL:** {result['trade_idea']}")
                elif result["action_color"] == "green":
                    st.success(f"**TRADE SIGNAL:** {result['trade_idea']}")
                else:
                    st.info(f"**TRADE SIGNAL:** {result['trade_idea']}")
            
            st.divider()
            st.subheader("UPDATE INSTITUTIONAL MEMORY")
            st.markdown("Archive this event to improve future RAG retrieval.")
            
            # DYNAMIC MEMORY UPDATING
            desk_action = st.text_input("Enter Desk Action Taken (e.g., 'Shorted 10Y Treasuries'):")
            if st.button("Archive to Database"):
                if desk_action:
                    meta_to_save = st.session_state.structured_data
                    meta_to_save["action"] = desk_action
                    add_to_memory(st.session_state.current_headline, meta_to_save)
                    st.success("Successfully written to TF-IDF Memory Bank!")
                else:
                    st.error("Please enter a Desk Action before saving.")
        else:
            st.info("Awaiting Signal Execution...")


# ==========================================
# TAB 2: MACRO HEATMAP (Hot vs Cooling)
# ==========================================
with tab2:
    st.subheader("🔥 REAL-TIME THEME TRACKER")
    st.markdown("Monitoring frequency of macro keywords in the live RSS feed to determine 'Hot' vs 'Cooling' themes.")
    
    # Simple logic to simulate tracking themes over time for the hackathon
    live_headlines_str = " ".join(live_headlines).lower()
    themes = {
        "Inflation / Rates": live_headlines_str.count("rate") + live_headlines_str.count("inflation") + live_headlines_str.count("cpi") + live_headlines_str.count("fed"),
        "Geopolitics / War": live_headlines_str.count("war") + live_headlines_str.count("iran") + live_headlines_str.count("russia") + live_headlines_str.count("strike"),
        "Energy / Supply": live_headlines_str.count("oil") + live_headlines_str.count("crude") + live_headlines_str.count("opec") + live_headlines_str.count("energy"),
        "Tech / Equities": live_headlines_str.count("tech") + live_headlines_str.count("apple") + live_headlines_str.count("nvidia") + live_headlines_str.count("earnings")
    }
    
    # Sort themes to find what is "Hot"
    sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
    
    col_x, col_y, col_z = st.columns(3)
    with col_x:
        st.metric(label="HOTTEST THEME", value=sorted_themes[0][0], delta="Spiking Mentions")
    with col_y:
        st.metric(label="WATCHLIST", value=sorted_themes[1][0], delta="Stable", delta_color="off")
    with col_z:
        st.metric(label="COOLING THEME", value=sorted_themes[-1][0], delta="Fading Mentions", delta_color="inverse")
    
    # Bypass Altair and use Streamlit's native UI elements for a custom bar chart
    st.divider()
    st.markdown("### Mentions Volume")
    
    # Find the maximum value to scale the progress bars correctly
    max_mentions = max(themes.values()) if max(themes.values()) > 0 else 1
    
    for theme_name, count in sorted_themes:
        st.write(f"**{theme_name}** ({count} mentions)")
        # Calculate percentage for the progress bar (0.0 to 1.0)
        progress = count / max_mentions
        st.progress(progress)


# ==========================================
# TAB 3: INSTITUTIONAL ARCHIVE
# ==========================================
with tab3:
    st.subheader("🗄️ INTERNAL DATABASE VIEWER")
    st.markdown("Navigate and filter past institutional memory and analyst notes.")
    
    if memory_bank["documents"]:
        # Create a clean format for the UI to display the memory bank
        archive_data = []
        for i in range(len(memory_bank["documents"])):
            archive_data.append({
                "Archived Event": memory_bank["documents"][i],
                "Theme": memory_bank["metadatas"][i].get("theme", "N/A"),
                "Asset Class": memory_bank["metadatas"][i].get("asset_class", "N/A"),
                "Desk Action": memory_bank["metadatas"][i].get("action", "N/A")
            })
        st.dataframe(archive_data, use_container_width=True)
    else:
        st.info("Database is currently empty.")