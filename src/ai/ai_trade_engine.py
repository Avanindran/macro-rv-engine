import sys
import os

# Ensure the root directory is in the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use absolute imports to prevent "No module named" errors
try:
    from graphs.regime_trades import REGIME_TRADES
    from graphs.macro_graph_40 import propagate_macro_event
    from ai.trade_generator import TRADE_MAP
except ImportError:
    # Fallback for direct script execution
    import graphs.regime_trades as REGIME_TRADES
    import graphs.macro_graph_40 as macro_graph
    import ai.trade_generator as TRADE_MAP
    
    # Map the functions if fallback is used
    propagate_macro_event = macro_graph.propagate_macro_event


def generate_ai_trades(node, direction, regime):

    propagation = propagate_macro_event(node, direction)

    trades = []

    for p in propagation:

        target = p["target"]

        if target in TRADE_MAP:

            trades.extend(TRADE_MAP[target])

    reg_trades = REGIME_TRADES.get(regime, [])

    trades.extend(reg_trades)

    return list(set(trades))