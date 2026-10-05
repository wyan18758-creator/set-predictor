import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="SET Realtime Momentum Predictor",
    page_icon="📈",
    layout="centered",
)

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
    st.session_state.auto_triggered = {"Morning_1130": False, "Afternoon_0330": False}

# --- Fetch from EODHD API Safely ---
def fetch_live_set_value():
    api_token = "6ac1dfd4509a07.37594523"
    url = f"https://eodhd.com/api/real-time/SET.INDX?api_token={api_token}&fmt=json"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            val_str = data.get("previousClose")
            if not val_str or val_str == "NA":
                val_str = data.get("close")
                
            if val_str and val_str != "NA":
                return float(val_str)
    except Exception as e:
        st.error(f"API Error: {e}")
    
    return 1563.91  # Default fallback

# --- Advanced Helper Function: Momentum & Decimal Last Digit ---
def generate_momentum_candidates(value_list):
    try:
        if not value_list or len(value_list) < 2:
            return "1 5 9", "Neutral (Normal)"
        
        avg_val = sum(value_list) / len(value_list)
        clean_val = f"{avg_val:.2f}"
        decimal_part = clean_val.split('.')[1]
        last_digit_dec = int(decimal_part[-1])
        
        start_val = value_list[0]
        latest_val = value_list[-1]
        momentum_diff = latest_val - start_val
        
        if momentum_diff > 0.5:
            momentum_status = "🚀 Bullish Momentum (အားကောင်းသော အတက်)"
            offset = 1
        elif momentum_diff < -0.5:
            momentum_status = "🔻 Bearish Momentum (အားပျော့သော အကျ)"
            offset = -1
        else:
            momentum_status = "⚖️ Neutral Momentum (ရိုးရိုးအသွားအလာ)"
            offset = 0
            
        adjusted_digit = (last_digit_dec + offset) % 10
        
        c1 = (adjusted_digit + 2) % 10
        c2 = (adjusted_digit + 5) % 10
        c3 = (adjusted_digit + 8) % 10
        
        return f"{c1} {c2} {c3}", momentum_status
    except:
        return "1 5 9", "Neutral"

# ==========================================
# 🔴 1. TOP SECTION: REALTIME LIVE SET DISPLAY
# ==========================================
st.title("📈 SET Realtime Momentum Predictor")
st.markdown("ဈေးကွက်ဖွင့်ချိန်အတွင်း Realtime Live SET တန်ဖိုးများကို ထိပ်ဆုံးတွင် အမြဲပြသနေပါသည်။")

current_live_val = fetch_live_set_value()

st.markdown("---")
top_col1, top_col2 = st.columns(2)
with top_col1:
    st.metric(label="🔴 REALTIME LIVE SET VALUE", value=f"{current_live_val:,.2f}" if current_live_val > 0 else "N/A")
with top_col2:
    st.metric(label="⏱️ လက်ရှိ မြန်မာစံတော်ချိန်", value=current_time_str)
st.markdown("---")

# --- Time Range & Data Accumulation Logic ---
now_time = current_time_mm.time()

morning_market_open = datetime.strptime("09:30:00", "%H:%M:%S").time()
morning_trigger_time = datetime.strptime("11:30:00", "%H:%M:%S").time()
morning_market_close = datetime.strptime("12:01:00", "%H:%M:%S").time()

afternoon_market_open = datetime.strptime("14:00:00", "%H:%M:%S").time()
afternoon_trigger_time = datetime.strptime("15:30:00", "%H:%M:%S").time()
afternoon_market_close = datetime.strptime("16:10:00", "%H:%M:%S").time()

if morning_market_open <= now_time <= morning_market_close:
    if current_live_val > 0:
        if not st.session_state.morning_collected_values or st.session_state.morning_collected_values[-1] != current_live_val:
            st.session_state.morning_collected_values.append(current_live_val)

if afternoon_market_open <= now_time <= afternoon_market_close:
    if current_live_val > 0:
        if not st.session_state.afternoon_collected_values or st.session_state.afternoon_collected_values[-1] != current_live_val:
            st.session_state.afternoon_collected_values.append(current_live_val)

# --- Automatic Triggers at 11:30 AM & 3:30 PM ---
if now_time >= morning_trigger_time and not st.session_state.auto_triggered["Morning_1130"]:
    morning_candidates, morning_mom = generate_momentum_candidates(st.session_state.morning_collected_values)
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Morning (12:01 Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Morning (12:01 Target)",
            "Candidates": morning_candidates,
            "Momentum Status": morning_mom,
            "Actual": "Pending"
        })
    st.session_state.auto_triggered["Morning_1130"] = True

