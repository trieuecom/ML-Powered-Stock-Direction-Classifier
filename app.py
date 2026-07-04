import streamlit as st
import pandas as pd
import time 
from src.predict import *
from src.fetch_data import *
from src.rag_logic import *

# Configure the application page
st.set_page_config(page_title = "Stock Direction App", 
                   page_icon = "📊", 
                   layout = "wide",
                   initial_sidebar_state = "auto",
                   menu_items = {
                       'About': " End-to-end application to predict Big Tech's stock movements,using Streamlit-powered dashboard for real-time data retrieval."
                   })
# Main website headings
st.title("🚀 AI Stock Direction Classifier")
st.markdown("Data is directly stored on **Supabase Cloud**.")

# Sidebar control
st.sidebar.header("Choose your tickers to predict")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
features_list = ['RSI', 'SMA_50', 'Close', 'Volume']
list_tickers = st.sidebar.multiselect("Pick tickers to predict:", options = tickers)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "needs_refresh" not in st.session_state:
    st.session_state.needs_refresh = False
if "show_results" not in st.session_state:
    st.session_state.show_results = False

# Main prediction button
if st.sidebar.button("Activate prediction!"):
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
                        advice = "BUY 💵" if prob > 0.7 else "WAIT IS BETTER ⌛"
                        print(f" Ticker: {tick:6} | Action: {advice:16} | Probability: {prob:.2f}")
                        save_data_to_supabase(ticker = tick, action = advice, probability = prob)
                    st.sidebar.success("Prediction complete ✅")
                    st.session_state.show_results = True
                    st.session_state.needs_refresh = True    
                    st.rerun()
   
# Refresh and clear buttons
col_del_refresh, col_query = st.columns([1.5, 6])
with col_del_refresh:
    if st.button("📊 View/Refresh Results"):
        st.session_state.show_results = not st.session_state.show_results
        if st.session_state.show_results:
            st.session_state.needs_refresh = True
    if st.button("Clear Database 🗑️"):
        with st.spinner("Deleting all data rows..."):
            delete_all_history()
            st.toast("✅ All prediction data has been deleted!")     

    with col_query:
        with st.form(key="chat_form", clear_on_submit=True):
            user_query = st.text_input("What financial decision are you looking for today?")
            submit_button = st.form_submit_button(label="Send")
        
        if user_query and submit_button:
            # Step 1: Saving queries into chat history
            st.session_state.chat_history.append({"role": "user", "content": user_query}) # Append to the session state list with role and the query's content
            
            with st.spinner("Your personal analyst is working, please wait..."):
                # Step 2: Using Gemini API to extract query info
                extracted_ticker, extracted_action = get_ticker_action_info(user_query)
                            
                # Step 2.1: Edge case where user did not input ticker info in the query
                if not extracted_ticker:
                    extracted_ticker = get_latest_ticker()
                    st.toast(
                        f"❗ **Ticker missing!** Please specify a ticker next time.\n"
                        f"ℹ️ Auto-analyzing the latest active ticker from database: **{extracted_ticker}**"
                    )
                
                extracted_action_db, extracted_prob_db = get_latest_info_from_db(extracted_ticker)

                # Step 2.2: Edge case when user ask general questions
                if extracted_prob_db == 0.5 or not extracted_action_db:
                    # CASE 1: Database do not have the ticker
                    st.toast(f"⚠️ {extracted_ticker} is not predicted by the system yet, we will give you general information.")
                    final_action = "WAIT IS BETTER ⌛" # Ép về trạng thái chờ, không cho khuyên BUY bậy bạ kkk
                    extracted_prob_db = 0.5
                    
                elif not extracted_action or extracted_action == "GENERAL_INFO":
                    # CASE 2: User asks general question
                    st.toast("Please tell us more on your financial action for us to provide you with a more detailed analysis. Do you want to sell, buy or keep any stocks?")
                    # If user action is general, take the action from model prediction
                    final_action = extracted_action_db 
                else: 
                    # CASE 3: There is 
                    final_action = extracted_action
            
            # Step 3: Get news summary and recommendations from Gemini
            news_summary = get_news_summary(extracted_ticker)
            # Get recommend result from Gemini based on final action
            recommended_result = provide_recommendation(extracted_ticker, final_action, extracted_prob_db, news_summary)
            
            # Append model's recommended result to chat history
            if recommended_result:
                st.session_state.chat_history.append({"role": "assistant", "content": recommended_result})
                st.rerun() # Reload the app after the logic is completed!
             

# Show prediction history button
if st.session_state.show_results:
    with st.spinner("In progress..."):
        time.sleep(1)
        data = get_prediction_history(limit = 20)
        if data: 
            df = pd.DataFrame(data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Create a display table
            cols = ["id", "created_at", "ticker", "action", "probability"]
            df_display = df[cols].copy()
            df_display["created_at"] = pd.to_datetime(df_display['created_at']).dt.strftime('%H:%M %d-%m-%Y')
            df_display = df_display.sort_values(by = 'id', ascending = True)

            # Success message 
            st.success("Here is the latest tickers' data!")
            st.dataframe(df_display, width = "stretch", hide_index=True)
            # Drop duplicates
            df_display = df_display.drop_duplicates(subset = ['ticker'], keep = 'first')
            
            # Create a barchart for each stock group
            df_for_barchart = df_display.sort_values("created_at").groupby("ticker").tail(1).sort_values(["ticker", "created_at"], ascending = True)
            st.bar_chart(df_for_barchart.set_index('ticker')['probability'],width = "stretch")
            
            st.session_state.needs_refresh = False
        else: 
            st.toast("🗑️ Database is empty! Activate model prediction to see data.")
            # After display result we turn off the notification
            st.session_state.show_results = False

show_chat_history = st.toggle("Open/Close Chat History", value = False)  
if show_chat_history:      
    st.subheader("Financial Analysis History")
    st.write("---")
    
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"]) # Display the analysed result from the chatbot          




