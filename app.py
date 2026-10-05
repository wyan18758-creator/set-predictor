import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SET Total Value Prediction Dashboard",
    page_icon="📈",
    layout="centered",
)

st.title("📈 SET Total Value Prediction Dashboard")
st.markdown("API ဒေတာများကို အမှန်ကန်ဆုံး ဖမ်းယူပြသပေးမည့်စနစ်။")

# --- Timezone Setup (Myanmar Time = UTC +6:30) ---
mm_offset = timezone(timedelta(hours=6, minutes=30))
current_time_mm = datetime.now(mm_offset)
current_time_str = current_time_mm.strftime("%H:%M:%S")
current_date_str = current_time_mm.strftime("%Y-%m-%d")

# --- Initialize Session State ---
if "history_data" not in st.session_state:
    st.session_state.history_data = []

if "morning_collected_values" not in st.session_state:
    st.session_state.morning_collected_values = []

if "afternoon_collected_values" not in st.session_state:
    st.session_state.afternoon_collected_values = []

if "auto_triggered" not in st.session_state:
    st.session_state.auto_triggered = {"Morning_1130": False, "Afternoon_0335": False}

# --- Fetch from EODHD API with Safe Parsing for 'NA' ---
def fetch_live_total_value_from_eodhd():
    api_token = "6ac1dfd4509a07.37594523"
    # လိုအပ်ပါက Ticker ကို SET.INDX သို့မဟုတ် SET.SET ပြောင်းလဲစမ်းသပ်နိုင်သည်
    url = f"https://eodhd.com/api/real-time/SET.INDX?api_token={api_token}&fmt=json"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.write("🔍 API Raw Data အပြည့်အစုံ:", data)
            
            # 'NA' သို့မဟုတ် တန်ဖိုးမရှိသည်များကို စစ်ဆေးခြင်း
            close_val = data.get("close")
            if close_val and close_val != "NA":
                return float(close_val)
            
            # အကယ်၍ close မှာ NA ဖြစ်နေပါက previousClose ကို သုံးရန်
            prev_val = data.get("previousClose")
            if prev_val and prev_val != "NA":
                return float(prev_val)
                
    except Exception as e:
        st.error(f"API Error: {e}")
    
    return 0.0

# --- Helper Function: Generate 5 Candidates ---
def generate_candidates_from_average(value_list):
    try:
        if not value_list:
            return "1 3 5 7 9"
        avg_val = sum(value_list) / len(value_list)
        clean_val = f"{avg_val:.2f}"
        int_part = clean_val.split('.')[0]
        last_digit = int(int_part[-1])
        
        c1 = (last_digit + 1) % 10
        c2 = (last_digit + 3) % 10
        c3 = (last_digit + 5) % 10
        c4 = (last_digit + 7) % 10
        c5 = (last_digit + 9) % 10
        
        return f"{c1} {c2} {c3} {c4} {c5}"
    except:
        return "1 3 5 7 9"

# --- UI: Live Total Value Display ---
st.subheader("🔴 EODHD API Live Value Tracker")

current_live_val = fetch_live_total_value_from_eodhd()

col_a, col_b = st.columns(2)
with col_a:
    st.metric(label="API မှ ရလာသော Live Value", value=f"{current_live_val:,.2f}" if current_live_val > 0 else "N/A")
with col_b:
    st.metric(label="လက်ရှိ မြန်မာစံတော်ချိန်", value=current_time_str)

st.markdown("---")

# --- Time Range & Data Accumulation Logic ---
now_time = current_time_mm.time()
morning_start = datetime.strptime("09:30:00", "%H:%M:%S").time()
morning_cutoff = datetime.strptime("11:30:00", "%H:%M:%S").time()

afternoon_start = datetime.strptime("14:00:00", "%H:%M:%S").time()
afternoon_cutoff = datetime.strptime("15:35:00", "%H:%M:%S").time()

if morning_start <= now_time <= morning_cutoff:
    if current_live_val > 0 and current_live_val not in st.session_state.morning_collected_values:
        st.session_state.morning_collected_values.append(current_live_val)

if afternoon_start <= now_time <= afternoon_cutoff:
    if current_live_val > 0 and current_live_val not in st.session_state.afternoon_collected_values:
        st.session_state.afternoon_collected_values.append(current_live_val)

# --- Automatic Triggers at Target Times ---
if now_time >= morning_cutoff and not st.session_state.auto_triggered["Morning_1130"]:
    morning_candidates = generate_candidates_from_average(st.session_state.morning_collected_values)
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Morning Closing (12:01 PM Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Morning Closing (12:01 PM Target)",
            "Candidate Set": morning_candidates,
            "Actual Value": "Pending"
        })
    st.session_state.auto_triggered["Morning_1130"] = True

if now_time >= afternoon_cutoff and not st.session_state.auto_triggered["Afternoon_0335"]:
    afternoon_candidates = generate_candidates_from_average(st.session_state.afternoon_collected_values)
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Afternoon Closing (4:30 PM Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Afternoon Closing (4:30 PM Target)",
            "Candidate Set": afternoon_candidates,
            "Actual Value": "Pending"
        })
    st.session_state.auto_triggered["Afternoon_0335"] = True

# --- UI Sessions ---
st.subheader("🌅 Morning Session (12:01 PM Closing Target)")
st.text(f"• စုဆောင်းနေသည့်ဒေတာအရေအတွက်: {len(st.session_state.morning_collected_values)} ခု")
if now_time >= morning_cutoff:
    morning_res = next((item["Candidate Set"] for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Morning Closing (12:01 PM Target)"), "N/A")
    st.success(f"🎯 တွက်ချက်ပြီးသော Candidate များ: **{morning_res}**")
else:
    st.info("⏳ ၁၁:၃၀ AM တွင် Candidate များ အလိုအလျောက် ထွက်လာပါမည်။")

st.markdown("---")
st.subheader("🌇 Afternoon Session (4:30 PM Closing Target)")
st.text(f"• စုဆောင်းနေသည့်ဒေတာအရေအတွက်: {len(st.session_state.afternoon_collected_values)} ခု")
if now_time >= afternoon_cutoff:
    afternoon_res = next((item["Candidate Set"] for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Afternoon Closing (4:30 PM Target)"), "N/A")
    st.success(f"🎯 တွက်ချက်ပြီးသော Candidate များ: **{afternoon_res}**")
else:
    st.info("⏳ ၃:၃၅ PM တွင် Candidate များ အလိုအလျောက် ထွက်လာပါမည်။")

# --- History & Reconciliation ---
st.markdown("---")
st.subheader("📊 Performance & History Tracking")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်းမရှိသေးပါ။")

st.markdown("---")
st.subheader("🎯 Actual Value ထည့်သွင်းရန် (Reconciliation)")
with st.form("actual_form"):
    sel_session = st.selectbox("Session ရွေးချယ်ရန်:", ["Morning Closing (12:01 PM Target)", "Afternoon Closing (4:30 PM Target)"])
    actual_val = st.text_input("တကယ်ကျလာသော တန်ဖိုး (Actual Value):")
    submit_btn = st.form_submit_button("Update Actual Value")
    
    if submit_btn and actual_val:
        updated = False
        for item in st.session_state.history_data:
            if item["Date"] == current_date_str and item["Session"] == sel_session:
                item["Actual Value"] = actual_val
                updated = True
        if updated:
            st.success("အောင်မြင်စွာ အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
            st.rerun()
        else:
            st.warning("ယနေ့အတွက် သက်ဆိုင်ရာ Session မှတ်တမ်း မရှိသေးပါ။")

time.sleep(60)
st.rerun()
