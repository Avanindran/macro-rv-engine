import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from graphs.regime_trades import REGIME_TRADES
    from ai.trade_generator import TRADE_MAP
    from ai.llm_processor import generate_institutional_trades
except ImportError:
    import graphs.regime_trades as REGIME_TRADES
    import ai.trade_generator as TRADE_MAP
    from llm_processor import generate_institutional_trades
    
    

