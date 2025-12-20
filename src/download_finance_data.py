# Import imporantant libraries
import yfinance as yf
import pandas as pd

def download_finance_data(ticker, start_date, end_date):
    """_summary_

    Args:
        ticker (_type_): The stock ticker symbol to extract on Yahoo Finance (e.g. AAPL is short for Apple Inc.)
        start_date (_type_): The start date for the historical data extraction of the ticker, in "YYYY-MM-DD" format
        end_date (_type_): The end date for the historical data extraction of the ticker, in "YYYY-MM-DD" format
    """
    # Download historical data from Yahoo Finance dataset
    data = yf.download(ticker, start=start_date, end=end_date)
    # Save the data to a CSV file
    data.to_csv(f"data/{ticker}_raw.csv")
    print(f"Raw data {ticker} downloaded and saved into CSV file.")
    
    
    if __name__ == "__main__":
        # Example usage of download_finance_data function
        download_finance_data("AAPL", "2020-01-01", "2023-01-01")
    