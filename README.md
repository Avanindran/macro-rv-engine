# MacroSynthetix Terminal

**An Institutional-Grade AI Co-Pilot for Global Macro & Systematic Execution**

## Overview
MacroSynthetix is a prototype quantitative research terminal designed to solve the primary bottleneck on modern Sales & Trading desks: **Information Overload**. 

By combining Large Language Models (Llama-3.3-70B) with mathematical Retrieval-Augmented Generation (TF-IDF Vectorization) and deterministic Cross-Asset Causal Graphs, the terminal autonomously ingests unstructured global news, maps it to structural macro regimes, and generates mathematically scored systematic trade ideas.

## Core Quantitative Architecture

### 1. True RAG Institutional Memory (TF-IDF & Cosine Similarity)
* **The Math:** Converts historical firm trade theses and macro events into a TF-IDF vocabulary matrix.
* **The Alpha:** When a new shock hits, the system calculates the Cosine Similarity against the entire historical vector space to retrieve the top $n$ nearest-neighbor precedents.
* **Data Integrity:** Engineered with strict exact-match filtering to prevent data leakage (overfitting to a $0.0$ distance match), ensuring the AI Co-Pilot generates theses based on true historical correlation, not exact string overlap.

### 2. Multi-Level Causal Knowledge Graph (BFS Traversal)
* **The Engine:** Moves beyond "black-box" LLM guessing by utilizing a hardcoded, deterministic dictionary of macroeconomic principles.
* **The Math:** Employs a Breadth-First Search (BFS) algorithm (`max_depth=2`) via `networkx` to trace second and third-order contagion paths (e.g., Geopolitics $\rightarrow$ Oil Supply $\rightarrow$ Inflation $\rightarrow$ Central Bank Policy). 
* **Dynamic Inversion:** Automatically inverts downstream propagation effects if the primary catalyst is a negative shock (e.g., cooling inflation dynamically triggers a dovish curve-steepening path).

### 3. Structural Regime Classification (6-Month Momentum)
* Filters out daily market noise by strictly classifying the global macroeconomic quadrant (Goldilocks, Overheating, Stagflation, Recession) using trailing 6-month momentum of Growth (10Y Treasury Yields) and Inflation (Crude Oil) proxies.

### 4. Conversational AI Co-Pilot & Execution
* **Context-Aware:** The AI Portfolio Manager is grounded strictly in the retrieved mathematical RAG precedents and live `yfinance` news event that is parsed.


## Tech Stack
* **Frontend UI:** Streamlit, Plotly (Interactive Charting)
* **Macro Data Pipeline:** `yfinance` API, `feedparser` (Live equities, rates, FX, commodities, and news)
* **AI / Inference:** Groq API (Llama-3.3-70B-Versatile for near-zero latency reasoning)
* **Quantitative Math:** `numpy`, `pandas`, `scikit-learn` (Vectorization, Percentiles, Correlation Matrices)
* **Contagion Mapping:** `networkx`, `matplotlib` (Seeded Spring Layouts for deterministic rendering)

## Terminal Workflow
1.  **Ingest & Analyze:** Auto-pulls RSS feeds, drops duplicates, and maps qualitative news to quantitative macro nodes.
2.  **Retrieve:** Scans the institutional RAG memory for mathematically correlated historical precedents.
3.  **Strategize:** The AI Co-Pilot suggests Relative Value and Factor trades based strictly on the contagion map and regime dictionaries.
4.  **Execute & Red-Team:** The PM submits a thesis; the AI Risk Manager stress-tests the logic against live pricing and logs it to the Institutional Blotter.