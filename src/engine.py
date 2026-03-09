import pandas as pd
import numpy as np
from scipy import stats


def calculate_rv_signal(macro_data: dict):
    '''
    Takes structured JSON from LLM and calculates a statistical relative value trade recommendation based on historical mock data
    '''

    #Extract driver identified by LLM
    driver = macro_data.get("implied_driver", "Unknown")
    theme = macro_data.get("theme", "Unknown")

    # Hardcoded Mock Historical Data for the Hackathon Demo
    # In production, this would query a live Bloomberg/Refinitiv database
    market_database = {
        "Higher Rates": {
            "spread_name": "US 2Y / 10Y Treasury Yield Spread",
            "historical_mean": -0.40, # Inverted curve average
            "historical_std": 0.15,
            "current_market_pricing": -0.85 # The spread widened massively on the news
        },
        "Supply shock": {
            "spread_name": "Brent / WTI Crude Spread",
            "historical_mean": 4.50,
            "historical_std": 1.20,
            "current_market_pricing": 8.10 # Massive divergence
        },
        "Dovish Policy": {
            "spread_name": "S&P 500 / Russell 2000 Ratio",
            "historical_mean": 1.50,
            "historical_std": 0.05,
            "current_market_pricing": 1.41
        }
    }


    #match driver to our database. If not found, return a default.
    if driver not in market_database:
        return {"error:" f"No quantitative model build for driver: {driver}"}
    
    model = market_database[driver]

    #logic
    X = model["current_market_pricing"]
    mean = model["historical_mean"]
    sd = model["historical_std"]

    z_score = (X - mean) / sd

    trade_idea = "Hold Position / Monitor"
    action_colour = "normal"


    if z_score > 2.0:
        trade_idea = f"Sell the {model['spread_name']} (Overextended likely to mean revert)"
        action_colour = "red"
    elif z_score < -2.0:
        trade_idea = f"Buy the {model['spread_name']} (Undervalued likely to mean revert)"
        action_colour = "green"
        
    return {
        "spread_name": model['spread_name'],
        "current_value": round(X, 2),
        "historical_mean": model["historical_mean"],
        "historical_std": model['historical_std'],
        "z_score": round(z_score, 2),
        "trade_idea": trade_idea,
        "action_colour": action_colour
    }

# --- Testing the Module ---
if __name__ == "__main__":
    # Simulate the JSON we got from the LLM in the previous step
    mock_llm_output = {
        "theme": "Inflation",
        "asset_class": "Fixed Income",
        "sentiment": "Hot",
        "implied_driver": "Higher Rates"
    }
    
    result = calculate_rv_signal(mock_llm_output)
    print("Quant Engine Output:")
    print(result)