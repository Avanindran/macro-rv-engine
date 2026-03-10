import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from graphs.regime_trades import REGIME_TRADES
    from graphs.macro_graph_40 import propagate_macro_event
    from ai.trade_generator import TRADE_MAP
    from ai.llm_processor import generate_institutional_trades
except ImportError:
    import graphs.regime_trades as REGIME_TRADES
    import graphs.macro_graph_40 as macro_graph
    import ai.trade_generator as TRADE_MAP
    from llm_processor import generate_institutional_trades
    
    propagate_macro_event = macro_graph.propagate_macro_event

def generate_and_score_trades(catalyst: str, node: str, direction: str, regime: str, macro_data: dict) -> list:
    """
    1. Maps graph contagion to raw candidate trades.
    2. Passes candidates to the LLM for quantitative scoring and thesis generation.
    3. Returns the final structured output to the UI.
    """
    propagation = propagate_macro_event(node, direction) if node and direction else []
    candidate_trades = []
    
    # 1. Gather Tactical Trades based on Graph Contagion
    if propagation:
        for p in propagation:
            target = p.get("target", "").lower()
            effect = p.get("effect", "increases").lower()

            if effect in ["up", "bullish", "spikes"]: effect = "increases"
            if effect in ["down", "bearish", "crashes"]: effect = "decreases"

            if target in TRADE_MAP:
                target_trades = TRADE_MAP[target]
                if isinstance(target_trades, dict) and effect in target_trades:
                    candidate_trades.extend(target_trades[effect])
                elif isinstance(target_trades, list): 
                    candidate_trades.extend(target_trades)
                    
    # 2. Gather Structural Trades based on Macro Regime
    if regime:
        reg_trades = REGIME_TRADES.get(regime, [])
        candidate_trades.extend(reg_trades)

    # Remove duplicates safely while preserving order
    clean_candidates = list(dict.fromkeys(candidate_trades))
    
    if not clean_candidates:
        return [] # No mapped trades found

    # 3. Use the LLM to score the candidates against live market data
    scored_trades = generate_institutional_trades(catalyst, regime, macro_data, clean_candidates)
    
    # Sort them by confidence before returning
    return sorted(scored_trades, key=lambda x: x.get("confidence", 0), reverse=True)