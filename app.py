import streamlit as st
import pandas as pd
import time 
import uuid
from src.predict import *
from src.fetch_data import *
from src.rag_logic import *
from datetime import datetime


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
st.sidebar.header("Give your preferred tickers to the model to see report:")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
features_list = ['RSI', 'SMA_50', 'Close', 'Volume']
list_tickers = st.sidebar.multiselect(label="Pick one/multiple tickers:", options = tickers)

if "session" not in st.query_params: # Streamlit API to write query parameters in URL
    st.query_params.session = str(uuid.uuid4()) # Create a random session id to store in database

session_id = st.query_params.session # If there is a session already, there will be a session id
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history(session_id)
if "needs_refresh" not in st.session_state:
    st.session_state.needs_refresh = False
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "show_chat_history" not in st.session_state:
    st.session_state.show_chat_history = False

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
                    for tick, prob, rsi, sma_50, close_price in zip(latest_data['Ticker'], probs, latest_data["RSI"], latest_data["SMA_50"], latest_data["Close"]):
                        advice = "" 
                        if prob > 0.7:
                            advice = "buy"
                        elif prob < 0.3:
                            advice = "sell"
                        else:
                            advice = "wait"
                        print(f" Ticker: {tick:6} | Action: {advice:16} | Probability: {prob:.2f} | Close: {close_price:.2f} | RSI: {rsi:.2f} | SMA 50: {sma_50:.2f}")
                        save_data_to_supabase(ticker = tick, action = advice, probability = prob, rsi = rsi, sma_50 = sma_50, current_price = close_price)
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
        user_query = st.text_input("**What financial decision are you looking for today?** *Please provide your ticker and action to have more insightful report.*")
        submit_button = st.form_submit_button(label="Send")
    
    if user_query and submit_button:
        st.session_state.show_chat_history = True
        # Step 1: Saving queries into chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query, "timestamp": datetime.now()}) # Append to the session state list with role and the query's content
        save_chat_message(session_id, "user", user_query)
        with st.spinner("Thinking..."):
            try:
                # Step 2: Using Gemini API to extract user's current ticker and action, if there is an error, it will go to except block
                extracted_ticker, extracted_action = get_ticker_action_info(user_query)
                # Step 3.1: Edge case where user did not input ticker info in the query
                
                # If the query is too general without the ticker info, push a notification for the user to specify the ticker
                if not extracted_ticker:
                   missing_ticker_msg = (
                        "❗ Please specify a ticker for me to help you better analyze the market. "
                        "For example: \"Should I buy AAPL?\" or \"What's the outlook for MSFT?\""
                    )
                   st.session_state.chat_history.append({"role": "assistant", "content": missing_ticker_msg})
                   save_chat_message(session_id, "assistant", missing_ticker_msg)
                   st.rerun()

                
                extracted_action_db, extracted_prob_db, extracted_rsi_db, extracted_sma50_db, extracted_current_price_db = get_latest_info_from_db(extracted_ticker)
                valid_action_list = ["buy", "acquire", "purchase", "long", "sell", "dump", "short", "liquidate", "hold", "keep", "wait", "neutral"]
                
                extracted_action = extracted_action.strip().lower()

                # Step 3.2: Edge case when user ask general questions
                if extracted_prob_db == 0.5 or not extracted_action_db:
                    # CASE 1: Database do not have the ticker
                    st.toast(f"⚠️ {extracted_ticker} is not predicted by the system yet, we will give you general information.")
                    final_action = "wait" # Force into wait status as information is still vague
                    extracted_prob_db = 0.5
                    
                elif extracted_action not in valid_action_list or extracted_action == "":
                    # CASE 2: User asks general question
                    st.toast("Please tell us more on your financial action for us to provide you with a more detailed analysis. Do you want to sell, buy or keep any stocks?")
                    final_action = "wait" # Force into wait status as action is still vague
                    extracted_prob_db = 0.5
                else: 
                    # CASE 3: There is 
                    final_action = extracted_action_db.lower()
                    
                # Get all news if there is more than one extracted ticker
                all_news = get_all_tickers_news(tickers, main_ticker=extracted_ticker)
                # Get recommend result from Gemini based on final action
                recommended_result = provide_recommendation(
                                    extracted_ticker,
                                    extracted_action, 
                                    final_action, 
                                    extracted_prob_db, 
                                    all_news, 
                                    extracted_rsi_db, 
                                    extracted_sma50_db, 
                                    extracted_current_price_db
                )
                st.session_state.chat_history.append({"role": "assistant", "content": recommended_result})
                save_chat_message(session_id, "assistant", recommended_result)
                st.rerun() # Reload the app after the logic is completed!            
                
            except Exception as e:
                print(f"There is an error with Gemini: {e}")
                error_msg = "🤖 Our model is temporarily resting due to daily free quota limits. Please retry in a few seconds."
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                save_chat_message(session_id, "assistant", error_msg)
                st.warning(error_msg)

# Show prediction history button
if st.session_state.show_results:
    with st.spinner("In progress..."):
        data = get_prediction_history(limit = 3)
        if data: 
            df = pd.DataFrame(data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Create a display table
            cols = ["id", "created_at", "ticker", "action", "probability","rsi", "sma_50", "current_price"]
            df_display = df[cols].copy()
            df_display["created_at"] = pd.to_datetime(df_display['created_at'])
            df_display["created_at"] = df_display['created_at'].dt.tz_convert('UTC').dt.strftime('%H:%M %d-%m-%Y UTC')
            df_display = df_display.sort_values(by = 'id', ascending = False)

            # Success message 
            st.success("Here is the latest tickers' data!")
            st.dataframe(df_display, width = "stretch", hide_index=True, column_config= {
                "id" : 
                    st.column_config.NumberColumn("ID", width="small"),
                "created_at":
                    st.column_config.TextColumn("Created At"),
                "ticker":
                    st.column_config.TextColumn("Ticker"),
                "action" : 
                    st.column_config.SelectboxColumn(
                    "Action", 
                    options = ["buy", "sell", "wait"],
                    # Format the predictions value into friendly UI 
                    format_func = lambda x: {"buy": "📈 BUY", "sell" : "📉 SELL", "wait" : "📊 HOLD"}.get(x, x)
                ),
                "probability" : 
                    st.column_config.NumberColumn("Probability", format = "%.2f"),
                 "rsi" : 
                    st.column_config.NumberColumn("RSI (14 days)", format = "%.2f"),
                 "sma_50" : 
                    st.column_config.NumberColumn("SMA 50", format = "%.2f"),
                 "current_price" : 
                    st.column_config.NumberColumn("Current Price", format = "%.2f")

            })
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

st.toggle("Open/Close Chat History", key = "show_chat_history") # Use key in toggle to save the show chat history session state  
             
if st.session_state.show_chat_history:
    st.subheader("Your Personal Financial Analysis Chat History")
    st.write("---")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"]) # Display the analysed result from the chatbot
            if "timestamp" in m:
                st.caption(m["timestamp"].strftime("%H:%M %d-%m-%y"))
    
    
    
    




