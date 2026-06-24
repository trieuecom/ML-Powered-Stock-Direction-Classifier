from supabase import create_client
import streamlit as st

# Do not delete these variables, important info for importing data to Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SECRET_KEY"]
supabase = create_client(url, key)

def get_prediction_history(limit=10):
    # select("*"), select all rows
    # limit = 10, limit top 10 latest data
    try:
        response = supabase.table("predictions") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        return response.data
        
    except Exception as e:
        print(f"There is an error", e)
        

if __name__ == "__main__":
    data = get_prediction_history()
    if data: 
        print(f"Data: {data} is fetched successfully")
        print(data)
    else:
        print("Error: There is no data to be fetched!")