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
    "မနက်ပိုင်းနှင့် ညနေပိုင်း ဈေးကွက်လှုပ်ရှားမှု (Velocity & Momentum) များကို သီးသန့်စီ စောင့်ကြည့်တွက်ချက်ပေးမည့်စနစ်။"
)

# --- Initialize Session State for Data Logging ---
if "history_data" not in st.session_state:
    st.session_state.history_data = []

# --- Morning Session Calculation Logic ---
def calculate_morning_prediction():
    # မနက်ပိုင်း ဈေးကွက်စဖွင့်ချိန်မှ 11:30 AM အထိ Accumulated Data ကို အခြေခံသည့် Logic
    try:
        url = "https://www.set.or.th/en/home"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        # မနက်ပိုင်း သီးသန့် Parsing / Calculation
    except Exception as e:
        pass
    
    # Morning Candidate Set (ဥပမာ - မနက်ပိုင်း သီးသန့်တွက်ချက်ချက်)
    morning_candidates = "13579"
    return morning_candidates

# --- Afternoon Session Calculation Logic ---
def calculate_afternoon_prediction():
    # နေ့လယ်ပိုင်း ဈေးကွက်စဖွင့်ချိန်မှ 3:35 PM အထိ Accumulated Data ကို အခြေခံသည့် Logic
    try:
        url = "https://www.set.or.th/en/home"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        # ညနေပိုင်း သီးသန့် Parsing / Calculation
    except Exception as e:
        pass
    
    # Afternoon Candidate Set (ဥပမာ - ညနေပိုင်း သီးသန့်တွက်ချက်ချက်)
    afternoon_candidates = "24680"
    return afternoon_candidates

# --- မှတ်တမ်းတင်ရန် Function (Session အလိုက် သီးသန့်) ---
def log_prediction(session_name, candidate_set):
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    
    # ယခင်နေ့စွဲနှင့် Session တူသည်များကို စစ်ဆေးပြီး Update လုပ်ရန် သို့မဟုတ် အသစ်ထည့်ရန်
    existing_entry = None
    for item in st.session_state.history_data:
        if item["Date"] == current_date and item["Session"] == session_name:
            existing_entry = item
            break
            
    if existing_entry:
        existing_entry["Candidate Set"] = candidate_set
    else:
        st.session_state.history_data.append({
            "Date": current_date,
            "Session": session_name,
            "Candidate Set": candidate_set,
            "Actual Value": "Pending"
        })

# --- Morning Session (12:01 PM Target) ---
st.subheader("🌅 Morning Session (12:01 PM Target)")
st.text("စောင့်ကြည့်မည့်ကာလ: မနက်ဈေးကွက်စဖွင့်ချိန် မှ 11:30 AM အထိ")

if st.button("📊 Calculate Morning Prediction"):
    morning_candidates = calculate_morning_prediction()
    st.success(f"Morning Candidate Set: {morning_candidates}")
    log_prediction("Morning Session", morning_candidates)

# --- Afternoon Session (4:30 PM Target) ---
st.subheader("🌇 Afternoon Session (4:30 PM Target)")
st.text("စောင့်ကြည့်မည့်ကာလ: နေ့လယ်ဈေးကွက်စဖွင့်ချိန် မှ 3:35 PM အထိ")

if st.button("📊 Calculate Afternoon Prediction"):
    afternoon_candidates = calculate_afternoon_prediction()
    st.success(f"Afternoon Candidate Set: {afternoon_candidates}")
    log_prediction("Afternoon Session", afternoon_candidates)

# --- Performance & History Tracking Section ---
st.subheader("📊 Performance & History Tracking")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်းမရှိသေးပါ။")

# --- Manual Override for Actual Value (Session အလိုက် ရွေးချယ်နိုင်ရန်) ---
st.markdown("---")
st.subheader("တကယ်ကျလာသော တန်ဖိုး (Actual Value) ထည့်သွင်းရန်")
with st.form("actual_value_form"):
    selected_session = st.selectbox("Session ရွေးချယ်ရန်:", ["Morning Session", "Afternoon Session"])
    actual_input = st.text_input("Actual Value (ဥပမာ - 5 digits သို့မဟုတ် တန်ဖိုး):")
    submit_actual = st.form_submit_button("Update Actual Value")
    
    if submit_actual and actual_input:
        current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        updated = False
        for item in st.session_state.history_data:
            if item["Date"] == current_date and item["Session"] == selected_session:
                item["Actual Value"] = actual_input
                updated = True
                
        if updated:
            st.success(f"{selected_session} အတွက် Actual Value အောင်မြင်စွာ အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
            st.rerun()
        else:
            st.warning("ယနေ့အတွက် သက်ဆိုင်ရာ Session မှတ်တမ်း မတွေ့ရှိရသေးပါ။ ကျေးဇူးပြု၍ Prediction အရင်ထုတ်ပါ။")
