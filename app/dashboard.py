import streamlit as st
import sys
import os
import feedparser
from collections import Counter
import yfinance as yf
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ==========================================
# LOCAL IMPORTS 
# ==========================================
from src.core.engine import calculate_rv_signal
from src.ai.llm_processor import chat_with_macro_assistant, extract_macro_signals, critique_trade_thesis, generate_morning_thesis, generate_institutional_trades
from src.memory.vector_store import recall_past_events, add_to_memory, memory_bank, save_to_trade_blotter, trade_blotter
from src.graphs.macro_graph import propagate_macro_shock, generate_risk_implications
from src.memory.theme_tracker import update_theme
from src.graphs.impact_matrix import generate_market_impacts
from src.core.regime_classifier import classify_regime
from src.ai.ai_trade_engine import generate_and_score_trades



# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Macro-RAG Terminal", layout='wide', initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    /* Force pitch black on the main app container */
    .stAppViewContainer {
        background-color: #000000;
    }
    
    /* Clean up headers */
    h1, h2, h3, h4 { 
        color: #ff9d00 !important; 
        font-family: 'Arial', sans-serif; 
        text-transform: uppercase; 
        font-weight: 700;
    }

    /* Style the bordered containers (st.container(border=True)) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0d1117;
        border: 1px solid #30363d !important;
    }

    /* Fix the Metric values for terminal readability */
    [data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace !important;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# Data 
# ==========================================
@st.cache_data(ttl=300)
def fetch_live_news():
    try:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC,CL=F&region=US&lang=en-US"
        feed = feedparser.parse(url)
        news_dict = {entry.title: entry.link for entry in feed.entries[:20]} 
        return news_dict if news_dict else {"No live news found.": "#"}
    except Exception as e:
        return {f"Error fetching news: {e}": "#"}

@st.cache_data(ttl=600)
def fetch_macro_overview():
    tickers = {
        "S&P 500": "^GSPC", # Added for true risk sentiment
        "US 10Y Yield": "^TNX", 
        "US 2Y Yield": "^IRX", 
        "EUR/USD": "EURUSD=X", 
        "DXY (Dollar)": "DX-Y.NYB",
        "Crude Oil": "CL=F", 
        "Gold": "GC=F"
    }
    data = {}
    try:
        for name, ticker in tickers.items():
            # Pull 6 months of data
            hist = yf.Ticker(ticker).history(period="6mo")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev_daily = hist['Close'].iloc[-2]
                prev_6mo = hist['Close'].iloc[0] # Price 6 months ago
                
                daily_pct = ((current - prev_daily) / prev_daily) * 100
                six_mo_pct = ((current - prev_6mo) / prev_6mo) * 100
                
                data[name] = {
                    "val": round(current, 3), 
                    "change": round(daily_pct, 2), # Keep for the header strip
                    "6mo_change": round(six_mo_pct, 2) # New institutional metric
                }
    except Exception as e:
        pass
    return data

@st.cache_data(ttl=60)
def fetch_chart_data(ticker, period, interval):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_correlation_matrix():
    #fetch macro common macro proxies
    tickers = ['SPY', 'TLT', 'GLD', 'USO', 'UUP']
    try:
        df = yf.download(tickers, period ="6mo", interval = "1d")['Close']

        returns = df.pct_change().dropna()
        corr_matrix = returns.corr().round(2)
        return corr_matrix
    except Exception as e:
        return None
    
# Fetch background data
macro_data = fetch_macro_overview()
live_news_dict = fetch_live_news()

# ==========================================
# HEADER 
# ==========================================
st.title("MACROSYNTHETIX TERMINAL (PROTOTYPE)")
st.markdown("**SYSTEM STATUS:** ONLINE | **ASSET CLASS:** MULTI | **ENGINE:** TF-IDF, LLAMA-3")
st.write("")

if macro_data:
    cols = st.columns(len(macro_data))
    for i, (name, metrics) in enumerate(macro_data.items()):
        with cols[i]:
            color = "#3fb950" if metrics['change'] > 0 else "#f85149"
            st.markdown(f"""
            <div style="border: 1px solid #30363d; border-radius: 6px; padding: 15px; text-align: center; background-color: #0d1117; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <p style="margin: 0; color: #8b949e; font-size: 12px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">{name}</p>
                <h3 style="margin: 5px 0; color: #ffffff; font-family: 'Courier New', monospace; font-size: 22px;">{metrics['val']}</h3>
                <p style="margin: 0; font-size: 13px; font-weight: bold; color: {color};">
                    {'+' if metrics['change'] > 0 else ''}{metrics['change']}%
                </p>
            </div>
            """, unsafe_allow_html=True)

st.write("")
st.write("")

# ==========================================
# TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "MORNING BRIEFING & NEWS",
    "MACRO REGIME & RISKS",
    "EXECUTION TERMINAL",
    "MACRO AI CO-PILOT",
    "INSTITUTIONAL ARCHIVE"
])

