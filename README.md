# MacroSynthetix Terminal

**An Institutional-Grade AI Co-Pilot for Global Macro & Systematic Trading**



## Overview
MacroSynthetix is a prototype quantitative research terminal designed to solve the primary bottleneck on modern Sales & Trading desks: **Information Overload**. 

By combining large language models (Llama-3.3-70B) with mathematical Retrieval-Augmented Generation (TF-IDF Vectorization) and cross-asset contagion graphs, the terminal autonomously ingests unstructured global news, maps it to structural macro regimes, and provides a clearer picture of macroeconomic events through interactive elements.

## Key Features

* **Quantitative Event Parsing:** Converts raw news feeds into structured macro entities (Catalyst, Asset Class, Directional Impact) using zero-shot LLM extraction.
* **True RAG Institutional Memory:** Implements a TF-IDF vector database to recall highly correlated historical precedents via cosine similarity, explicitly engineered to prevent data leakage and exact-match overfitting.
* **Cross-Asset Causal Graphing:** Utilizes `networkx` to visualize second-order market contagion (e.g., Geopolitics $\rightarrow$ Oil Supply $\rightarrow$ Inflation $\rightarrow$ Equity Volatility).
* **6-Month Structural Regime Monitor:** Classifies the current macroeconomic quadrant (Goldilocks, Overheating, Stagflation, Recession) using trailing 6-month momentum of Growth (10Y Yields) and Inflation (Crude) proxies.
* **Conversational AI Co-Pilot:** A dynamic chat interface allowing Portfolio Managers to debate structural positioning against the firm's archived memory and live pricing data.
* **Risk-Adjusted Execution:** Calculates live 1-Day 95% Historical Value at Risk (VaR) and Annualized Volatility before routing trades to an AI Senior PM for thesis red-teaming.

## Architecture & Tech Stack
* **Frontend:** Streamlit, Plotly (Interactive Charting)
* **Macro Data:** `yfinance` API (Live equities, rates, FX, and commodities)
* **AI Engine:** Groq API (Llama-3.3-70B-Versatile for near-zero latency reasoning)
* **Math & Risk:** `numpy`, `pandas`, `scikit-learn` (TF-IDF, Cosine Similarity, VaR)
* **Network Mapping:** `networkx`, `matplotlib`

## The Pipeline
1. **Ingest:** Auto-pulls RSS feeds and drops duplicates.
2. **Contextualize:** Scans the institutional memory for math-distance precedents.
3. **Strategize:** Co-Pilot suggests Relative Value trades based on the contagion map.
4. **Execute:** PM submits a thesis; AI Risk Manager stress-tests the logic against live pricing.