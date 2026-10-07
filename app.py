import json
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="SET Index Pattern Dashboard", page_icon="ðŸ“Š", layout="wide")

SYMBOL = "^SET.BK"
TZ = ZoneInfo("Asia/Yangon")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PATTERN_FILE = DATA_DIR / "patterns.csv"
RAW_FILE = DATA_DIR / "raw_prices.csv"

MORNING_START = time(9, 0)
MORNING_DATA_END = time(11, 30)
MORNING_OUTPUT = time(11, 35)
MORNING_TARGET = time(12, 1)

EVENING_START = time(13, 0)
EVENING_DATA_END = time(15, 30)
EVENING_OUTPUT = time(15, 35)
EVENING_TARGET = time(16, 10)

PATTERN_COLUMNS = [
    "date", "session", "target_time", "window_start", "window_end",
    "start_index", "end_index", "high", "low", "net_change", "range",
    "up_moves", "down_moves", "direction_changes", "pattern", "target_digit"
]


def empty_patterns():
    return pd.DataFrame(columns=PATTERN_COLUMNS)


def load_patterns():
    if not PATTERN_FILE.exists():
        return empty_patterns()
    try:
        df = pd.read_csv(PATTERN_FILE)
        for col in PATTERN_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        return df[PATTERN_COLUMNS]
    except Exception:
        return empty_patterns()


def save_patterns(df):
    df.drop_duplicates(
        subset=["date", "session", "target_time"], keep="last"
    ).to_csv(PATTERN_FILE, index=False)


def load_raw():
    if not RAW_FILE.exists():
        return pd.DataFrame(columns=["timestamp", "price"])
    try:
        df = pd.read_csv(RAW_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        return df.dropna(subset=["timestamp", "price"])
    except Exception:
        return pd.DataFrame(columns=["timestamp", "price"])


def append_raw(data):
    if data.empty:
        return
    old = load_raw()
    new = data[["Dt", "Close"]].rename(
        columns={"Dt": "timestamp", "Close": "price"}
    )
    new["timestamp"] = pd.to_datetime(new["timestamp"], utc=True)
    out = pd.concat([old, new], ignore_index=True)
    out = out.drop_duplicates(subset=["timestamp"], keep="last")
    out.sort_values("timestamp").tail(50000).to_csv(RAW_FILE, index=False)


@st.cache_data(ttl=30, show_spinner=False)
def load_live_data():
    try:
        df = yf.download(
            SYMBOL, period="7d", interval="1m", auto_adjust=False,
            progress=False, prepost=False, threads=False
        )
        if df is None or df.empty:
            return pd.DataFrame(), "Yahoo Finance data á€™á€›á€•á€«"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        dt_col = "Datetime" if "Datetime" in df.columns else "Date"
        df["Dt"] = pd.to_datetime(df[dt_col], utc=True).dt.tz_convert(TZ)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                df[col] = np.nan
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["Dt", "Close"]).copy()
        df["Date"] = df["Dt"].dt.date.astype(str)
        df["Time"] = df["Dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df["time_val"] = (
            df["Dt"].dt.hour * 60
            + df["Dt"].dt.minute
            + df["Dt"].dt.second / 60
        )
        return df.sort_values("Dt").reset_index(drop=True), ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def last_digit(price):
    return int(f"{float(price):.2f}"[-1])


def session_bounds(session):
    if session == "morning":
        return MORNING_START, MORNING_DATA_END, MORNING_OUTPUT, MORNING_TARGET
    return EVENING_START, EVENING_DATA_END, EVENING_OUTPUT, EVENING_TARGET


def current_session_data(df, session):
    if df.empty:
        return df
    start, data_end, _, _ = session_bounds(session)
    date_value = df["Date"].max()
    start_val = start.hour * 60 + start.minute
    end_val = data_end.hour * 60 + data_end.minute
    return df[
        (df["Date"] == date_value)
        & (df["time_val"] >= start_val)
        & (df["time_val"] <= end_val)
    ].copy()


def calculate_features(rows):
    if rows is None or len(rows) < 2:
        return None
    rows = rows.sort_values("Dt")
    prices = rows["Close"].astype(float).to_numpy()
    diffs = np.diff(prices)
    signs = np.sign(diffs)
    signs = signs[signs != 0]
    changes = int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0
    first, last = float(prices[0]), float(prices[-1])
    high, low = float(prices.max()), float(prices.min())
    return {
        "window_start": rows["Dt"].iloc[0].strftime("%H:%M:%S"),
        "window_end": rows["Dt"].iloc[-1].strftime("%H:%M:%S"),
        "start_index": first, "end_index": last, "high": high, "low": low,
        "net_change": last - first, "range": high - low,
        "up_moves": int((diffs > 0).sum()),
        "down_moves": int((diffs < 0).sum()),
        "direction_changes": changes,
    }