# ==========================================
# TAB 1: MORNING BRIEFING & NEWS
# ==========================================
with tab1:
    
    # --- AUTOMATED BATCH INGESTION ---
    with st.container(border=True):
        st.subheader("Automated Theme Ingestion")
        st.markdown("Select a lookback horizon. The AI will process non-duplicate news and track themes into Institutional Memory.")
        
        col_slider, col_btn = st.columns([3, 1])
        with col_slider:
            lookback_hours = st.slider("Lookback Horizon (Hours):", min_value=1, max_value=48, value=24)
        with col_btn:
            st.write("") 
            if st.button("Auto-Ingest to Memory", type="primary", use_container_width=True):
                with st.spinner(f"Batch processing last {lookback_hours} hours of news..."):
                    headlines_to_process = list(live_news_dict.keys())[:5] 
                    existing_docs = memory_bank.get("documents", [])
                    added_count = 0
                    
                    for hl in headlines_to_process:
                        if hl not in existing_docs:
                            res = extract_macro_signals(hl)
                            meta = res
                            meta["action"] = "AUTO-LOGGED BY BATCH SCRIPT"
                            add_to_memory(hl, meta)
                            added_count += 1
                            
                    st.success(f"Processed {added_count} NEW events into the RAG Database. ({len(headlines_to_process) - added_count} duplicates skipped).")

    # --- MORNING BRIEFING COMPONENT ---
    with st.container(border=True):
        st.subheader("PM Morning Synthesis")
        st.markdown("Ingest overnight feeds to formulate structural daily thesis.")
        
        if st.button("Generate Morning Macro Briefing"):
            with st.spinner("Synthesizing news feed and live pricing..."):
                headlines = list(live_news_dict.keys())
                thesis = generate_morning_thesis(headlines, macro_data)
                st.session_state.morning_thesis = thesis
                
        if 'morning_thesis' in st.session_state:
            t = st.session_state.morning_thesis
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("DOMINANT THEME", t.get('dominant_theme', 'N/A'))
                st.metric("IMPLIED REGIME", t.get('market_regime', 'N/A'))
                st.error(f"TAIL RISK: {t.get('key_tail_risk', 'N/A')}")
            with c2:
                st.info(f"CORE THESIS:\n\n{t.get('core_thesis', 'N/A')}")
                st.success(f"HIGH CONVICTION CALL:\n\n{t.get('high_conviction_call', 'N/A')}")

    # --- INDIVIDUAL EVENT INGESTION ---
    col1, col2 = st.columns([1.5, 1])

    with col1:
        with st.container(border=True):
            st.subheader("EVENT INGESTION")
            input_method = st.radio("SOURCE:", ["Live Feed (Yahoo Finance)", "Manual Entry"], horizontal=True)
            
            if input_method == "Live Feed (Yahoo Finance)":
                headline_input = st.selectbox("SELECT BREAKING HEADLINE:", list(live_news_dict.keys()))
                article_url = live_news_dict[headline_input]
                st.markdown(f"*[Read Source Article]({article_url})*")
            else:
                headline_input = st.text_area("ENTER CUSTOM HEADLINE:", value="Middle East tensions escalate, causing Brent crude to spike 8% overnight.")

            if st.button("INGEST & ANALYZE EVENT", use_container_width=True):
                with st.spinner("LLM Extracting Macro Entities..."):
                    data = extract_macro_signals(headline_input)
                    st.session_state.structured_data = data
                    st.session_state.current_headline = headline_input

                    node = data.get("macro_node")
                    direction = data.get("direction")
                    theme = data.get("theme")

                    update_theme(theme)
                    st.session_state.propagation = propagate_macro_shock(node, direction)
                    st.session_state.risks = generate_risk_implications(node, direction)
                    st.session_state.market_impacts = generate_market_impacts(node)
                
        if 'structured_data' in st.session_state:
            with st.container(border=True):
                st.subheader("CROSS-ASSET IMPLICATIONS")
                driver = st.session_state.structured_data.get('implied_driver', 'Unknown Event')
                asset = st.session_state.structured_data.get('asset_class', 'Unknown Asset')
                primary = st.session_state.structured_data.get('primary_impact', 'Unknown Primary')
                secondary = st.session_state.structured_data.get('secondary_spillover', 'Unknown Secondary')
                rationale = st.session_state.structured_data.get('rationale', 'No rationale provided.')

                st.warning(f"{st.session_state.current_headline} ➔ likely {driver} ➔ {asset} volatility ↑")
                
                c1, c2, c3, c4, c5 = st.columns([2, 0.5, 2, 0.5, 2])
                with c1: st.info(f"CATALYST\n\n{driver}")
                with c2: st.markdown("<h3 style='text-align: center; color: #58a6ff;'>➔</h3>", unsafe_allow_html=True)
                with c3: st.warning(f"1st ORDER\n\n{primary}")
                with c4: st.markdown("<h3 style='text-align: center; color: #58a6ff;'>➔</h3>", unsafe_allow_html=True)
                with c5: st.error(f"2nd ORDER\n\n{secondary}")
                st.caption(f"Macro Rationale: {rationale}")
        
        if "propagation" in st.session_state:
            with st.container(border=True):
                st.subheader("MACRO PROPAGATION ENGINE")
                for p in st.session_state.propagation:
                    st.write(f"**{p['source']}** ➔ **{p['target']}** ({p['effect']})")

    with col2:
        with st.container(border=True):
            st.subheader("SUGGESTED RELATIVE VALUE TRADE")
            if 'structured_data' in st.session_state:
                result = calculate_rv_signal(st.session_state.structured_data)
                if "error" in result:
                    st.info("News event does not trigger a mapped macro spread model.")
                elif "spread_name" in result:
                    st.metric(
                        label=f"TARGET: {result['spread_name']}",
                        value=f"{result['current_value']} bps",
                        delta=f"Z-Score Deviation: {result['z_score']}",
                        delta_color="inverse"
                    )
                    st.write(f"Historical Mean: {result['historical_mean']} bps")
                    
                    if result["action_color"] == "red":
                        st.error(f"TRADE SIGNAL: {result['trade_idea']}")
                    elif result["action_color"] == "green":
                        st.success(f"TRADE SIGNAL: {result['trade_idea']}")
                    else:
                        st.info(f"TRADE SIGNAL: {result['trade_idea']}")
            else:
                st.info("Awaiting Signal Execution...")

            with st.container(border=True):
                        st.subheader("RAG PRECEDENTS")
                        if 'current_headline' in st.session_state:
                            # The backend pulls the top 10 for the LLM's deep context
                            memory_results = recall_past_events(st.session_state.current_headline)
                            
                            if memory_results and memory_results['documents'] and len(memory_results["documents"][0]) > 0:
                                
                                display_count = min(2, len(memory_results['documents'][0]))
                                
                                for i in range(display_count):
                                    past_doc = memory_results['documents'][0][i]
                                    past_meta = memory_results['metadatas'][0][i] 
                                    distance = memory_results['distances'][0][i]
                                    
                                    with st.expander(f"Archived Match {i+1} | Math Distance: {distance}"):
                                        st.caption(f"Desk Action: {past_meta.get('action', 'N/A')}")
                                        st.write(f"*{past_doc}*")
                                        
        if "market_impacts" in st.session_state:
            with st.container(border=True):
                st.subheader("CROSS-ASSET IMPACT MATRIX")
                impacts = st.session_state.market_impacts
                for asset, direction in impacts.items():
                    if direction == "bullish":
                        st.success(f"{asset.upper()} ➔ BULLISH")
                    elif direction == "bearish":
                        st.error(f"{asset.upper()} ➔ BEARISH")
                        
