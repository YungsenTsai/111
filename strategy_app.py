# 111
import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="centered", page_title="策略通", page_icon="🎯")

st.markdown("<h1 style='text-align:center; color:white;'>策略通：TQQQ＋TMF 輪動策略</h1>", unsafe_allow_html=True)
st.markdown("<style>body { background-color: #121212; color: white; }</style>", unsafe_allow_html=True)

# ✅ 完整 get_data 函數（強化防錯＋月資料處理）
def get_data(ticker, period="2y"):
    df = yf.download(ticker, period=period, interval="1mo", progress=False)

    if df.empty:
        st.error(f"❌ 無法抓取 {ticker} 的資料，請稍後再試")
        return pd.DataFrame()

    # 若 index 沒有欄名，強制設為 'Date'
    if df.index.name is None:
        df.index.name = 'Date'

    df = df.reset_index()

    # 檢查欄位是否有 Date 跟 Close
    if 'Date' not in df.columns or 'Close' not in df.columns:
        st.error(f"❌ {ticker} 缺少必要欄位（Date 或 Close），實際欄位：{list(df.columns)}")
        return pd.DataFrame()

    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Month'] = df['Date'].dt.to_period('M')
        df = df.drop_duplicates(subset='Month', keep='last')
    except Exception as e:
        st.error(f"❌ {ticker} 建立 Month 欄位失敗：{e}")
        return pd.DataFrame()

    df.set_index('Date', inplace=True)
    return df

# ⬇️ 抓取資料
tqqq = get_data("TQQQ")
tmf = get_data("TMF")
qqq = get_data("QQQ")

# ❗ 若任一資料為空則停止
if tqqq.empty or tmf.empty or qqq.empty:
    st.stop()

# ⬇️ 組合資料表
df = pd.DataFrame({
    'TQQQ_close': tqqq['Close'],
    'TMF_close': tmf['Close'],
    'QQQ_close': qqq['Close']
})

# ⬇️ 計算報酬與移動平均
df['TQQQ_ret'] = df['TQQQ_close'].pct_change()
df['TMF_ret'] = df['TMF_close'].pct_change()
df['TQQQ_3mo'] = df['TQQQ_ret'].rolling(3).mean()
df['TMF_3mo'] = df['TMF_ret'].rolling(3).mean()
df['QQQ_MA200'] = qqq['Close'].rolling(200).mean()
df['QQQ_above_MA'] = qqq['Close'] > df['QQQ_MA200']

# ⬇️ 策略邏輯
def decide(row):
    if not row['QQQ_above_MA']:
        return '暫時空手'
    if row['TQQQ_3mo'] > row['TMF_3mo']:
        return '持有 TQQQ'
    else:
        return '持有 TMF'

df['建議'] = df.apply(decide, axis=1)

# ⬇️ 顯示近 12 個月結果
df = df.tail(12)
st.table(df[['TQQQ_ret','TMF_ret','TQQQ_3mo','TMF_3mo','QQQ_above_MA','建議']].round(3))

# ⬇️ 當月策略建議
st.markdown("**📌 本月建議：**  " + df['建議'].iloc[-1])
