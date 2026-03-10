"""
Trade map for AI to follow core macroeconomic trade principles
"""


TRADE_MAP = {
    "oil": {
        "increases": ["Long Brent/WTI Calendar Spreads", "Long Energy vs. Short Airlines (RV Pair)"],
        "decreases": ["Short Front-Month Brent Futures", "Long Consumer Discretionary (XLY)"]
    },
    "equities": {
        "increases": ["Long High-Beta Tech / Short Staples", "Short VIX Futures (Volatility Risk Premium)"],
        "decreases": ["Long VIX Call Spreads", "Long Defensive Sectors (XLU/XLP)"]
    },
    "dollar": {
        "increases": ["Short EUR/USD", "Long USD/JPY (Carry Trade)"],
        "decreases": ["Long Emerging Market FX", "Long Gold (XAU/USD)"]
    },
    "yield_curve": {
        "steepens": ["2s10s Curve Steepener (Pay 2Y, Receive 10Y)"],
        "flattens": ["2s10s Curve Flattener (Receive 2Y, Pay 10Y)"]
    },
    "real_rates": {
        "increases": ["Short Gold Futures", "Short Unprofitable Tech (ARKK)"],
        "decreases": ["Long TIPS (Treasury Inflation-Protected Securities)", "Long Gold"]
    }
}


def infer_trades(propagation):

    trades=[]

    for p in propagation:

        tgt = p["target"]

        if tgt in TRADE_MAP:

            trades.extend(TRADE_MAP[tgt])

    return list(set(trades))