# --- LIVE NEWS SCREENER MATRIX (INFORMATION OVERLOAD FIX) ---
        with st.container(border=True):
            st.subheader("24H MACRO EVENT SCREENER")
            st.markdown("Filter ingested global headlines by extracted macroeconomic features.")
            
            # Pull data directly from the RAG memory bank
            if memory_bank.get("documents"):
                screener_data = []
                for doc, meta in zip(memory_bank["documents"], memory_bank["metadatas"]):
                    # Look up the URL from the live news dictionary, fallback if manual
                    article_url = live_news_dict.get(doc, "https://finance.yahoo.com") if doc in live_news_dict else None
                    
                    screener_data.append({
                        "Headline": doc,
                        "Country": meta.get("country", "Global").upper(),
                        "Asset Class": meta.get("asset_class", "MULTI").upper(),
                        "Theme": meta.get("theme", "N/A"),
                        "Impact": meta.get("direction", "NEUTRAL").upper(),
                        "Source Link": article_url
                    })
                
                import pandas as pd
                df_screener = pd.DataFrame(screener_data)
                
                # Streamlit 1.32+ native column filtering and clickable links
                st.dataframe(
                    df_screener,
                    use_container_width=True,
                    hide_index=True,
                    height=250, # Keeps it compact
                    column_config={
                        "Source Link": st.column_config.LinkColumn(
                            "Source Link", 
                            help="Click to read the original article",
                            display_text="Read Article 🔗" # Makes it look clean instead of a raw ugly URL string
                        )
                    }
                )
            else:
                st.info("No structured events in memory. Run 'Auto-Ingest' above to populate the screener.")

