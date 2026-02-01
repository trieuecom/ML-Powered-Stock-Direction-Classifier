from supabase import create_client  
import os

SUPABASE_URL = "https://ybsfnpixzggwelyteiuw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlic2ZucGl4emdnd2VseXRlaXV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMDQ2NzgsImV4cCI6MjA4NDg4MDY3OH0.dgdn_F_lJcRibL2Jk-qMCuMaTn7rA7qZQUkA0oXwjfs"

supabase = create_client(supabase_url = SUPABASE_URL, supabase_key = SUPABASE_KEY)

# Insert some data into the supabase database
test_data = {
    "ticker" : "AAPL",
    "action" : "BUY",
    "probability" : 0.8
}

try: 
    server_response = supabase.table("predictions").insert(test_data).execute()
    print("Data has been uploaded on Supabase successfully!")
    print(f"Response from server: {server_response}" )
except Exception as e:
    print("There is an error: ", e)