if now_time >= afternoon_trigger_time and not st.session_state.auto_triggered["Afternoon_0330"]:
    afternoon_candidates, afternoon_mom = generate_momentum_candidates(st.session_state.afternoon_collected_values)
    existing = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Afternoon (4:10 Target)"), None)
    if not existing:
        st.session_state.history_data.append({
            "Date": current_date_str,
            "Session": "Afternoon (4:10 Target)",
            "Candidates": afternoon_candidates,
            "Momentum Status": afternoon_mom,
            "Actual": "Pending"
        })
    st.session_state.auto_triggered["Afternoon_0330"] = True

# ==========================================
# 🌅 2. MORNING SESSION PANEL
# ==========================================
st.subheader("🌅 Morning Session (Target: 12:01 PM)")
st.text(f"• မနက်ပိုင်း စုဆောင်းထားသော ဒေတာအရေအတွက်: {len(st.session_state.morning_collected_values)} ခု")

if morning_market_open <= now_time <= morning_market_close:
    st.info("🟢 မနက်ပိုင်း ဈေးကွက်ဖွင့်ချိန်မှ ၁၂:၀၁ ပိတ်ချိန်အထိ Live တန်ဖိုးများကို ဆက်လက်ပြသနေပါသည်။")

if st.session_state.morning_collected_values:
    with st.expander("📥 မနက်ပိုင်း စုဆောင်းရရှိထားသော SET တန်ဖိုးများကို ကြည့်ရန်"):
        st.write(st.session_state.morning_collected_values)

if now_time >= morning_trigger_time:
    m_item = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Morning (12:01 Target)"), None)
    if m_item:
        cand_val = m_item['Candidates']
        mom_val = m_item['Momentum Status']
        st.success(f"🎯 ၁၁:၃၀ တွင် ထွက်လာသော Candidate ၃ လုံး: **{cand_val}**")
        st.info(f"📊 ဈေးကွက်အရှိန်အဟုန်: **{mom_val}**")
else:
    st.info("⏳ မနက် ၁၁:၃၀ တွင် Candidate များ ထွက်လာပါမည်။")

st.markdown("---")

# ==========================================
# 🌇 3. AFTERNOON SESSION PANEL
# ==========================================
st.subheader("🌇 Afternoon Session (Target: 4:10 PM)")
st.text(f"• နေ့လယ်ပိုင်း စုဆောင်းထားသော ဒေတာအရေအတွက်: {len(st.session_state.afternoon_collected_values)} ခု")

if afternoon_market_open <= now_time <= afternoon_market_close:
    st.info("🟢 နေ့လယ်ပိုင်း ဈေးကွက်ဖွင့်ချိန်မှ ၄:၁၀ ပိတ်ချိန်အထိ Live တန်ဖိုးများကို ဆက်လက်ပြသနေပါသည်။")

if st.session_state.afternoon_collected_values:
    with st.expander("📥 နေ့လယ်ပိုင်း စုဆောင်းရရှိထားသော SET တန်ဖိုးများကို ကြည့်ရန်"):
        st.write(st.session_state.afternoon_collected_values)

if now_time >= afternoon_trigger_time:
    a_item = next((item for item in st.session_state.history_data if item["Date"] == current_date_str and item["Session"] == "Afternoon (4:10 Target)"), None)
    if a_item:
        cand_val_a = a_item['Candidates']
        mom_val_a = a_item['Momentum Status']
        st.success(f"🎯 ၃:၃၀ တွင် ထွက်လာသော Candidate ၃ လုံး: **{cand_val_a}**")
        st.info(f"📊 ဈေးကွက်အရှိန်အဟုန်: **{mom_val_a}**")
else:
    st.info("⏳ နေ့လယ် ၃:၃၀ တွင် Candidate များ ထွက်လာပါမည်။")

# ==========================================
# 📊 4. HISTORY & TRACKING
# ==========================================
st.markdown("---")
st.subheader("📊 History & Tracking")
if len(st.session_state.history_data) > 0:
    st.dataframe(pd.DataFrame(st.session_state.history_data), use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်း မရှိသေးပါ။")

time.sleep(60)
st.rerun()