# ==========================================
# TAB 2: MACRO REGIME & RISKS
# ==========================================
with tab2:
    st.subheader("MACRO REGIME MONITOR (6-MONTH STRUCTURAL)")

    growth_signal = macro_data.get("US 10Y Yield", {}).get("6mo_change", 0.0)
    inflation_signal = macro_data.get("Crude Oil", {}).get("6mo_change", 0.0)
    regime = classify_regime(growth_signal, inflation_signal)

    col_reg1, col_reg2 = st.columns([1,1])
    with col_reg1:
        st.metric("CURRENT MACRO REGIME", regime, help="Calculated using 6-Month Rolling Momentum")
    with col_reg2:
        st.caption("Structural Signals (6-Month Momentum):")
        st.code(f"Growth Proxy (10Y): {growth_signal}%\nInflation Proxy (Oil): {inflation_signal}%")

    with st.container(border=True):
        st.subheader("Risk Engine")
        if "risks" in st.session_state:
            for r in st.session_state.risks:
                st.warning(r)
        else:
            st.info("No risk signals detected yet.")

    with st.container(border=True):
        st.subheader("Multi-Asset Correlation Matrix")
        st.markdown("Monitoring the daily shifting relationships between Equities, Treasuries, Commodities, and FX.")
        corr_matrix = fetch_correlation_matrix()

        if corr_matrix is not None:
            fig_heatmap = go.Figure(data=go.Heatmap(
                z = corr_matrix.values,
                x = corr_matrix.columns,
                y = corr_matrix.index,
                colorscale = "RdBu",
                zmin = -1, zmax = 1,
                text = corr_matrix.values,
                texttemplate = "%{text}",
                showscale = True
            ))

            fig_heatmap.update_layout(
                template = 'plotly_dark',
                plot_bgcolor= 'rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0),
                height=350,
                xaxis_title="",
                yaxis_title="",
            )

            st.plotly_chart(fig_heatmap, use_container_width= True)
        else:
            st.error("Correlation data currently unavailable")    

    with st.container(border=True):
            st.subheader("GLOBAL MACRO CAUSAL GRAPH")
            st.markdown("Visualizing cross-asset implications and directional effects.")
            
            if "propagation" in st.session_state and st.session_state.propagation:
                G = nx.DiGraph()
                edge_labels = {}
                
                for p in st.session_state.propagation:
                    source = p["source"]
                    target = p["target"]
                    effect = p["effect"].upper() 
                    
                    G.add_edge(source, target)
                    edge_labels[(source, target)] = effect
                
                fig_col, _ = st.columns([2, 1])
                with fig_col:
                    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#000000')
                    ax.set_facecolor('#000000')
                    
                    pos = nx.spring_layout(G, k=2.0, seed=42) 
                    
                    nx.draw_networkx_nodes(
                        G, pos, ax=ax, 
                        node_color='#0d1117', 
                        edgecolors='#ff9d00', 
                        node_size=3000, 
                        linewidths=2
                    )
                    
                    nx.draw_networkx_edges(
                        G, pos, ax=ax, 
                        edge_color='#58a6ff', 
                        arrows=True, 
                        arrowsize=20, 
                        width=2,
                        connectionstyle="arc3,rad=0.1" 
                    )
                    
                    nx.draw_networkx_labels(
                        G, pos, ax=ax, 
                        font_size=10, 
                        font_color='white', 
                        font_family='sans-serif', 
                        font_weight='bold'
                    )
                    
                    nx.draw_networkx_edge_labels(
                        G, pos, ax=ax,
                        edge_labels=edge_labels, 
                        font_color='#f85149', 
                        font_size=9, 
                        font_weight='bold',
                        bbox=dict(facecolor='#000000', edgecolor='none', pad=0) 
                    )
                    
                    ax.axis('off')
                    st.pyplot(fig)
            else:
                st.info("Awaiting macro shock propagation.")
        

    with st.container(border=True):
            col_reg1, col_reg2, col_reg3 = st.columns(3)
            
            sp500_6mo = macro_data.get("S&P 500", {}).get("6mo_change", 0.0)
            is_risk_on = sp500_6mo > 0 
            
            curr_2y = macro_data.get("US 2Y Yield", {}).get("val", 0.0)
            curr_10y = macro_data.get("US 10Y Yield", {}).get("val", 0.0)
            curve_inverted = curr_2y > curr_10y and curr_10y != 0.0
            
            dxy_6mo = macro_data.get("DXY (Dollar)", {}).get("6mo_change", 0.0)
            
            with col_reg1:
                st.markdown("### Market Sentiment")
                if is_risk_on: 
                    st.success(f"RISK-ON (+{sp500_6mo}% 6mo)")
                else: 
                    st.error(f"RISK-OFF ({sp500_6mo}% 6mo)")
                    
            with col_reg2:
                st.markdown("### Yield Curve Shape")
                if curve_inverted: 
                    st.error(f"INVERTED ({curr_2y} > {curr_10y})")
                else: 
                    st.success(f"NORMAL ({curr_10y} > {curr_2y})")
                    
            with col_reg3:
                st.markdown("### Dominant Dollar (DXY)")
                if dxy_6mo > 0: 
                    st.warning(f"STRONG DOLLAR (+{dxy_6mo}% 6mo)")
                else: 
                    st.info(f"WEAK DOLLAR ({dxy_6mo}% 6mo)")

