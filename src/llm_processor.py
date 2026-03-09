import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key = os.environ.get("GROQ_API_KEY"),
                base_url = "https://api.groq.com/openai/v1"
                )

def extract_macro_signals(headline: str) -> dict:
    """ 
    Takes a raw news headline and returns structured data for the engine
    """
    
    system_prompt = """
        You are a macro hedge fund analyst.

        Extract macro signals from the headline.

        Return STRICT JSON:

        {
        "theme": "",
        "country": "",
        "macro_node": "",
        "direction": "up/down/neutral",
        "asset_class": "",
        "sentiment": "",
        "implied_driver": "",
        "primary_impact": "",
        "secondary_spillover": "",
        "confidence": 0-1,
        "rationale": ""
        }

        macro_node options:
        inflation
        growth
        central_bank_policy
        oil_prices
        geopolitics
        risk_sentiment
        bond_yields
    """

    try:
        response = client.chat.completions.create(
            model = "llama-3.3-70b-versatile", # faster responses
            response_format = {"type" : "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": headline}
            ],
            temperature=0.0 #keep temperature at 0 for deterministic, consistent outputs
        )
        
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Error connecting to LLM: {e}")
        return {}
    
if __name__ == "__main__":
    #Mock headline acting as our input data
    sample_news = "US CPI jumps to 4.5% in February, crushing estimates and triggering a massive selloff in Treasuries."
    print(f"Analyzing headline: {sample_news} '\n")

    result = extract_macro_signals(sample_news)
    print("structured output for engine:") 
    print(json.dumps(result, indent = 4))


def critique_trade_thesis(ticker: str, action: str, thesis: str, macro_context: dict) -> dict:
    """
    Acts as a Senior PM evaluating a junior trader's thesis before execution.
    """
    system_prompt = f"""
    You are a Senior Macro Portfolio Manager. A trader is proposing a {action} trade on {ticker}.
    Current Macro Environment Data: {json.dumps(macro_context)}
    Trader's Thesis: {thesis}
    
    Critique this trade. Identify blind spots, correlation risks, or conflicts with the current macro environment.
    Return strictly as a JSON object with these keys:
    - approval_status: (String: "Approved", "Warning", or "Rejected")
    - confidence_score: (Integer 1-10)
    - senior_pm_critique: (A harsh, 2-sentence quantitative critique of their thesis)
    - key_risk: (1 short sentence identifying the biggest risk to this trade)
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Evaluate my trade."}
            ],
            temperature=0.2 # Slight temperature for better reasoning
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error connecting to LLM: {e}")
        return {"approval_status": "Error", "senior_pm_critique": "AI connection failed."}