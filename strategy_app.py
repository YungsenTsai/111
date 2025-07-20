import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="centered", page_title="策略通", page_icon="🎯")
st.markdown("<h1 style='text-align:center; color:white;'>策略通：TQQQ＋TMF 輪動策略</h1>", unsafe_allow_html=True)
st.markdown("<style>body { background-color: #121212; color: white; }</style>", unsafe_allow_html=True)

def get_data(ticker, period="2y"):
    try:
        df = yf.download(ticker, period=period, interval="1mo", progress=False)
    except Exception as e:
        st.error(f"❌ 無法下載 {ticker}：{e}")
        return None

    if df.empty:
        st.error(f"❌ {ticker} 資料為空")
        return None

    # 嘗試轉換 index 為日期
    try:
        df.index = pd.to_datetime(df.index, errors="coerce")
    except Exception as e:
        st.error(f"❌ {ticker} index 轉換日期失敗：{e}")
        return None

    df = df.reset_index()

    # 檢查 Date 和 Close 是否存在
    if "Date" not in df.columns or "Close" not in df.columns:
        st.error(f"❌ {ticker} 缺少必要欄位：Date 或 Close，實際欄位：{df.columns.tolist()}")
        return None

    # 清除 Date 為 NaT 的資料
    df = df.dropna(subset=["Date"])

    # 避免 Month 重複
    if "Month" in df.columns:
        df = df.drop(columns=["Month"])

    try:
        df["Month"] = df["Date"].dt.to_period("M")
        df = df.drop_duplicates(subset="Month", keep="last")
        df.set_index("Date", inplace=True)
    except Exception as e:
        st.error(f"❌ {ticker} 建立 Month 錯誤：{e}")
        return None

    return df

# 讀資料
tqqq = get_data("TQQQ")
tmf = get_data("TMF")
qqq = get_data("QQQ")

if any(x is None or x.empty for x in [tqqq, tmf, qqq]):
    st.stop()

# 整合與計算
df = pd.DataFrame({
    'TQQQ_close': tqqq['Close'],
    'TMF_close': tmf['Close'],
    'QQQ_close': qqq['Close']
})

df['TQQQ_ret'] = df['TQQQ_close'].pct_change()
df['TMF_ret'] = df['TMF_close'].pct_change()
df['TQQQ_3mo'] = df['TQQQ_ret'].rolling(3).mean()
df['TMF_3mo'] = df['TMF_ret'].rolling(3).mean()
df['QQQ_MA200'] = df['QQQ_close'].rolling(200).mean()
df['QQQ_above_MA'] = df['QQQ_close'] > df['QQQ_MA200']

def decide(row):
    if not row['QQQ_above_MA']:
        return '暫時空手'
    return '持有 TQQQ' if row['TQQQ_3mo'] > row['TMF_3mo'] else '持有 TMF'

df['建議'] = df.apply(decide, axis=1)
df = df.tail(12)

# 顯示結果
st.table(df[['TQQQ_ret','TMF_ret','TQQQ_3mo','TMF_3mo','QQQ_above_MA','建議']].round(3))
st.markdown("**📌 本月建議：**  " + df['建議'].iloc[-1])
