import yfinance as yf
import json
import time
from google import genai
from google.genai import types
from datetime import datetime, timezone
import streamlit as st

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"], vertexai=False)

client = get_gemini_client()

def get_ticker_action_info(user_query):
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
 

def get_news_summary(ticker, limit = 5):
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
            
            if count >= limit: # Count if the amount of ticker context is larger than 5 then stop
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
    
def get_all_tickers_news(tickers, main_ticker=None, main_limit=5, other_limit=2):
    all_news = {}
    for tick in tickers:
        limit = main_limit if tick == main_ticker else other_limit
        summary = get_news_summary(tick, limit=limit)
        all_news[tick] = summary if summary else "No recent news data available."
    return all_news

def provide_recommendation(ticker, user_action, final_action, probability, all_news, rsi, sma_50, current_price, predicted_date, max_entries=2): 
    
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
    "5. Respond in the user's input language, in 4-6 bullet points total.\n")
    
    user_action = user_action.upper() if user_action else "GENERAL INQUIRY"
    has_technical_data = all(v is not None for v in [rsi, sma_50, current_price])

    rsi_display = f"{rsi:.2f}" if rsi is not None else "N/A (no data yet)"
    price_display = f"{current_price:.2f} USD" if current_price is not None else "N/A (no data yet)"
    sma_display = f"{sma_50:.2f} USD" if sma_50 is not None else "N/A (no data yet)"
    trend_note = (
        f"(price is {'above' if current_price > sma_50 else 'below'} SMA-50)"
        if has_technical_data else ""
    )
    main_news = all_news.get(ticker, "No news")
    other_news_text = ""
    for tick, summary in all_news.items():
        if tick == ticker:
            continue
        other_news_text += f"\n[{tick}]\n{summary}\n"
    today_date = datetime.now(timezone.utc).date().strftime("%d-%m-%Y")
    
    system_prompt = f"""
    [INPUT DATA]
    - Ticker: {ticker}
    - User Intent: Wants to know if they should "{user_action}" this stock.
    - Model: The model trained on technical indicators
    - Predicted Action: {final_action.upper()}
    - Model Confidence: {probability*100:.1f}%
    (This is the model's predicted probability for the "{final_action}" class, 
    based on the current RSI and SMA-50 values below. It is a statistical output, not a certainty.)
    - Current RSI (14): {rsi_display}
    - Current Price: {price_display}
    - SMA-50: {sma_display} {trend_note}
    - Market News Summary for {ticker}: {main_news}
    - Broader Market Context (other tracked tickers): {other_news_text if other_news_text else "No data for other tickers."}
    - Data based on date: {predicted_date}
    [TASK]
    Using ONLY the data above:
    0. "Note: the latest available data for {ticker} is from {predicted_date}; treat the analysis below with caution if the date is different from today ({today_date}), as market conditions may have changed."
    1. "Model prediction explained:" 
    Compare the user's intended action **{user_action.upper()}** with the model's predicted signal **{final_action.upper()}**.
    - If user_action is "GENERAL INQUIRY" or "GENERAL_INFO" (no specific buy/sell/hold intent stated): 
    skip the match/contradict comparison entirely. Instead, simply present the model's 
    signal as informational context, e.g.: "The model currently signals **{final_action.upper()}** at **{probability*100:.1f}%** confidence, based on current technical indicators."
    - If they MATCH: confirm alignment in one sentence, e.g.:
    "The model's **{final_action.upper()}** signal aligns with the user's intent to {user_action}, 
    supported by a {probability*100:.1f}% confidence level."
    - If they CONTRADICT (e.g., user wants to sell/buy but model signals otherwise): state the 
    mismatch clearly and neutrally in one sentence, e.g.:
    "The model currently signals **{final_action.upper()}** at {probability*100:.1f}% confidence, 
    which does not align with your intent to {user_action.upper()}."
    Do not use phrases like "action to WAIT" — always phrase it as "signals WAIT" or "predicted WAIT".    
    2. Explain what the RSI and current price vs SMA50 values indicate technically 
    (e.g., RSI > 70 = overbought, RSI < 30 = oversold, price above SMA50 = short-term uptrend bias). 
    Only interpret the numbers given — do not invent other indicators like MACD, volume, or resistance levels 
    unless they are explicitly provided above.
    3. If Market News Summary for {ticker} is empty, state explicitly that no news data supports or contradicts the signal.
    You may briefly reference the Broader Market Context only if directly relevant to {ticker}'s sector — 
    do not analyze other tickers individually, this app only forecasts {ticker}.
    4. Conclusion: Critical analysis based on generated info from bullet points 1 to 4, short, concise balanced risk considerations for {ticker}'s sector. Give final short-term and long term decision based on conclusion in short 4-5 words for each.
    5. Write this in italic: This is a model-generated statistical signal, providing data as reference for supplementing investors' decision making, not direct financial advice.

    [STYLE]
    - IMPORTANT: EXACTLY 8 BULLET POINTS IN TOTAL, no headers, no emojis, no horizontal rules. Short-term decision and long-term decision in one bullet point.
    - Professional, calm tone. Avoid phrases like "aggressive bullish breakthrough" or "compelling opportunity".
    - Every technical claim must trace back to the RSI or SMA-50 values provided — no invented indicators.
    - Use **bold** (markdown) ONLY on the following, and nothing else, act as a heading for each sentence:
        - {user_action.upper()} and {probability*100:.1f}%
        - Current RSI for {ticker}:
        - Current Price for {ticker}:
        - Current SMA-50 for {ticker}:
        - The RSI value and its label (overbought/oversold/neutral)
    - Write bonus word in bold in bullet point 1 and bullet point 5 for word "Model prediction explained:", "Market news:", "Broader market context:", "Conclusion:", "Short-term decision:", and "Long-term decision:" at the start of the sentence.
    - Do not bold entire sentences, or generic phrases — bold is reserved strictly for the data points above so it stays scannable, not noisy.
    
    [EXAMPLE FORMAT]
    - **Model prediction explained:**  The model currently signals WAIT at 42.9% confidence, which does not align with your intent to BUY.
    - **Current RSI for NVDA:** The RSI value of 49.67 indicates a neutral condition, as it is neither above 70 (overbought) nor below 30 (oversold).
    - **Current Price for NVDA:** At 202.78 USD, the price is below the Current SMA-50 for NVDA: of 209.24 USD, which typically suggests a short-term downtrend bias.
    - **Market news:** News for NVDA includes a report suggesting potential stock buybacks following a significant market value change. Additionally, the successful Nasdaq debut of chip giant SK Hynix, an AI powerhouse, is noted in the broader semiconductor sector.
    - **Broader market context:** The broader market context indicates that "Magnificent 7" stocks, which include NVDA, are trading at their cheapest valuation in over a decade. Furthermore, Corning has partnered with Nvidia to expand domestic manufacturing capacity for advanced optical solutions supporting AI computing.
    - **Conclusion:** The model's "WAIT" signal, supported by a low confidence level and a short-term downtrend bias from the price being below the SMA-50, contrasts with the user's "BUY" intent. While the RSI is neutral, broader market context shows NVDA as part of the "Magnificent 7" trading at lower valuations and engaging in strategic AI infrastructure partnerships. 
    - **Short-term decision:** X. **Long-term decision:** Y.
    
    *This is a model-generated statistical signal, providing data as reference for supplementing investors' decision making, not direct financial advice.*
    
    """ 
    
    
    
    for attempt in range(max_entries + 1):
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
            print(f"Error: {e}")
            if attempt < max_entries and "503" in str(e):
                time.sleep(3) # Wait for 3 seconds then retry
                continue
            raise