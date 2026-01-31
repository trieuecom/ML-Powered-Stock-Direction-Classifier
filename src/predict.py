import pandas as pd
import yfinance as yf
import joblib
import pandas_ta as ta
import os
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import StandardScaler
from supabase import create_client

# Do not delete these variables, important info for importing data to Supabase
SUPABASE_URL = "https://ybsfnpixzggwelyteiuw.supabase.co"
SUPABASE_KEY = "sb_publishable_Rhl3c91z8mvJjxPXSdrK5A_0Zie6H_U"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load scaler and models from models folder function
def load_assets():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_joined_path = os.path.join(current_dir,"..","models")
    try:
        # Take the current directory of this predict.py file
        scaler = joblib.load(os.path.join(model_joined_path,'scaler.pkl'))
        xgb_model = joblib.load(os.path.join(model_joined_path,'best_xgb_model.pkl'))
        rf_model = joblib.load(os.path.join(model_joined_path,'best_random_forest_model.pkl'))
        print('All models and scaler have been loaded successfully!')
        return scaler, rf_model, xgb_model
    except Exception as e:
        print(f'There is an error {e} when loading the models/scaler')
        return None, None, None
        

def get_latest_data(tickers):
    data_list = []
    for ticker in tickers:
        try:    
            df = yf.download(tickers=ticker, period='2y', interval= '1d')
            if df.empty:
                print(f'There is no data for {ticker}')
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)   
                
            df['RSI'] = ta.rsi(df['Close'], length=14)        
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['Ticker'] = ticker
            
            df.dropna(subset = ['RSI', 'SMA_50'], inplace = True)            
            
            if not df.empty:
                data_list.append(df)
                print(f"The data of {ticker} ticker has been fetched succesfully!")
            
        except Exception as e:
            print(f"There is an error when fetching the data of {ticker}!")
    if not data_list: return None       
    final_data = pd.concat(data_list)
    return final_data

def make_prediction(model, scaler, data, features_list):
    X = data[features_list]
    X_scaled = scaler.transform(X.values)
    prob_result = model.predict_proba(X_scaled)[:,1]
    return prob_result

def save_data_to_supabase(ticker, action, probability):
    try:
        data = {
            "ticker" : ticker,
            "action" : action,
            "probability" : float(probability)
        }
        server_response = supabase.table("predictions").insert(data).execute()
        print("The data has been imported into 'predictions' table successfully!")
        print(f"Response from server: {server_response}" )
    except Exception as e:
        print(f"There is an error: ", e)


if __name__ == "__main__":
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    features_list = ['RSI', 'SMA_50', 'Close', 'Volume']
    # STEP 1: LOAD THE MODEL AND SCALER
    scaler, rf, xgb = load_assets()
    # STEP 2: GET THE LATEST DATA
    df_all = get_latest_data(tickers)
    
    if df_all is not None:
        latest_data = df_all.groupby('Ticker').tail(1)
        # STEP 3: MAKE PREDICTION
        probs = make_prediction(xgb, scaler, latest_data, features_list)
        # STEP 4: SHOW RESULTS
        for tick, prob in zip(latest_data['Ticker'], probs):
            advice = "BUY" if prob > 0.7 else "WAIT IS BETTER"
            print(f" Ticker: {tick:6} | Action: {advice: 16} | Probability: {prob:.2f}")
            save_data_to_supabase(ticker = tick, action = advice, probability = prob)
            
        