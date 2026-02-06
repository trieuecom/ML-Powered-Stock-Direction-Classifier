import streamlit as st
import pandas as pd
import time 
from src.predict import *
from src.fetch_data import get_prediction_history

# Configure the application page
st.set_page_config(page_title = "Stock Direction", 
                   page_icon = "📊", 
                   layout = "centered",
                   initial_sidebar_state = "auto",
                   menu_items = {
                       'About': "# This is an *extremely* cool app!"
                   })
# Main website headings
st.title("🚀 AI Stock Direction Classifier")
st.markdown("Data is directly stored on **Supabase Cloud**.")

# Sidebar control
st.sidebar.header("🤖 Control the AI")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
features_list = ['RSI', 'SMA_50', 'Close', 'Volume']
list_tickers = st.sidebar.multiselect("Pick tickers to predict:", options = tickers, default= ['AAPL', 'MSFT'])


if "needs_refresh" not in st.session_state:
    st.session_state.needs_refresh = False
if "show_results" not in st.session_state:
    st.session_state.show_results = False
    
# Refresh and clear buttons
col_refresh, col_clear = st.columns([2, 2])
with col_refresh:
    if st.button("📊 View/Refresh Results"):
        st.session_state.show_results = not st.session_state.show_results
        if st.session_state.show_results:
            st.session_state.needs_refresh = True
with col_clear:
    if st.button("Clear Database 🗑️"):
        delete_all_history()
        st.session_state.needs_refresh = True 
        st.error("All prediction data has been deleted!")
        
# Show prediction history button
if st.session_state.show_results or st.session_state.needs_refresh:
    with st.spinner("In progress...", show_time = True):
        time.sleep(1)
        data = get_prediction_history(limit = 20)
        if data: 
            df = pd.DataFrame(data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Create a display table
            cols = ["created_at", "ticker", "action", "probability"]
            df_display = df[cols].copy()
            df_display["created_at"] = pd.to_datetime(df_display['created_at']).dt.strftime('%d-%m-%Y %H:%M')
            df_display = df_display.sort_values(by = 'ticker', ascending = True)

            # Success message 
            st.success("Here is the latest tickers' data!")
            st.dataframe(df_display, width = "stretch")
            # Drop duplicates
            df_display = df_display.drop_duplicates(subset = ['ticker'], keep = 'first')
            
            # Create a barchart for each stock group
            df_for_barchart = df_display.sort_values("created_at").groupby("ticker").tail(1).sort_values(["ticker", "created_at"], ascending = True)
            st.bar_chart(df_for_barchart.set_index('ticker')['probability'],width = "stretch")
            
            st.session_state.needs_refresh = False
        else: 
            st.error("Database is empty. Activate AI to see data.")
                

# Main AI prediction button
if st.sidebar.button("Activate AI prediction!"):
    if not list_tickers: 
        st.sidebar.warning("Please select at least one ticker!")
    else:
        with st.spinner("Generating prediction...", show_time = True):
            scaler, rf, xgb = load_assets()
            if xgb is None or scaler is None:
                st.sidebar.error("xgb and scaler cannot be found")
            else:
                df_all = get_latest_data(list_tickers) # get data from selected tickers list
                if df_all is not None:
                    latest_data = df_all.groupby('Ticker').tail(1)
                    probs = make_prediction(xgb, scaler, latest_data, features_list)
                    for tick, prob in zip(latest_data['Ticker'], probs):
                        advice = "BUY" if prob > 0.7 else "WAIT IS BETTER"
                        print(f" Ticker: {tick:6} | Action: {advice:16} | Probability: {prob:.2f}")
                        save_data_to_supabase(ticker = tick, action = advice, probability = prob)
                    st.sidebar.success("Prediction complete ✅")
                    st.session_state.show_results = True
                    st.session_state.needs_refresh = True    
                    st.rerun()


