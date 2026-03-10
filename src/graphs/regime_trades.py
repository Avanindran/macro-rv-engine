"""
Structural Macro Regime Trades (3-6 Month Horizon)
"""

REGIME_TRADES = {
    "Goldilocks": [
        "Long Risk Assets (NQ/ES Futures)",
        "Short VIX Futures (Harvest Volatility Risk Premium)",
        "Long EM FX Carry Trades (e.g., BRL/JPY)",
        "Long High Yield vs IG Credit Spreads" 
    ],

    "Overheating": [ 
        "Short US Treasuries (Bear Flattener Curve Trade)", 
        "Long Broad Commodities (BCOM Index)",
        "Long Value vs. Growth Factor RV",
        "Long Breakeven Inflation (TIPS vs Nominal)"
    ],

    "Stagflation": [
        "Long Gold (XAU/USD)",
        "Long Volatility (VIX Call Spreads)",
        "Short Consumer Discretionary vs. Staples (XLY/XLP RV)",
        "Underweight Duration (Cash)"
    ],

    "Recession": [
        "Long US Duration (Bull Steepener Curve Trade)", 
        "Long Gold (Flight to Safety)",
        "Short Cyclicals (Industrials/Materials)",
        "Short High Yield Credit (CDX HY Widening)"
    ],
    
    "Neutral": [
        "Harvest Yield (Selling Iron Condors)",
        "Market-Neutral Statistical Arbitrage",
        "Wait for Regime Confirmation"
    ]
}