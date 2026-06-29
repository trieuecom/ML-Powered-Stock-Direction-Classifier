import yfinance as yf
import json
from google import genai
from google.genai import types

def get_ticker_action_info(user_query):
    client = genai.Client()
    tick_act_prompt = f"""
    Analyze the following user query: {user_query} and extract the information:
    1. The stock ticker symbol mentioned (e.g., if the user enters Apple or similar words, convert it to AAPL; similarly: NVDA for NVIDIA, MSFT for Microsoft, GOOGL for Google, AMZN for Amazon, TSLA for Tesla).
    2. Understand the context of the query and extract the action from the user's query (e.g., WAIT, SELL, BUY, HOLD, GENERAL_INFO). Example: User query: "What should I do with my Apple's stocks right now? Should I sell or buy more?", this will return AAPL as the ticket and GENERAL_INFO as the action.
    Return ONLY a valid JSON object with the keys "ticker" and "action". Do not include any markdown formatting or backticks.
    """
    
    try:
        response = client.models.generate_content(
            model = "gemini-3.5-flash",
            contents = tick_act_prompt,
            config= genai.types.GenerateContentConfig(
                temperature=0.0, #always take the exact query info from the user, no distorting
                response_mime_type="application/json" #Forcing Gemini to return in JSON format        
            )
        )
        
        # Parsing the JSON response into text:
        result = json.loads(response.text)
        ticker = result.get("ticker")
        action = result.get("action")
        return ticker, action
    
    except Exception as e:
        print(f"There is an error in returning user's ticker and action info: {e}")
        return None, "GENERAL_INFO"

def get_news_summary(ticker):
    try:
        tick = yf.Ticker(ticker) # initialize an Ticker object 
        news_list = tick.news # retrieve a list a news for the ticker
        if not news_list:
            print(f"There is no news for {ticker}")
            return None
        
        ticker_context = "" # placeholder for context
        
        for i, news in enumerate(news_list[:5]):
            title = news.get('title', "There is no title for the article.")
            publisher = news.get('publisher', "There is no publisher for the article.")
            summary = news.get('summary', "There is no summary for the article.")
            # Generate context
            ticker_context += f"Article: {i+1}\n"
            ticker_context += f"Title: {title}\n"
            ticker_context += f"Publisher: {publisher}\n"
            ticker_context += f"Summary: {summary}"
            
        if ticker_context: # check whether there is any generated context
            return ticker_context.strip() # remove spaces
        else: 
            return None
    except Exception as e: 
        print(f"Error fetching for Ticker: {ticker}: {e}!")
        return None

def get_latest_queries(ticker, action, probability, news_context): 
    client = genai.Client()
    
    # Choosing client models as we can choose the instruction preference
    system_instruction = ("You are a financial advisory expert. Based on the provided context data for the specified ticker, please provide:"
                  "1. A current overview of the ticker."
                  "2. Valuable insights to support investment decisions at this time."
                  "3. A perspective and recommendation for investors on whether to invest, based on the probability variable."
                  "4. Tone requirements: professional and concise yet highlighting key details; do not hallucinate information or over-exaggerate."
                  "5. Respond in the user's input language, keeping the information within 4–6 bullet points."
    )
    
    system_prompt = f"""
    Our system has just generated a prediction based on the latest data for ticker {ticker}:
    - Recommended action: {action}
    - Model confidence level: {probability:.2f}

    Additionally, here is the latest news providing context for {ticker}: {news_context}

    Based on the provided information, let us outline the rationale for the prediction, key insights, and the risks investors should consider.
    """
    
    try:
        model_response = client.models.generate_content(
            model = "gemini-3.5-flash",
            contents = system_prompt,
            config = genai.types.GenerateContentConfig(
                system_instruction = system_instruction,
                temperature = 0.2 # set temperature to decrease hallucination from AI 
            )
        )
        return model_response.text
        
    except Exception as e:
        print(f"There is an error when generating investing decision analysis for {ticker}: {e}")
        return None