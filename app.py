import streamlit as st
import pandas as pd
from src.fetch_data import get_prediction_history
import time 

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

if st.button("Download stock price data"):
    with st.spinner("In progress...", show_time = True):
        time.sleep(3)
        data = get_prediction_history(limit = 20)
        if data: 
            df = pd.DataFrame(data)
            cols = ["created_at", "ticker", "action", "probability"]
            df = df[cols]
            df["created_at"] = pd.to_datetime(df['created_at']).dt.strftime('%d-%m-%Y %H:%M')
            st.success("Done!")
            st.dataframe(df, width = "stretch")
            st.bar_chart(df.set_index('ticker')['probability'],width = "stretch")
        else: 
            print("Error: There is no data to be fetched!")
        