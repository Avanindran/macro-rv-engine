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
    You are a quantitative macro analyst. Extract the following information from the news
    headline and return it strictly as a JSON object with these keys:
    - theme (eg,. Inflation, Geopolitics, Central Bank, Energy )
    - asset_class (e.g, Equities, fX, Fixed Income, Commodities )
    - sentiment (Hot or Cool)
    - implied_driver (eg, Higher Rates, Policy shock, Supply shock, Dovish Policy )
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
