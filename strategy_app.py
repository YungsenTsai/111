# 策略通 App（最終穩定版）
import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="centered", page_title="策略通", page_icon="🎯")
st.markdown("<h1 style='text-align:center; color:white;'>策略通：TQQQ＋TMF 輪動策略</h1>", unsafe_allow_html=True)
st.markdown("<style>body { background-color: #121212; color: white; }</style>", unsafe_allow_html=True)

# ✅ 穩定的 get_data 函數
def get_data(ticker, period="2y"):
    df = yf.download(ticker, period=period, interval="1mo", progress=False)

    if df.empty:
        st.error(f"❌ 無法抓取 {ticker} 的資料")
        return None

    # 確保 index 是 datetime（yfinance 有時會回傳 object）
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            st.error(f"❌ {ticker} 日期轉換失敗：{e}")
            return None

    df.index.name = 'Date'
    df = df.reset_index()

    if 'Date' not in df.columns or 'Close' not in df.columns:
        st.error(f"❌ {ticker} 缺少必要欄位（Date 或 Close），目前欄位：{list(df.columns)}")
        return None

    try:
        df['Month'] = df['Date'].dt.to_period('M')
        df = df.drop_duplicates(subset='Month', keep='last')
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ {ticker} 建立 Month 欄位錯誤：{e}")
        return None

# ✅ 讀取資料
tqqq = get_data("TQQQ")
tmf = get_data("TMF")
qqq = get_data("QQQ")

if any(x is None or x.empty for x in [tqqq, tmf, qqq]):
    st.stop()

# ✅ 計算欄位與策略判斷
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

# ✅ 顯示建議結果
st.table(df[['TQQQ_ret','TMF_ret','TQQQ_3mo','TMF_3mo','QQQ_above_MA','建議']].round(3))
st.markdown("**📌 本月建議：**  " + df['建議'].iloc[-1])
