from supabase import create_client  
from dotenv import load_dotenv
import os

# Load Supabase Key and URL from local first
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

if not SUPABASE_SECRET_KEY or not SUPABASE_URL:
    raise ValueError("Please configure Supabase key and Supabase URL first!")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

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
