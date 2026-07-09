import yfinance as yf
import json
from google import genai
from google.genai import types
import streamlit as st

def get_ticker_action_info(user_query):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    tick_act_prompt = f"""
    Analyze the following user query: {user_query} and extract the information:
    1. The stock ticker symbol mentioned (e.g., if the user enters Apple or similar words, convert it to AAPL; similarly: NVDA for NVIDIA, MSFT for Microsoft, GOOGL for Google, AMZN for Amazon, TSLA for Tesla).
    2. Understand the context of the query and extract the action from the user's query. This MUST be normalized into one of these exact lowercase base forms: "buy", "sell", "hold", "wait", or "general_info".
    
    *Example case*: If the User query is "What should I do with my Apple's stocks right now? Should I sell or buy more?", this will return "AAPL" as the ticker and "general_info" as the action (since the intent is a mixed/general inquiry).
    
    You MUST strictly return a JSON object with the following keys:
    - "ticker": The stock ticker in uppercase (e.g., "AAPL", "NVDA"). If not found, return null.
    - "action": The normalized financial action intent ("buy", "sell", "hold", "wait", or "general_info").
    
    Return ONLY a valid JSON object with the keys "ticker" and "action". Do not include any markdown formatting, backticks, or extra commentary outside the JSON.
    """
    
    try:
        response = client.models.generate_content(
            model = "gemini-2.5-flash",
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
        print(news_list[0])
        if not news_list:
            print(f"There is no news for {ticker}")
            return None
        
        ticker_context = "" # placeholder for context
        count = 0 # use count to count until reach n number of stories
        
        for news in news_list:
            # Extract the content
            content = news.get("content", {})
            # Skip video content, only keep text t
            if content.get("contentType") == "VIDEO":
                continue
            
            if count >= 5: # Count if the amount of ticker context is larger than 5 then stop
                break
            title = content.get('title', "There is no title for the article.")
            publisher = content.get('provider', {}).get("displayName", "There is no publisher for the article.")
            summary = content.get('summary', "There is no summary for the article.")
            
            # Generate context
            ticker_context += f"Article: {count+1}\n"
            ticker_context += f"Title: {title}\n"
            ticker_context += f"Publisher: {publisher}\n"
            ticker_context += f"Summary: {summary}\n\n"
            
            if ticker_context:
                count += 1
            else:
                return None
            
        if ticker_context: # check whether there is any generated context
            return ticker_context.strip() # remove spaces
        else: 
            return None
    except Exception as e: 
        print(f"Error fetching for Ticker: {ticker}: {e}!")
        return None

def provide_recommendation(ticker, final_action, probability, news_summary, rsi, sma_50, current_price): 
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Choosing client models as we can choose the instruction preference
    system_instruction = (
    "You are a financial data assistant. Based ONLY on the provided context data, "
    "produce a concise, professional summary. "
    "Rules:\n"
    "1. Never invent technical indicators, price levels, or news that are not explicitly provided in the input.\n"
    "2. If a data field is missing or empty (e.g., no news), state that explicitly instead of speculating.\n"
    "3. Do not issue direct buy/sell instructions ('you should invest'). Instead, present the model's signal "
    "and probability as one data point among several risk factors, and frame conclusions as informational, "
    "not financial advice.\n"
    "4. Tone: plain, professional, concise. No emojis, no dramatic headings, no marketing language.\n"
    "5. Respond in the user's input language, in 4-6 bullet points total.\n"
)
    
    system_prompt = f"""
    [INPUT DATA]
    - Ticker: {ticker}
    - Model: The model trained on technical indicators
    - Predicted Action: {final_action.upper()}
    - Model Confidence: {probability*100:.1f}%
    (This is the model's predicted probability for the "{final_action}" class, 
    based on the current RSI and SMA-50 values below. It is a statistical output, not a certainty.)
    - Current RSI (14): {rsi:.2f}
    - Current Price: {current_price:.2f} USD
    - SMA-50: {sma_50:.2f} USD (price is {"above" if current_price > sma_50 else "below"} SMA-50)
    - Market News Summary: {news_summary if news_summary else "No recent news data available."}
    [TASK]
    Using ONLY the data above:
    1. Ticker summary: one neutral line summarize all the bullet points below.
    2. Explain what the RSI and current price vs SMA50 values indicate technically 
    (e.g., RSI > 70 = overbought, RSI < 30 = oversold, price above SMA50 = short-term uptrend bias). 
    Only interpret the numbers given — do not invent other indicators like MACD, volume, or resistance levels 
    unless they are explicitly provided above.
    3. Connect these two indicators to why the XGBoost model likely predicted "{final_action.upper()}" with {probability*100:.1f}% confidence.
    4. If Market News Summary is empty, state explicitly that no news data supports or contradicts the signal.
    5. Conclusion: Critical analysis based on generated info from bullet points 1 to 4, short, concise balanced risk considerations for {ticker}'s sector. Give final short-term and long term decision based on conclusion in short 2-3 words for each.
    6. Write this in italic: This is a model-generated statistical signal, providing data as reference for supplementing investors' decision making, not direct financial advice.

    [STYLE]
    - Exactly 7 bullet points total, no headers, no emojis, no horizontal rules.
    - Professional, calm tone. Avoid phrases like "aggressive bullish breakthrough" or "compelling opportunity".
    - Every technical claim must trace back to the RSI or SMA-50 values provided — no invented indicators.
    - Use **bold** (markdown) ONLY on the following, and nothing else:
        - Current RSI for {ticker}
        - Current Price for {ticker}
        - Current SMA-50 for {ticker}
        - The RSI value and its label (overbought/oversold/neutral)
    - Write bonus word in bold in bullet point 1 and bullet point 5 for word "Ticker summary:", "Conclusion:", "Short-term decision:", and "Long-term decision:" at the start of the sentence.
    - Do not bold entire sentences, or generic phrases — bold is reserved strictly for the data points above so it stays scannable, not noisy.
""" 
    try:
        model_response = client.models.generate_content(
            model = "gemini-2.5-flash",
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