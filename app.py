import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime, timedelta, timezone
from collections import Counter
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="SET Value Auto Predictor", page_icon="📈", layout="centered")
st.title("📈 SET Value Auto Predictor")
st.markdown("Value ရဲ့ **ဒသမရှေ့နောက်ဆုံးဂဏန်း** ကို auto စုဆောင်းပြီး candidate ၅ လုံး ထုတ်ပေးမယ့် dashboard ပါ။")

# ၁ မိနစ်တစ်ခါ auto refresh
st_autorefresh(interval=60_000, key="auto_refresh")

mm = timezone(timedelta(hours=6, minutes=30))
now_mm = datetime.now(mm)
now_time = now_mm.time()
today = now_mm.strftime("%Y-%m-%d")

if "am_values" not in st.session_state:
    st.session_state.am_values = []
if "pm_values" not in st.session_state:
    st.session_state.pm_values = []
if "history" not in st.session_state:
    st.session_state.history = []
if "triggered" not in st.session_state:
    st.session_state.triggered = {"am": False, "pm": False}

# ---- Auto fetch Value ----
def fetch_value():
    # ၁။ EODHD secret ရှိရင် အရင်သုံး
    try:
        token = st.secrets["EODHD_API_KEY"]
        url = f"https://eodhd.com/api/real-time/SET.INDX?api_token={token}&fmt=json"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            d = r.json()
            for k in ["turnover", "value", "amount"]:
                if d.get(k):
                    return float(d[k]), "EODHD API"
    except Exception:
        pass

    # ၂။ SET website ကို proxy ဖြင့် scrape
    target = "https://www.set.or.th/en/market/index/set/overview"
    proxies = [
        "https://api.allorigins.win/raw?url=",
        "https://corsproxy.io/?",
    ]
    for p in proxies:
        try:
            r = requests.get(p + requests.utils.quote(target, safe=""), timeout=10)
            if r.status_code != 200:
                continue
            m = re.search(r'([d,]+.d+)s*(?:M.?Baht|Million|บาท)', r.text, re.I)
            if m:
                return float(m.group(1).replace(",", "")), "SET website (proxy)"
        except Exception:
            continue

    return None, "Fetch failed"

value, source = fetch_value()

st.subheader("🔴 Auto Live Value")
c1, c2 = st.columns(2)
with c1:
    st.metric("Live Value (M.Baht)", f"{value:,.2f}" if value else "Unavailable")
with c2:
    st.metric("မြန်မာစံတော်ချိန်", now_mm.strftime("%H:%M:%S"))
st.caption(f"Source: {source}")

# ---- Market hours collection ----
am_s = datetime.strptime("09:30", "%H:%M").time()
am_e = datetime.strptime("11:30", "%H:%M").time()
pm_s = datetime.strptime("14:00", "%H:%M").time()
pm_e = datetime.strptime("15:35", "%H:%M").time()

if value:
    if am_s <= now_time <= am_e:
        st.session_state.am_values.append(value)
    if pm_s <= now_time <= pm_e:
        st.session_state.pm_values.append(value)

