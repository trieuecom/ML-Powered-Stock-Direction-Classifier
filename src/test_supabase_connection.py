from supabase import create_client  
import os

SUPABASE_URL = "https://ybsfnpixzggwelyteiuw.supabase.co"
SUPABASE_KEY = "sb_publishable_Rhl3c91z8mvJjxPXSdrK5A_0Zie6H_U"

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
