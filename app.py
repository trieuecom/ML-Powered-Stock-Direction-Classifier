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

st.title("🚀 AI Stock Direction Classifier")
st.markdown("Data is directly stored on **Supabase Cloud**.")

st.sidebar.header("🤖 Control the AI")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
features_list = ['RSI', 'SMA_50', 'Close', 'Volume']
list_tickers = st.sidebar.multiselect("What ticker do you want to choose?", options = tickers, default= ['AAPL', 'MSFT'])

if st.sidebar.button("Activate AI prediction!"):
    with st.spinner("Generating prediction...", show_time = True):
        scaler, rf, xgb = load_assets()
        if xgb is None or scaler is None:
            st.sidebar.error("xgb and scaler cannot be found")
        else:
            df_all = get_latest_data(tickers)
            if df_all is not None:
                latest_data = df_all.groupby('Ticker').tail(1)
                probs = make_prediction(xgb, scaler, latest_data, features_list)
                for tick, prob in zip(latest_data['Ticker'], probs):
                    advice = "BUY" if prob > 0.7 else "WAIT IS BETTER"
                    print(f" Ticker: {tick:6} | Action: {advice:16} | Probability: {prob:.2f}")
                    save_data_to_supabase(ticker = tick, action = advice, probability = prob)
                st.sidebar.success("Prediction complete ✅")    
                

if st.button("Download stock price data"):
    with st.spinner("In progress...", show_time = True):
        time.sleep(1)
        data = get_prediction_history(limit = 20)
        if data: 
            df = pd.DataFrame(data)
            cols = ["created_at", "ticker", "action", "probability"]
            df = df[cols]
            df["created_at"] = pd.to_datetime(df['created_at']).dt.strftime('%d-%m-%Y %H:%M')
            st.success("Here is the latest tickers' data!")
            st.dataframe(df, width = "stretch")
            df.drop_duplicates(subset = ['ticker'], keep = 'first')
            st.bar_chart(df.set_index('ticker')['probability'],width = "stretch")
        else: 
            print("Error: There is no data to be fetched!")
        