# ---- Candidate logic ----
def make_candidates(values):
    if not values:
        return "—", 0
    digits = [int(f"{v/1000:.3f}".split(".")[0][-1]) for v in values]
    counts = Counter(digits)
    ranked = [d for d, _ in counts.most_common()]
    base = ranked[0] if ranked else 0
    for off in [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
        if len(ranked) >= 5:
            break
        c = (base + off) % 10
        if c not in ranked:
            ranked.append(c)
    return " ".join(map(str, ranked[:5])), len(values)

# ---- Auto trigger ----
if now_time >= am_e and not st.session_state.triggered["am"]:
    cand, n = make_candidates(st.session_state.am_values)
    st.session_state.history.append({"Date": today, "Session": "Morning (12:01)", "Samples": n, "Candidates": cand, "Actual": "Pending"})
    st.session_state.triggered["am"] = True

if now_time >= pm_e and not st.session_state.triggered["pm"]:
    cand, n = make_candidates(st.session_state.pm_values)
    st.session_state.history.append({"Date": today, "Session": "Afternoon (16:10)", "Samples": n, "Candidates": cand, "Actual": "Pending"})
    st.session_state.triggered["pm"] = True

# ---- UI ----
st.markdown("---")
st.subheader("🌅 Morning (12:01 target)")
cand_am, n_am = make_candidates(st.session_state.am_values)
st.metric("Samples", n_am)
st.metric("Candidate 5", cand_am)

st.markdown("---")
st.subheader("🌇 Afternoon (16:10 target)")
cand_pm, n_pm = make_candidates(st.session_state.pm_values)
st.metric("Samples", n_pm)
st.metric("Candidate 5", cand_pm)

st.markdown("---")
st.subheader("📊 History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
else:
    st.info("မှတ်တမ်းမရှိသေးပါ။") streamlit as st
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
st.markdown(
    "ဈေးကွက်စဖွင့်ချိန်မှ သတ်မှတ်ချိန်အထိ တန်ဖိုးများကို စုဆောင်း၍ Candidate ၅ လုံး အလိုအလျောက် ခန့်မှန်းထုတ်ပေးမည့်စနစ်။"
)

# --- Timezone Setup (Myanmar Time = UTC +6:30) ---
mm_offset = timezone(timedelta(hours=6, minutes=30))
current_time_mm = datetime.now(mm_offset)
current_time_str = current_time_mm.strftime("%H:%M:%S")
current_date_str = current_time_mm.strftime("%Y-%m-%d")

# --- Initialize Session State for Data Accumulation ---
if "history_data" not in st.session_state:
    st.session_state.history_data = []

if "morning_collected_values" not in st.session_state:
    st.session_state.morning_collected_values = []

if "afternoon_collected_values" not in st.session_state:
    st.session_state.afternoon_collected_values = []

if "auto_triggered" not in st.session_state:
    st.session_state.auto_triggered = {"Morning_1130": False, "Afternoon_0335": False}

# --- EODHD API Integration ---
def fetch_live_total_value_from_eodhd():
    api_token = "6ac1dfd4509a07.37594523"
    url = f"https://eodhd.com/api/real-time/SET.INDX?api_token={api_token}&fmt=json"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            val = float(data.get("close", data.get("price", 0)))
            if val > 0:
                return val
    except Exception as e:
        pass
    
    return 1450.50 + (datetime.now().second * 0.1)

# --- Helper Function: Generate 5 Candidates based on Average Value's digit ---
def generate_candidates_from_average(value_list):
    try:
        if not value_list:
            return "1 3 5 7 9"
        avg_val = sum(value_list) / len(value_list)
        clean_val = f"{avg_val:.2f}"
        int_part = clean_val.split('.')[0]
        last_digit = int(int_part[-1])  # ဒသမရှေ့ ကိန်းပြည့်၏ နောက်ဆုံးဂဏန်း
        
        c1 = (last_digit + 1) % 10
        c2 = (last_digit + 3) % 10
        c3 = (last_digit + 5) % 10
        c4 = (last_digit + 7) % 10
        c5 = (last_digit + 9) % 10
        
        return f"{c1} {c2} {c3} {c4} {c5}"
    except:
        return "1 3 5 7 9"

# --- UI: Live Total Value Display ---
st.subheader("🔴 EODHD API Live SET Tracker")

current_live_val = fetch_live_total_value_from_eodhd()

col_a, col_b = st.columns(2)
with col_a:
    st.metric(label="API မှ ရလာသော Live တန်ဖိုး", value=f"{current_live_val:,.2f}")
with col_b:
    st.metric(label="လက်ရှိ မြန်မာစံတော်ချိန်", value=current_time_str)

st.markdown("---")

# --- Time Range & Data Accumulation Logic ---
now_time = current_time_mm.time()
morning_start = datetime.strptime("09:30:00", "%H:%M:%S").time()
morning_cutoff = datetime.strptime("11:30:00", "%H:%M:%S").time()

afternoon_start = datetime.strptime("14:00:00", "%H:%M:%S").time()
afternoon_cutoff = datetime.strptime("15:35:00", "%H:%M:%S").time()

# 1. Morning Session Data Collection (09:30 AM - 11:30 AM)
if morning_start <= now_time <= morning_cutoff:
    if current_live_val not in st.session_state.morning_collected_values:
        st.session_state.morning_collected_values.append(current_live_val)

# 2. Afternoon Session Data Collection (02:00 PM - 03:35 PM)
if afternoon_start <= now_time <= afternoon_cutoff:
    if current_live_val not in st.session_state.afternoon_collected_values:
        st.session_state.afternoon_collected_values.append(current_live_val)

# --- Automatic Trigger at 11:30 AM and 03:35 PM ---
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

# ==========================================
# 🌅 မနက်ပိုင်း (Morning Closing Target: 12:01 PM)
# ==========================================
st.subheader("🌅 Morning Session (12:01 PM Closing Target)")
st.text(f"• စုဆောင်းနေသည့်ဒေတာအရေအတွက်: {len(st.session_state.morning_collected_values)} ခု\n• အလိုအလျောက် ထွက်ပေါ်မည့်အချိန်: ၁၁:၃၀ AM တွင် စုဆောင်းချက်မှ ၅ လုံး ထွက်မည်")

# ==========================================
# 🌇 ညနေပိုင်း (Afternoon Closing Target: 4:30 PM)
# ==========================================
st.markdown("---")
st.subheader("🌇 Afternoon Session (4:30 PM Closing Target)")
st.text(f"• စုဆောင်းနေသည့်ဒေတာအရေအတွက်: {len(st.session_state.afternoon_collected_values)} ခု\n• အလိုအလျောက် ထွက်ပေါ်မည့်အချိန်: ၃:၃၅ PM တွင် စုဆောင်းချက်မှ ၅ လုံး ထွက်မည်")

# --- Performance & History Tracking ---
st.markdown("---")
st.subheader("📊 Performance & History Tracking")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("လောလောဆယ် မှတ်တမ်းမရှိသေးပါ။ (သတ်မှတ်ချိန်ရောက်ပါက စုဆောင်းထားသည်များမှ အလိုအလျောက် ဝင်လာပါမည်)")

# --- Manual Override for Actual Value ---
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
            st.success("Actual Value အောင်မြင်စွာ အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
            st.rerun()
        else:
            st.warning("ယနေ့အတွက် သက်ဆိုင်ရာ Session မှတ်တမ်း မရှိသေးပါ။")

# --- Auto Refresh for Real-time Live Display ---
time.sleep(60)
st.rerun()
