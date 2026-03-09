# Macro-RAG Relative Value (RV) Engine

## Project Description
The Macro-RAG RV Engine is a quantitative macroeconomic tracker designed to identify relative value trading opportunities. Instead of functioning as a standard news aggregator, this solution treats macroeconomic themes as quantitative factors. 

**How it Solves the Problem Statement:**
* **Information Overload & Hot Themes:** It utilizes an LLM pipeline to ingest fragmented news, extracting structured entities (theme, sentiment, asset class) to dynamically score and track market-moving developments.
* **Institutional Memory:** It employs a local vector database (ChromaDB) to map current events to historical analyst notes and past market reactions via semantic similarity. 
* **Risk Implications (Bonus):** It bridges qualitative news with quantitative trading by piping extracted macro signals into a statistical engine, calculating Z-scores against historical spreads to propose actionable risk implications and RV trades.