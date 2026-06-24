# 🚀 End-to-end ML-Powered-Stock-Direction-Classifier

A real-time stock trend prediction application that combines the power of **Machine Learning (XGBoost)** and **Cloud Database (Supabase)** and displayed UI using **Streamlit**. 

This app analyzes the **probability of price movements (Up/Down) for popular tickers** based on key technical indicators.

---

## ✨ Key Features

* **AI-Powered Inference:** Utilizes a trained XGBoost model to provide directional probabilities and actionable advice (`BUY` vs. `WAIT`).
* **Real-time Market Data:** Automatically fetches the latest financial data from Yahoo Finance via the `yfinance` API.
* **Cloud Persistence:** Integrated with **Supabase (PostgreSQL)** to store and retrieve prediction history.
* **Dynamic User Interface:**
    * **Ticker Selection:** Multi-select functionality to choose specific stocks for analysis.
    * **Interactive Dashboard:** Toggleable views for dataframes and charts to optimize screen real estate.
    * **Visual Analytics:** Probability results are visualized using interactive bar charts.
---

## 🛠 Tech Stack

| Technology | Purpose |
| :--- | :--- |
| **Streamlit** | Web interface & State management |
| **XGBoost & Scikit-learn** | Machine Learning model & Data scaling |
| **Supabase** | Backend Database (PostgreSQL) |
| **Pandas & Pandas-TA** | Data engineering & Technical analysis |
| **YFinance** | Real-time market data source |

---

## 🚀 Getting Started

### 1. Clone the Project
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git](https://github.com/trieuecom/ML-Powered-Stock-Direction-Classifier.git))
cd ML-Powered-Stock-Direction-Classifier
```

### 2. Setup Virtual Environment (Recommended)
```bash
python -m venv venv
```
```bash
# Windows
venv\Scripts\activate
```
```bash
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a .streamlit/secrets.toml file in the root directory and add your Supabase credentials:
```bash
SUPABASE_URL = "https://ybsfnpixzggwelyteiuw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlic2ZucGl4emdnd2VseXRlaXV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMDQ2NzgsImV4cCI6MjA4NDg4MDY3OH0.dgdn_F_lJcRibL2Jk-qMCuMaTn7rA7qZQUkA0oXwjfs"
```
### 5. Run the Application
```bash
streamlit run app.py
```

---
## 📂 Project Structure

* app.py: Main entry point for the Streamlit UI.

* src/predict.py: Contains model loading logic and inference functions.

* src/fetch_data.py: Handles API calls to Yahoo Finance and Supabase interactions.

* models/: Stores serialized model files (.pkl) and scalers.

* .gitignore: Protects sensitive files like secrets.toml and venv/.

---
## 📸 Screenshots
<img width="1920" height="1097" alt="image" src="https://github.com/user-attachments/assets/e6145f4a-7f42-42fc-9bd1-0e35eb6dbf77" />