def label_pattern(f):
    if f is None:
        return "UNKNOWN"
    net, rng = f["net_change"], f["range"]
    if net > 0.5 and f["down_moves"] > 0:
        direction = "UP_REVERSAL"
    elif net < -0.5 and f["up_moves"] > 0:
        direction = "DOWN_REVERSAL"
    elif net > 0.1:
        direction = "UP"
    elif net < -0.1:
        direction = "DOWN"
    else:
        direction = "FLAT"
    volatility = "HIGH" if rng >= 2 else "MEDIUM" if rng >= 0.8 else "LOW"
    return f"{direction}_{volatility}"


def predict_top3(patterns, session, prediction_data):
    features = calculate_features(prediction_data)
    if features is None:
        return None, "11:30/15:30 cutoff data á€™á€œá€¯á€¶á€œá€±á€¬á€€á€ºá€•á€«"
    pattern = label_pattern(features)
    selected = patterns[
        (patterns["session"] == session)
        & (patterns["pattern"] == pattern)
    ].copy()
    if len(selected) < 3:
        selected = patterns[patterns["session"] == session].copy()
    if selected.empty:
        return {"features": features, "pattern": pattern, "top3": []}, "Historical data á€™á€›á€¾á€­á€žá€±á€¸á€•á€«"
    digits = pd.to_numeric(selected["target_digit"], errors="coerce").dropna().astype(int)
    counts = digits.value_counts().reindex(range(10), fill_value=0)
    total = int(counts.sum())
    ranked = counts.sort_values(ascending=False).head(3)
    top3 = [(int(d), round(float(n / total * 100), 1)) for d, n in ranked.items()]
    return {"features": features, "pattern": pattern, "top3": top3}, None


def send_telegram(token, chat_id, text):
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}, timeout=10
    )
    response.raise_for_status()


st.title("ðŸ“Š SET Index Live & Session Pattern Dashboard")
st.markdown("SET Index data á€€á€­á€¯ cutoff á€¡á€á€»á€­á€”á€ºá€¡á€‘á€­ á€…á€¯á€…á€Šá€ºá€¸á€•á€¼á€®á€¸ á€á€…á€ºá€€á€¼á€­á€™á€ºá€á€Šá€ºá€¸ Top 3 á€‘á€¯á€á€ºá€•á€±á€¸á€žá€±á€¬ dashboard")

with st.sidebar:
    session = st.radio(
        "Session á€›á€½á€±á€¸á€•á€«", ["morning", "evening"],
        format_func=lambda x: "ðŸŒ… á€™á€”á€€á€ºá€•á€­á€¯á€„á€ºá€¸" if x == "morning" else "ðŸŒ‡ á€Šá€”á€±á€•á€­á€¯á€„á€ºá€¸"
    )
    st.info(
        "á€™á€”á€€á€º: 11:30 cutoff â†’ 11:35 output â†’ 12:01 target\n\n"
        "á€Šá€”á€±: 15:30 cutoff â†’ 15:35 output â†’ 16:10 target"
    )

patterns = load_patterns()
data, error = load_live_data()

if error:
    st.warning(f"Live data error: {error}")
if data.empty:
    st.error("SET data á€™á€›á€•á€«á‹ Internet/yfinance symbol á€€á€­á€¯á€…á€…á€ºá€•á€«á‹")
    st.stop()

append_raw(data)
latest = data.iloc[-1]
st.metric("Latest SET Index", f"{float(latest['Close']):.2f}")
st.caption(f"Last update: {latest['Dt'].strftime('%Y-%m-%d %H:%M:%S %Z')}")

start_at, cutoff_at, output_at, target_at = session_bounds(session)
session_data = current_session_data(data, session)

if session_data.empty:
    st.warning("á€›á€½á€±á€¸á€‘á€¬á€¸á€á€²á€· session á€¡á€á€½á€€á€º data á€™á€›á€žá€±á€¸á€•á€«á‹")
else:
    st.dataframe(
        session_data[["Time", "Open", "High", "Low", "Close", "Volume"]].tail(20),
        use_container_width=True, hide_index=True
    )
    st.plotly_chart(
        px.line(session_data, x="Dt", y="Close", title=f"{session.title()} Session"),
        use_container_width=True
    )

now = datetime.now(TZ).time()
st.info(
    f"Data á€…á€¯á€™á€Šá€·á€ºá€¡á€á€»á€­á€”á€º: {start_at.strftime('%H:%M')}â€“{cutoff_at.strftime('%H:%M')} | "
    f"á€‚á€á€”á€ºá€¸á€‘á€¯á€á€ºá€™á€Šá€·á€ºá€¡á€á€»á€­á€”á€º: {output_at.strftime('%H:%M')} | "
    f"Target: {target_at.strftime('%H:%M')}"
)

