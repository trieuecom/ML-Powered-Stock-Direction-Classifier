from supabase import create_client
import streamlit as st

# Do not delete these variables, important info for importing data to Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SECRET_KEY"]
supabase = create_client(url, key)

def get_prediction_history(limit = 10):
    # select("*"), select all rows
    # limit = 10, limit top 10 latest data
    try:
        response = supabase.table("predictions") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return response.data
        
    except Exception as e:
        st.error(f"There is an error: {e}")
        return None
        
# def get_latest_ticker():
    
#     try:
#         # Getting the latest ticker based on created timestamp
#         response = supabase.table("predictions") \
#             .select("ticker") \
#             .order("created_at", desc=True) \
#             .limit(1) \
#             .execute() 
        
#         latest_ticker = response.data[0]["ticker"] #Response is a object in key-value, choose key as "ticker"
#         return latest_ticker   
#     except Exception as e:
#         st.error(f"There is an error: {e}")
#         return None
    
def get_latest_info_from_db(ticker):
    # If there is no ticker at all, return general action and general probability
    if not ticker: 
        return "GENERAL_INFO", 0.50, None, None, None 
    try:
        # Query info that equal the uppercase ticker inputted only
        response = supabase.table("predictions") \
            .select("action, probability", "rsi", "sma_50", "current_price") \
            .eq("ticker", ticker.upper()) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute() 
        
        if response.data and len(response.data) > 0:
            latest_info = response.data[0]
            return (
                latest_info.get("action", "wait"), 
                latest_info.get("probability", 0.5), 
                latest_info.get("rsi"), 
                latest_info.get("sma_50"), 
                latest_info.get("current_price")
            )
        return "GENERAL_INFO", 0.50, None, None, None
    except Exception as e:
        print(f"There is an error from get_latest_info_from_db: {e}")
        return None, None, None, None, None
    
