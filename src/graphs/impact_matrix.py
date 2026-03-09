
IMPACT_MATRIX = {

    "inflation": {
        "bonds": "bearish",
        "equities": "bearish",
        "usd": "bullish",
        "gold": "bearish"
    },

    "growth": {
        "equities": "bullish",
        "commodities": "bullish",
        "bonds": "bearish"
    },

    "geopolitics": {
        "oil": "bullish",
        "gold": "bullish",
        "equities": "bearish"
    }
}


def generate_market_impacts(theme):

    if theme not in IMPACT_MATRIX:
        return {}

    return IMPACT_MATRIX[theme]