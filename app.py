import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="SET Total Value Prediction Dashboard",
    page_icon="📈",
    layout="centered",
)

st.title("📈 SET Total Value Prediction Dashboard")
st.markdown(
    "စျေးကွက်ဖွင့်ချိန်မှစတင်ကာ Real-time ဒေတာများကို စောင့်ကြည့်ပြီး"
    " သတ်မှတ်ချိန်များတွင် Candidate Set ၅ လုံးကို ဇေတို ထုတ်ပေးမည့် စနစ်။"
)

# Session State ထဲမှာ History သိမ်းဆည်းရန် နေရာဖန်တီးခြင်း
if "history_data" not in st.session_state:
  st.session_state.history_data = []


# ခန့်မှန်းချက် ထွက်လာတဲ့အခါ History ထဲ ထည့်သွင်းသည့် ဖန်ရှင်
def log_prediction(session_name, candidate_set, actual_value=None):
  st.session_state.history_data.append({
      "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
      "Session": session_name,
      "Candidate Set": candidate_set,
      "Actual Value": actual_value,
  })


st.divider()

# Morning Session
st.subheader("🌅 Morning Session (12:01 PM Target)")
st.write("**Cutoff Time:** 11:30 AM")
if st.button("📊 Calculate 11:30 Prediction"):
  # ဥပမာ တွက်ချက်ထားသော Candidate Set (နောက်ပိုင်းတွင် လိုသလို တိကျသော logic ထည့်ရန်)
  sample_set = "12345"
  st.success(f"Morning Candidate Set: {sample_set}")
  log_prediction("Morning Session", sample_set)

st.divider()

# Afternoon Session
st.subheader("🌇 Afternoon Session (4:30 PM Target)")
st.write("**Cutoff Time:** 3:35 PM")
if st.button("📊 Calculate 3:35 Prediction"):
  # ဥပမာ တွက်ချက်ထားသော Candidate Set
  sample_set = "67890"
  st.success(f"Afternoon Candidate Set: {sample_set}")
  log_prediction("Afternoon Session", sample_set)

st.divider()
st.subheader("📊 Performance & History Tracking")

if st.session_state.history_data:
  df_history = pd.DataFrame(st.session_state.history_data)
  st.dataframe(df_history, use_container_width=True)

  # တကယ်ကျလာသော တန်ဖိုး (Actual Value) ထည့်ရန်
  with st.form("update_actual_form"):
    st.write("တကယ်ကျလာသော တန်ဖိုး (Actual Value) ထည့်သွင်းရန်")
    actual_input = st.text_input(
        "Actual Value (ဥပမာ - 5 digits သို့မဟုတ် တန်ဖိုး)"
    )
    submit_actual = st.form_submit_button("Update Actual Value")
    if submit_actual and actual_input:
      if st.session_state.history_data:
        st.session_state.history_data[-1]["Actual Value"] = actual_input
        st.success("မှတ်တမ်း အပ်ဒိတ်လုပ်ပြီးပါပြီ!")
        st.rerun()
else:
  st.info("ယနေ့အတွက် မှတ်တမ်းများ မရှိသေးပါ။")