# ==========================================
# TAB 3: EXECUTION TERMINAL 
# ==========================================
with tab3:
    st.subheader("TERMINAL CHARTING & TRADE EXECUTION")
    st.markdown("Pull live asset data, formulate a thesis, and submit to the AI Portfolio Manager for Red-Teaming.")
    
    chart_col, execution_col = st.columns([2, 1])
    
    with chart_col:
        with st.container(border=True):
            st.markdown("### Interactive Charting and Asset Risk")
            
            with st.form("chart_form"):
                c_input1, c_input2, c_input3 = st.columns(3)
                with c_input1:
                    target_ticker = st.text_input("Enter Asset Ticker (e.g., AAPL, CL=F):", value="CL=F")
                with c_input2:
                    time_period = st.selectbox("Time Horizon:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
                with c_input3:
                    chart_interval = st.selectbox("Interval:", ["1d", "1wk", "1mo"], index=0)
                
                submit_chart = st.form_submit_button("Load Chart Data")
                
            if target_ticker:
                with st.spinner("Fetching Market Data..."):
                    df = fetch_chart_data(target_ticker, time_period, chart_interval)
                    
                    if df is not None and not df.empty:
                        
                        daily_returns = df['Close'].pct_change().dropna()
                        var_95 = np.percentile(daily_returns, 5) * 100
                        volatility = daily_returns.std() * np.sqrt(252) * 100

                        #risk metrics
                        r1, r2, r3 = st.columns(3)
                        r1.metric("1-Day 95% VaR", f"{var_95:.2f}%", help="In 95% of trading days, daily losses will not exceed this percentage.")
                        r2.metric("Annualized Volatility", f"{volatility:.2f}%")
                        r3.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}")
                        
                        st.divider()

                        #charting
                        fig = go.Figure(data=[go.Candlestick(
                            x=df.index, open=df["Open"], high=df["High"],
                            low=df["Low"], close=df["Close"], name=target_ticker,
                            increasing_line_color='#3fb950', decreasing_line_color='#f85149'
                        )])

                        fig.update_layout(
                            title=f"{target_ticker} Price Action", xaxis_title="Date", yaxis_title="Price",
                            template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            xaxis_rangeslider_visible=False, height=500
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("No data found. Please check the ticker symbol.")

    with execution_col:
        with st.container(border=True):
            st.markdown("### Trade Blotter Submission")
            with st.form("blotter_form"):
                trade_action = st.radio("Action:", ["Buy / Long", "Sell / Short"], horizontal=True)
                trader_thesis = st.text_area("Write your Macro Thesis:", height=150, 
                                             placeholder="E.g., I am going long Oil because the DXY is cooling and Middle East supply is constrained.")
                submit_trade = st.form_submit_button("Submit to AI Risk Manager", type="primary", use_container_width=True)
            
            if submit_trade:
                if trader_thesis and target_ticker:
                    with st.spinner("Senior AI PM is reviewing your thesis..."):
                        critique = critique_trade_thesis(target_ticker, trade_action, trader_thesis, macro_data)
                        
                        st.divider()
                        st.markdown("#### AI PM Feedback")
                        
                        status = critique.get("approval_status", "Warning")
                        if status == "Approved": st.success(f"Status: {status} (Confidence: {critique.get('confidence_score')}/10)")
                        elif status == "Warning": st.warning(f"Status: {status} (Confidence: {critique.get('confidence_score')}/10)")
                        else: st.error(f"Status: {status} (Confidence: {critique.get('confidence_score')}/10)")
                            
                        st.write(f"**Critique:** {critique.get('senior_pm_critique')}")
                        st.write(f"**Key Risk:** {critique.get('key_risk')}")
                        
                        save_to_trade_blotter(target_ticker, trade_action, trader_thesis, critique)
                        st.toast("Trade logged to Institutional Memory.")
                else:
                    st.error("Please enter a ticker and a thesis.")


# ==========================================
# TAB 4: MACRO AI CO-PILOT
# ==========================================
with tab4:
    st.subheader("MACRO AI CO-PILOT")
    st.markdown("Converse with the institutional memory engine to synthesize theses, query past precedents, and debate structural positioning.")

    current_news = st.session_state.get("current_headline", "No live news parsed yet.")
    
    memory_context = "Memory bank is currently empty."
    
    if current_news != "No live news parsed yet." and memory_bank.get("documents"):
        memory_results = recall_past_events(current_news)
        
        if memory_results and memory_results['documents'] and len(memory_results["documents"][0]) > 0:
            relevant_docs = []
            for i in range(len(memory_results['documents'][0])):
                doc = memory_results['documents'][0][i]
                meta = memory_results['metadatas'][0][i]
                distance = round(memory_results['distances'][0][i], 4)
                
                relevant_docs.append(f"[Past Event: {doc} | Theme: {meta.get('theme')} | Math Distance: {distance}]")
                
            memory_context = " | ".join(relevant_docs)
        else:
             memory_context = "No highly relevant historical precedents found for this specific shock."
             
    with st.expander("🔍 View Active AI Context (Live Data + RAG Retrieved Memory)"):
        st.write(f"**Latest Parsed Event (Morning Briefing & News):** {current_news}")
        st.write(f"**Retrieved Institutional Precedents:**\n{memory_context}")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "System online. I have synced with the Institutional Memory and live cross-asset pricing. How can we formulate today's macro thesis?"}
        ]

    chat_container = st.container(height=450, border=True)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("E.g., Compare today's headline to our institutional memory. What is the optimal RV trade?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Synthesizing institutional memory and live pricing..."):
                    response = chat_with_macro_assistant(
                        prompt, 
                        st.session_state.messages[:-1], 
                        macro_data, 
                        memory_context, 
                        current_news
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
# ==========================================
# TAB 5: INSTITUTIONAL ARCHIVE
# ==========================================
with tab5:
    st.subheader("INTERNAL DATABASE VIEWER")
    st.markdown("Navigate and filter past institutional memory and executed trade theses.")
    
    db_view = st.radio("Select Database:", ["Trade Blotter (Executions)", "Macro Event Archive (RAG)"], horizontal=True)
    
    with st.container(border=True):
        if db_view == "Trade Blotter (Executions)":
            if trade_blotter:
                st.dataframe(trade_blotter[::-1], use_container_width=True)
            else:
                st.info("Trade blotter is currently empty. Execute a trade in the Execution Terminal.")
        else:
            if memory_bank["documents"]:
                archive_data = []
                for i in range(len(memory_bank["documents"])):
                    archive_data.append({
                        "Archived Event": memory_bank["documents"][i],
                        "Theme": memory_bank["metadatas"][i].get("theme", "N/A"),
                        "Asset Class": memory_bank["metadatas"][i].get("asset_class", "N/A"),
                    })
                st.dataframe(archive_data, use_container_width=True)
            else:
                st.info("Macro Event Archive is currently empty.")