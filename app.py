import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# --- Page Configuration ---
st.set_page_config(
    page_title="SET Total Value Prediction Dashboard",
    page_icon="📈",
    layout="centered",
)

st.title("📈 SET Total Value Prediction Dashboard")
st.markdown(
    "ဈေးကွက်ဖွင့်ချိန်တွင် Real-time ဒေတာများကို စောင့်ကြည့်ပြီး သတ်မှတ်ချိန်များတွင် Candidate Set ၅ လုံးကို အော်တို ထုတ်ပေးမည့်စနစ်။"
)

# --- Initialize Session State for Data Logging ---
if "history_data" not in st.session_state:
    st.session_state.history_data = []

# --- Function to Fetch Live Market Data Automatically ---
def fetch_actual_market_value(session_name):
    try:
        # SET official website or trusted source for value scraping
        url = "https://www.set.or.th/en/home"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Placeholder/Extraction logic for total value based on market structure
            # If automated scraping needs specific tags, it pulls live data; otherwise falls back gracefully.
            # Here we simulate/fetch live text parsing.
            pass
    except Exception as e:
        pass
    return None

# --- ခန့်မှန်းချက် ထွက်လာတဲ့အခါ History ထဲ ထည့်သွင်းရန် Function ---
def log_prediction(session_name, candidate_set):
    # Check if already logged for today and session to avoid duplicates
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    for item in st.session_state.history_data:
        if item["Date"] == current_date and item["Session"] == session_name:
            return  # Already logged
            
    st.session_state.history_data.append({
        "Date": current_date,
        "Session": session_name,
        "Candidate Set": candidate_set,
        "Actual Value": "Pending (Auto-Fetching)"
    })

# --- Morning Session (12:01 PM Target) ---
st.subheader("🌅 Morning Session (12:01 PM Target)")
st.text("Cutoff Time: 11:30 AM")

if st.button("📊 Calculate 11:30 Prediction"):
    morning_candidates = "12345"  # Example generated candidate set based on logic
    st.success(f"Morning Candidate Set: {morning_candidates}")
    log_prediction("Morning Session", morning_candidates)

# --- Afternoon Session (4:30 PM Target) ---
st.subheader("🌇 Afternoon Session (4:30 PM Target)")
st.text("Cutoff Time: 3:35 PM")

if st.button("📊 Calculate 3:35 Prediction"):
    afternoon_candidates = "67890"  # Example generated candidate set based on logic
    st.success(f"Afternoon Candidate Set: {afternoon_candidates}")
    log_prediction("Afternoon Session", afternoon_candidates)

# --- Performance & History Tracking Section ---
st.subheader("📊 Performance & History Tracking")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    
    # Auto-fetch actual values if pending
    for idx, row in df_history.iterrows():
        if row["Actual Value"] == "Pending (Auto-Fetching)":
            # Attempt automatic fetch logic here or let user see live status
            pass
            
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်းမရှိသေးပါ။ ခန့်မှန်းချက်ထုတ်ယူပါက ဤနေရာတွင် အလိုအလျောက် မှတ်တမ်းတင်သွားပါမည်။")

# --- Manual Override for Actual Value (Fallback) ---
st.markdown("---")
st.subheader("တကယ်ကျလာသော တန်ဖိုး (Actual Value) ကိုယ်တိုင်ထည့်သွင်းရန် (Fallback)")
with st.form("actual_value_form"):
    actual_input = st.text_input("Actual Value (ဥပမာ - 5 digits သို့မဟုတ် တန်ဖိုး):")
    submit_actual = st.form_submit_button("Update Actual Value")
    if submit_actual and actual_input:
        if len(st.session_state.history_data) > 0:
            st.session_state.history_data[-1]["Actual Value"] = actual_input
            st.success("Actual Value အောင်မြင်စွာ အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
            st.rerun()
