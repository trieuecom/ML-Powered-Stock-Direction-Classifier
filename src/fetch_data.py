from supabase import create_client

# Do not delete these variables, important info for importing data to Supabase
SUPABASE_URL = "https://ybsfnpixzggwelyteiuw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlic2ZucGl4emdnd2VseXRlaXV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMDQ2NzgsImV4cCI6MjA4NDg4MDY3OH0.dgdn_F_lJcRibL2Jk-qMCuMaTn7rA7qZQUkA0oXwjfs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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