import streamlit as st
import sys
import os
import feedparser
from collections import Counter
import yfinance as yf
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local imports
from src.engine import calculate_rv_signal
from src.llm_processor import extract_macro_signals, critique_trade_thesis
from src.vector_store import recall_past_events, add_to_memory, memory_bank, save_to_trade_blotter, trade_blotter
from src.macro_graph import propagate_macro_shock, generate_risk_implications
from src.theme_tracker import update_theme
from src.impact_engine import generate_market_impacts
from src.regime_classifier import classify_regime
from src.ai_trade_engine import generate_ai_trades
from src.trade_scoring import score_trades


# --- Page Configuration ---
st.set_page_config(page_title="Macro-RAG Terminal", layout='wide', initial_sidebar_state="collapsed")

# --- Hybrid CSS for Tab Shaping ---
# (Colors are now handled by config.toml, we only keep structural CSS here)
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px 4px 0px 0px; padding: 10px 20px; border: 1px solid #30363d; border-bottom: none; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Fetching Helpers ---
@st.cache_data(ttl=300)
def fetch_live_news():
    try:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC,CL=F&region=US&lang=en-US"
        feed = feedparser.parse(url)
        news_dict = {entry.title: entry.link for entry in feed.entries[:15]}
        return news_dict if news_dict else {"No live news found.": "#"}
    except Exception as e:
        return {f"Error fetching news: {e}": "#"}

