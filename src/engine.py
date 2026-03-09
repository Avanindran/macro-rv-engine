import pandas as pd
import numpy as np
from scipy import stats
import yfinance as yf



def fetch_live_spread(ticker1 :str, ticker2: str, spread_name: str, operation: str = "subtract"):
    """Downloads 1 year of historical data and calculates the spread and returns z-score"""
    try:
        data1 = yf.download(ticker1, period = "1y", interval = "1d")['Close']
        data2 = yf.download(ticker2, period = "1y", interval = "1d")['Close']


        df = pd.concat([data1, data2], axis = 1).dropna()
        df.columns = ['Asset1', 'Asset2']


        if operation == "divide":
            df['Spread'] = df['Asset1'] / df['Asset2']
        else:
            df['Spread'] = df['Asset1'] - df['Asset2']

        #Calculate metrics
        current_spread = df['Spread'].iloc[-1]
        historical_mean = df['Spread'].mean()
        historical_std = df['Spread'].std()

        z_score = (current_spread - historical_mean) / historical_std

        return {
            "spread_name": spread_name,
            "current_value": round(float(current_spread), 3),
            "historical_mean": round(float(historical_mean), 3),
            "historical_std": round(float(historical_std), 3),
            "z_score": round(float(z_score), 2)
            } 
    
    except Exception as e:
    
        return {"error": f"Failed to fetch live data for {spread_name}: {e}"}


def calculate_rv_signal(macro_data: dict):
    '''
    Takes structured JSON from LLM and maps it to live market data.
    '''
    driver = macro_data.get("implied_driver", "Unknown")
    
    # Map the AI's macro driver to actual ticker symbols
    if "Rates" in driver or "Yield" in driver or "Inflation" in driver:
        # Proxy for Yield Curve (10Y Yield minus 5Y Yield)
        result = fetch_live_spread("^TNX", "^FVX", "US 10Y - 5Y Yield Spread", "subtract")
    elif "Supply" in driver or "Oil" in driver or "Energy" in driver:
        # Brent Crude vs WTI Crude
        result = fetch_live_spread("BZ=F", "CL=F", "Brent / WTI Crude Spread", "subtract")
    elif "Dovish" in driver or "Equities" in driver or "Risk" in driver:
        # Risk-on indicator: S&P 500 vs Russell 2000
        result = fetch_live_spread("^GSPC", "^RUT", "S&P 500 / Russell 2000 Ratio", "divide")
    else:
        return {"error": f"No live quantitative model built for driver: {driver}"}

    if "error" in result:
        return result

    # Trading Logic
    z_score = result["z_score"]
    if z_score > 2.0:
        result["trade_idea"] = f"Sell the {result['spread_name']} (Statistically Overextended)"
        result["action_color"] = "red"
    elif z_score < -2.0:
        result["trade_idea"] = f"Buy the {result['spread_name']} (Statistically Undervalued)"
        result["action_color"] = "green"
    else:
        result["trade_idea"] = "Hold Position / Monitor (Within normal ranges)"
        result["action_color"] = "normal"
        
    return result