if st.button(
    f"ðŸ”® {output_at.strftime('%H:%M')} á€™á€¾á€¬ á€‚á€á€”á€ºá€¸ áƒ á€œá€¯á€¶á€¸ á€á€…á€ºá€€á€¼á€­á€™á€ºá€á€Šá€ºá€¸á€‘á€¯á€á€ºá€™á€Šá€º",
    type="primary", key=f"predict_{session}"
):
    if now < output_at:
        st.warning(f"{output_at.strftime('%H:%M')} á€™á€›á€±á€¬á€€á€ºá€žá€±á€¸á€•á€«á‹")
    elif now >= target_at:
        st.warning(f"Target time {target_at.strftime('%H:%M')} á€€á€»á€±á€¬á€ºá€žá€½á€¬á€¸á€•á€«á€•á€¼á€®á‹")
    elif session_data.empty:
        st.warning("Cutoff data á€™á€›á€¾á€­á€žá€±á€¸á€•á€«á‹")
    elif st.session_state.get(f"done_{session}"):
        st.info("á€’á€® session á€¡á€á€½á€€á€º prediction á€€á€­á€¯ á€á€…á€ºá€€á€¼á€­á€™á€ºá€‘á€¯á€á€ºá€•á€¼á€®á€¸á€žá€¬á€¸á€•á€«á‹")
    else:
        result, message = predict_top3(patterns, session, session_data)
        st.session_state[f"done_{session}"] = True
        if result["top3"]:
            st.success(
                f"Pattern: {result['pattern']} | "
                f"Output: {output_at.strftime('%H:%M')} | "
                f"Target: {target_at.strftime('%H:%M')}"
            )
            st.markdown(
                "### ðŸ”® " + " áŠ ".join(
                    f"{digit} ({prob}%)" for digit, prob in result["top3"]
                )
            )
        else:
            st.info(message)
        st.json(result["features"])

st.divider()
st.subheader("ðŸ“š Historical Pattern Records")
if patterns.empty:
    st.info("Pattern record á€™á€›á€¾á€­á€žá€±á€¸á€•á€«á‹ á€¡á€±á€¬á€€á€ºá€€ form á€™á€¾á€¬ á€‘á€Šá€·á€ºá€•á€«á‹")
else:
    st.dataframe(patterns.tail(100), use_container_width=True, hide_index=True)

with st.expander("âž• Completed 5-minute pattern á€‘á€Šá€·á€ºá€›á€”á€º"):
    with st.form("pattern_form"):
        c1, c2, c3 = st.columns(3)
        record_date = c1.date_input("Date")
        record_session = c2.selectbox("Session", ["morning", "evening"])
        default_target = MORNING_TARGET if record_session == "morning" else EVENING_TARGET
        record_target = c3.time_input("Target time", default_target)
        rows_text = st.text_area(
            "TIME,INDEX rows",
            placeholder="11:55:21,1591.01\n11:56:18,1591.69\n12:00:24,1588.82"
        )
        actual_digit = st.number_input("Actual target last digit", 0, 9, 0)
        save_button = st.form_submit_button("Save record")

    if save_button:
        try:
            parsed = []
            for line in rows_text.strip().splitlines():
                t, price = [x.strip() for x in line.split(",")]
                parsed.append({
                    "Dt": pd.Timestamp(f"{record_date} {t}").tz_localize(TZ),
                    "Close": float(price),
                })
            record_df = pd.DataFrame(parsed).sort_values("Dt")
            features = calculate_features(record_df)
            if features is None:
                raise ValueError("á€¡á€”á€Šá€ºá€¸á€†á€¯á€¶á€¸ rows á‚ á€á€¯á€œá€­á€¯á€•á€«á€á€šá€º")
            features.update({
                "date": str(record_date),
                "session": record_session,
                "target_time": record_target.strftime("%H:%M"),
                "pattern": label_pattern(features),
                "target_digit": int(actual_digit),
            })
            save_patterns(pd.concat([patterns, pd.DataFrame([features])], ignore_index=True))
            st.success("Pattern record á€žá€­á€™á€ºá€¸á€•á€¼á€®á€¸á€•á€«á€•á€¼á€®á‹")
            st.rerun()
        except Exception as exc:
            st.error(f"Format error: {exc}")

with st.expander("ðŸ“± Telegram Alert"):
    token = st.text_input("Bot Token", type="password")
    chat_id = st.text_input("Chat ID")
    alert_text = st.text_area("Message", "SET pattern update")
    if st.button("Send test alert"):
        if not token or not chat_id:
            st.error("Bot Token á€”á€²á€· Chat ID á€–á€¼á€Šá€·á€ºá€•á€«á‹")
        else:
            try:
                send_telegram(token, chat_id, alert_text)
                st.success("Telegram alert á€•á€­á€¯á€·á€•á€¼á€®á€¸á€•á€«á€•á€¼á€®á‹")
            except Exception as exc:
                st.error(f"Telegram error: {exc}")
