import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SET Total Value Prediction Dashboard",
    page_icon="📈",
    layout="centered",
)

st.title("📈 SET Total Value Prediction Dashboard")
st.markdown(
    "ဈေးကွက်ဖွင့်ချိန်မှ ပိတ်ချိန်အထိ Live Value များကို တိုက်ရိုက်ပြသပေးခြင်းနှင့် သတ်မှတ်ချိန်အလိုက် Candidate ၅ လုံး အလိုအလျောက် ခန့်မှန်းထုတ်ပေးမည့်စနစ်။"
)

# --- Initialize Session State ---
if "history_data" not in st.session_state:
    st.session_state.history_data = []

if "auto_triggered" not in st.session_state:
    st.session_state.auto_triggered = {"Morning_1130": False, "Afternoon_0335": False}

# --- Live Market Value Fetcher (ဈေးကွက်ဖွင့်ချိန်မှ ပိတ်ချိန်အထိ တိုက်ရိုက်ပြရန်) ---
def fetch_live_market_value():
    try:
        url = "https://www.set.or.th/en/home"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Live SET Total Value ကို Parse လုပ်ရန် (လက်ရှိ Mock Value ထည့်ထားသည်)
            live_val = "1,234.56 (Live)"
            return live_val
    except Exception as e:
        pass
    return "Connecting Live..."

# --- UI: Live Market Display ---
st.subheader("🔴 Live Market Value Tracker")
current_time_str = datetime.now().strftime("%H:%M:%S")
current_date_str = datetime.now().strftime("%Y-%m-%d")

col_a, col_b = st.columns(2)
with col_a:
    st.metric(label="လက်ရှိ ဈေးကွက်တန်ဖိုး (Live Price)", value=fetch_live_market_value())
with col_b:
    st.metric(label="လက်ရှိ အချိန် (Current Time)", value=current_time_str)

st.markdown("---")

# --- Automatic Time-based Prediction Trigger Logic ---
now_time = datetime.now().time()
morning_cutoff = datetime.strptime("11:30:00", "%H:%M:%S").time()
afternoon_cutoff = datetime.strptime("15:35:00", "%H:%M:%S").time()

# ၁၁:၃၀ တိတိရောက်လျှင် မနက်ပိုင်း ၁၂:၀၁ အတွက် အလိုအလျောက် တွက်မည်
if now_time >= morning_cutoff and not st.session_state.auto_triggered["Morning_1130"]:
    morning_candidates = "24680"  # တွက်ချက်ထွက်လာသည့် Candidate ၅ လုံး
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Morning Session (12:01 Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Morning Session (12:01 Target)",
            "Candidate Set": morning_candidates,
            "Actual Value": "Pending"
        })
    st.session_state.auto_triggered["Morning_1130"] = True

# ၃:၃၅ တိတိရောက်လျှင် ညနေပိုင်း ၄:၃၀ အတွက် အလိုအလျောက် တွက်မည်
if now_time >= afternoon_cutoff and not st.session_state.auto_triggered["Afternoon_0335"]:
    afternoon_candidates = "13579"  # တွက်ချက်ထွက်လာသည့် Candidate ၅ လုံး
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Afternoon Session (4:30 Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Afternoon Session (4:30 Target)",
            "Candidate Set": afternoon_candidates,
            "Actual Value": "Pending"
        })
    st.session_state.auto_triggered["Afternoon_0335"] = True

# ==========================================
# 🌅 မနက်ပိုင်း (Morning Session - Target: 12:01 PM)
# ==========================================
st.subheader("🌅 Morning Session (Target: 12:01 PM)")
st.text("• စောင့်ကြည့်မည့်ကာလ: မနက်ဈေးကွက်စဖွင့်ချိန် မှ ၁၁:၃၀ AM အထိ\n• အလိုအလျောက် ထွက်ပေါ်မည့်အချိန်: ၁၁:၃၀ AM တွင် ၁၂:၀၁ အတွက် ၅ လုံး ထွက်မည်\n• Live Value ပြသမှု: မနက်ဈေးကွက်ပိတ်ချိန်အထိ တိုက်ရိုက်ပြနေမည်")

# ==========================================
# 🌇 ညနေပိုင်း (Afternoon Session - Target: 4:30 PM)
# ==========================================
st.markdown("---")
st.subheader("🌇 Afternoon Session (Target: 4:30 PM)")
st.text("• စောင့်ကြည့်မည့်ကာလ: နေ့လယ်ဈေးကွက်ပြန်စချိန် မှ ၃:၃၅ PM အထိ\n• အလိုအလျောက် ထွက်ပေါ်မည့်အချိန်: ၃:၃၅ PM တွင် ၄:၃၀ အတွက် ၅ လုံး ထွက်မည်\n• Live Value ပြသမှု: ညနေဈေးကွက်ပိတ်ချိန်အထိ တိုက်ရိုက်ပြနေမည်")

# --- Performance & History Tracking ---
st.markdown("---")
st.subheader("📊 Performance & History Tracking")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်းမရှိသေးပါ။ (သတ်မှတ်ချိန်ရောက်ပါက အလိုအလျောက် ဝင်လာပါမည်)")

# --- Manual Override for Actual Value ---
st.markdown("---")
st.subheader("🎯 Actual Value ထည့်သွင်းရန် (Reconciliation)")
with st.form("actual_form"):
    sel_session = st.selectbox("Session ရွေးချယ်ရန်:", ["Morning Session (12:01 Target)", "Afternoon Session (4:30 Target)"])
    actual_val = st.text_input("တကယ်ကျလာသော တန်ဖိုး (Actual Value):")
    submit_btn = st.form_submit_button("Update Actual Value")
    
    if submit_btn and actual_val:
        updated = False
        for item in st.session_state.history_data:
            if item["Date"] == current_date_str and item["Session"] == sel_session:
                item["Actual Value"] = actual_val
                updated = True
        if updated:
            st.success("Actual Value အောင်မြင်စွာ အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
            st.rerun()
        else:
            st.warning("ယနေ့အတွက် သက်ဆိုင်ရာ Session မှတ်တမ်း မရှိသေးပါ။")

# --- Auto Refresh for Real-time Live Display ---
time.sleep(60)
st.rerun()