@st.cache_data(ttl=600)
def fetch_macro_overview():
    tickers = {
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
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                pct_change = ((current - previous) / previous) * 100
                data[name] = {"val": round(current, 3), "change": round(pct_change, 2)}
    except:
        pass
    return data

@st.cache_data(ttl=60) # Fast cache for charting
def fetch_chart_data(ticker, period, interval):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df
    except Exception as e:
        return None

# --- Header ---
st.title("📟 SCHRODERS MACRO-RAG TERMINAL v2.0")
st.markdown("`SYSTEM STATUS: ONLINE | ASSET CLASS: MULTI | ENGINE: TF-IDF, LLAMA-3 & STAT-ARB`")
st.divider()

# --- Top Nav Data Strip ---
macro_data = fetch_macro_overview()
if macro_data:
    cols = st.columns(len(macro_data))
    for i, (name, metrics) in enumerate(macro_data.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="border: 1px solid #30363d; border-radius: 5px; padding: 10px; text-align: center; background-color: #161b22;">
                <p style="margin: 0; color: #8b949e; font-size: 12px; font-weight: bold;">{name}</p>
                <h4 style="margin: 0; color: #c9d1d9;">{metrics['val']}</h4>
                <p style="margin: 0; font-size: 12px; color: {'#3fb950' if metrics['change'] > 0 else '#f85149'};">
                    {'+' if metrics['change'] > 0 else ''}{metrics['change']}%
                </p>
            </div>
            """, unsafe_allow_html=True)
st.write("") 

# --- Multi-Tab Layout ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📰 News Intelligence",
    "🌐 Macro Engine",
    "📈 Execution Terminal",
    "🤖 AI Trade Generator",
    "🧠 Institutional Memory"
])

# ==========================================
# TAB 1: LIVE TERMINAL (The Event Engine)
# ==========================================
with tab1:
    col1, col2 = st.columns([1.5, 1])

    with col1:
        with st.container(border=True):
            st.subheader("📡 EVENT INGESTION")
            input_method = st.radio("SOURCE:", ["Live Feed (Yahoo Finance)", "Manual Entry"], horizontal=True)
            
            if input_method == "Live Feed (Yahoo Finance)":
                live_news_dict = fetch_live_news()
                headline_input = st.selectbox("SELECT BREAKING HEADLINE:", list(live_news_dict.keys()))
                article_url = live_news_dict[headline_input]
                st.markdown(f"*[🔗 Read Source Article]({article_url})*")
            else:
                headline_input = st.text_area("ENTER CUSTOM HEADLINE:", value="Middle East tensions escalate, causing Brent crude to spike 8% overnight.")

        if st.button("EXECUTE QUANTITATIVE PARSING", type="primary", use_container_width=True):
            with st.spinner("LLM Extracting Macro Entities..."):
                data = extract_macro_signals(headline_input)
                st.session_state.structured_data = data
                st.session_state.current_headline = headline_input

                # --- NEW MACRO ENGINE ---
                node = data.get("macro_node")
                direction = data.get("direction")
                theme = data.get("theme")

                update_theme(theme)
                st.session_state.propagation = propagate_macro_shock(node, direction)
                st.session_state.risks = generate_risk_implications(node, direction)
                st.session_state.market_impacts = generate_market_impacts(node)
                
        if 'structured_data' in st.session_state:
            with st.container(border=True):
                st.subheader("🕸️ CROSS-ASSET CONTAGION MAP")
                driver = st.session_state.structured_data.get('implied_driver', 'Unknown Event')
                asset = st.session_state.structured_data.get('asset_class', 'Unknown Asset')
                primary = st.session_state.structured_data.get('primary_impact', 'Unknown Primary')
                secondary = st.session_state.structured_data.get('secondary_spillover', 'Unknown Secondary')
                rationale = st.session_state.structured_data.get('rationale', 'No rationale provided.')

                st.warning(f"**{st.session_state.current_headline}** ➔ *likely {driver}* ➔ **{asset} volatility ↑**")
                
                c1, c2, c3, c4, c5 = st.columns([2, 0.5, 2, 0.5, 2])
                with c1: st.info(f"**CATALYST**\n\n{driver}")
                with c2: st.markdown("<h3 style='text-align: center; color: gray;'>➔</h3>", unsafe_allow_html=True)
                with c3: st.warning(f"**1st ORDER**\n\n{primary}")
                with c4: st.markdown("<h3 style='text-align: center; color: gray;'>➔</h3>", unsafe_allow_html=True)
                with c5: st.error(f"**2nd ORDER**\n\n{secondary}")
                st.caption(f"**Macro Rationale:** {rationale}")
        
        if "propagation" in st.session_state:
            with st.container(border=True):
                st.subheader("🌐 MACRO PROPAGATION ENGINE")
                for p in st.session_state.propagation:
                    st.write(f"**{p['source']}** ➜ **{p['target']}** ({p['effect']})")
        
        if "market_impacts" in st.session_state:
            with st.container(border=True):
                st.subheader("📊 CROSS-ASSET IMPACT MATRIX")
                impacts = st.session_state.market_impacts
                for asset, direction in impacts.items():
                    if direction == "bullish":
                        st.success(f"{asset.upper()} → BULLISH")
                    elif direction == "bearish":
                        st.error(f"{asset.upper()} → BEARISH")

    with col2:
        with st.container(border=True):
            st.subheader("⚙️ STAT-ARB RV ENGINE")
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
                    st.write(f"`Historical Mean: {result['historical_mean']} bps`")
                    
                    if result["action_color"] == "red":
                        st.error(f"**TRADE SIGNAL:** {result['trade_idea']}")
                    elif result["action_color"] == "green":
                        st.success(f"**TRADE SIGNAL:** {result['trade_idea']}")
                    else:
                        st.info(f"**TRADE SIGNAL:** {result['trade_idea']}")
            else:
                st.info("Awaiting Signal Execution...")

        with st.container(border=True):
            st.subheader("🧠 RAG PRECEDENTS")
            if 'current_headline' in st.session_state:
                memory_results = recall_past_events(st.session_state.current_headline)
                if memory_results and memory_results['documents'] and len(memory_results["documents"][0]):
                    for i in range(len(memory_results['documents'][0])):
                        past_doc = memory_results['documents'][0][i]
                        past_meta = memory_results['metadatas'][0][i] 
                        distance = round(memory_results['distances'][0][i], 4)
                        with st.expander(f"Archived Match {i+1} | Math Distance: {distance}"):
                            st.caption(f"Desk Action: {past_meta.get('action', 'N/A')}")
                            st.write(f"*{past_doc}*")

        with st.container(border=True):
            st.subheader("🔥 REAL-TIME THEME TRACKER")
            st.markdown("Monitoring frequency of macro keywords in the live RSS feed to determine 'Hot' vs 'Cooling' themes.")
            from src.theme_tracker import calculate_theme_heat

            heat = calculate_theme_heat()
            if heat:
                sorted_heat = sorted(heat.items(), key=lambda x: x[1], reverse=True)
                hottest = sorted_heat[0][0]
                coolest = sorted_heat[-1][0]
                col_x, col_y, col_z = st.columns(3)
                with col_x: st.metric("HOTTEST THEME", hottest)
                with col_y: st.metric("ACTIVE THEMES", len(heat))
                with col_z: st.metric("COOLING THEME", coolest)

                st.divider()
                for theme, score in sorted_heat:
                    st.write(f"**{theme}** (Heat Score: {score})")
                    st.progress(min(score / 5, 1))

# ==========================================
# TAB 2: MACRO ENGINE
# ==========================================
with tab2:
    st.subheader("Macro Regime Monitor")

    growth_signal = macro_data.get("US 10Y Yield", {}).get("change", 0)
    inflation_signal = macro_data.get("Crude Oil", {}).get("change", 0)
    regime = classify_regime(growth_signal, inflation_signal)
    st.metric("Current Macro Regime", regime)
    
    with st.container(border=True):
        st.subheader("Risk Engine")
        if "risks" in st.session_state:
            for r in st.session_state.risks:
                st.warning(r)
        else:
            st.info("No risk signals detected yet")

    with st.container(border=True):
        st.subheader("🌐 Macro Causal Graph")
        if "propagation" in st.session_state:
            G = nx.DiGraph()
            for p in st.session_state.propagation:
                G.add_edge(p["source"], p["target"])
            
            # Using st.columns to center/size the matplotlib chart nicely
            fig_col, _ = st.columns([2, 1])
            with fig_col:
                fig, ax = plt.subplots(facecolor='#0d1117')
                ax.set_facecolor('#0d1117')
                nx.draw(
                    G, with_labels=True, node_size=3000, font_size=9, 
                    ax=ax, node_color='#ff9d00', font_color='black', edge_color='#58a6ff'
                )
                st.pyplot(fig)
        else:
            st.info("Awaiting macro shock propagation.")

    with st.container(border=True):
        col_reg1, col_reg2, col_reg3 = st.columns(3)
        
        is_risk_on = macro_data.get("US 10Y Yield", {}).get("change", 0) > 0 and macro_data.get("Crude Oil", {}).get("change", 0) > 0
        curve_inverted = macro_data.get("US 2Y Yield", {}).get("val", 0) > macro_data.get("US 10Y Yield", {}).get("val", 0)
        
        with col_reg1:
            st.markdown("### Market Sentiment")
            if is_risk_on: st.success("🟢 RISK-ON (Growth Optimism)")
            else: st.error("🔴 RISK-OFF (Flight to Safety)")
                
        with col_reg2:
            st.markdown("### Yield Curve Shape")
            if curve_inverted: st.error("⚠️ INVERTED (Recession Warning)")
            else: st.success("📈 NORMAL (Economic Expansion)")
                
        with col_reg3:
            st.markdown("### Dominant Dollar (DXY)")
            if macro_data.get("DXY (Dollar)", {}).get("change", 0) > 0: st.warning("🦅 STRONG DOLLAR (Tightening)")
            else: st.info("🕊️ WEAK DOLLAR (Accommodative)")

    with st.container(border=True):
        st.subheader("📊 Live Cross-Asset Matrix")
        st.markdown("A real-time snapshot of critical spreads monitored by the quantitative desk.")
        matrix_cols = st.columns(3)
        with matrix_cols[0]:
            st.metric(label="Treasury 10s2s Spread", value=f"{round(macro_data.get('US 10Y Yield', {}).get('val', 0) - macro_data.get('US 2Y Yield', {}).get('val', 0), 2)} bps")
        with matrix_cols[1]:
            st.metric(label="Gold / Oil Ratio", value=round(macro_data.get('Gold', {}).get('val', 1) / (macro_data.get('Crude Oil', {}).get('val', 1) or 1), 2))
        with matrix_cols[2]:
            st.metric(label="EUR/USD Momentum", value=macro_data.get('EUR/USD', {}).get('val', 0), delta=f"{macro_data.get('EUR/USD', {}).get('change', 0)}%")


# ==========================================
# TAB 3: EXECUTION TERMINAL (FIXED CHARTING)
# ==========================================
with tab3:
    st.subheader("📈 TERMINAL CHARTING & TRADE EXECUTION")
    st.markdown("Pull live asset data, formulate a thesis, and submit to the AI Portfolio Manager for Red-Teaming.")
    
    chart_col, execution_col = st.columns([2, 1])
    
    with chart_col:
        with st.container(border=True):
            st.markdown("### Interactive Charting")
            c_input1, c_input2, c_input3 = st.columns(3)
            with c_input1:
                target_ticker = st.text_input("Enter Asset Ticker (e.g., AAPL, CL=F):", value="CL=F")
            with c_input2:
                time_period = st.selectbox("Time Horizon:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
            with c_input3:
                chart_interval = st.selectbox("Interval:", ["1d", "1wk", "1mo"], index=0)
                
            if target_ticker:
                with st.spinner("Fetching Market Data..."):
                    df = fetch_chart_data(target_ticker, time_period, chart_interval)
                    
                    if df is not None and not df.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=df.index,
                            open=df["Open"],
                            high=df["High"],
                            low=df["Low"],
                            close=df["Close"],
                            name=target_ticker,
                            increasing_line_color='#3fb950', 
                            decreasing_line_color='#f85149'
                        )])

                        fig.update_layout(
                            title=f"{target_ticker} Price Action",
                            xaxis_title="Date",
                            yaxis_title="Price",
                            template="plotly_dark",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis_rangeslider_visible=False, # Hides the bulky bottom slider for a cleaner look
                            height=500
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("No data found. Please check the ticker symbol.")

    with execution_col:
        with st.container(border=True):
            st.markdown("### Trade Blotter Submission")
            trade_action = st.radio("Action:", ["Buy / Long", "Sell / Short"], horizontal=True)
            trader_thesis = st.text_area("Write your Macro Thesis:", height=150, 
                                         placeholder="E.g., I am going long Oil because the DXY is cooling and Middle East supply is constrained.")
            
            if st.button("Submit to AI Risk Manager", type="primary", use_container_width=True):
                if trader_thesis and target_ticker:
                    with st.spinner("Senior AI PM is reviewing your thesis..."):
                        critique = critique_trade_thesis(target_ticker, trade_action, trader_thesis, macro_data)
                        
                        st.divider()
                        st.markdown("#### 🤖 AI PM Feedback")
                        
                        status = critique.get("approval_status", "Warning")
                        if status == "Approved":
                            st.success(f"**Status: {status}** (Confidence: {critique.get('confidence_score')}/10)")
                        elif status == "Warning":
                            st.warning(f"**Status: {status}** (Confidence: {critique.get('confidence_score')}/10)")
                        else:
                            st.error(f"**Status: {status}** (Confidence: {critique.get('confidence_score')}/10)")
                            
                        st.write(f"**Critique:** {critique.get('senior_pm_critique')}")
                        st.write(f"**Key Risk:** {critique.get('key_risk')}")
                        
                        save_to_trade_blotter(target_ticker, trade_action, trader_thesis, critique)
                        st.toast("✅ Trade logged to Institutional Memory.")
                else:
                    st.error("Please enter a ticker and a thesis.")

# ==========================================
# TAB 4: AI TRADE GENERATOR
# ==========================================
with tab4:

    st.subheader("AI Trade Generator")
    if "structured_data" in st.session_state:

        node = st.session_state.structured_data.get("macro_node")
        direction = st.session_state.structured_data.get("direction")

        growth = macro_data.get("US 10Y Yield",{}).get("change",0)
        inflation = macro_data.get("Oil",{}).get("change",0)

        regime = classify_regime(growth, inflation)
        st.metric("Macro Regime", regime)
        trades = generate_ai_trades(
            node,
            direction,
            regime
        )
        propagation = st.session_state.get("propagation", [])
        scored = score_trades(trades, propagation)

        st.divider()
        for t in scored:
            st.success(
                f"{t['trade']}  |  Confidence {t['confidence']}%"
            )

    else:
        st.info("Run news analysis first.")

# ==========================================
# TAB 5: INSTITUTIONAL MEMORY
# ==========================================
with tab5:
    st.subheader("🗄️ INTERNAL DATABASE VIEWER")
    st.markdown("Navigate and filter past institutional memory and executed trade theses.")
    
    db_view = st.radio("Select Database:", ["Trade Blotter (Executions)", "Macro Event Archive (RAG)"], horizontal=True)
    
    with st.container(border=True):
        if db_view == "Trade Blotter (Executions)":
            if trade_blotter:
                st.dataframe(trade_blotter[::-1], use_container_width=True)
            else:
                st.info("Trade blotter is currently empty. Execute a trade in the Charting tab.")
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