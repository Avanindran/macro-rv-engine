"""
Trade map for AI to follow core macroeconomic trade principles
"""


TRADE_MAP = {

"oil":[
"Long Oil Futures",
"Long Energy Equities"
],

"equities":[
"Long S&P500"
],

"volatility":[
"Long VIX Calls"
],

"dollar":[
"Long DXY"
],

"real_rates":[
"Short Gold"
]

}


def infer_trades(propagation):

    trades=[]

    for p in propagation:

        tgt = p["target"]

        if tgt in TRADE_MAP:

            trades.extend(TRADE_MAP[tgt])

    return list(set(trades))


