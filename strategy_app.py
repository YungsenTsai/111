# 111
import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="centered", page_title="策略通", page_icon="🎯")

st.markdown("<h1 style='text-align:center; color:white;'>策略通：TQQQ＋TMF 輪動策略</h1>", unsafe_allow_html=True)
st.markdown("<style>body { background-color: #121212; color: white; }</style>", unsafe_allow_html=True)

def get_data(ticker, period="2y"):
    df = yf.download(ticker, period=period, interval="1mo", progress=False)

    if df.empty:
        st.error(f"❌ 無法抓取 {ticker} 的資料，請稍後再試")
        return pd.DataFrame()

    df = df.reset_index()

    # 檢查必要欄位
    if 'Date' not in df.columns:
        st.error(f"❌ {ticker} 缺少 Date 欄位，資料格式異常")
        return pd.DataFrame()
    if 'Close' not in df.columns:
        st.error(f"❌ {ticker} 缺少 Close 欄位，資料格式異常")
        return pd.DataFrame()

    # 加入 Month 欄位
    try:
        df['Month'] = df['Date'].dt.to_period('M')
    except Exception as e:
        st.error(f"❌ {ticker} 建立 Month 欄位失敗：{e}")
        return pd.DataFrame()

    # 確認 Month 欄位成功後再 drop duplicates
    if 'Month' in df.columns:
        df = df.drop_duplicates(subset='Month', keep='last')
    else:
        st.error(f"❌ {ticker} 缺少 Month 欄位，資料格式異常")
        return pd.DataFrame()

    df.set_index('Date', inplace=True)
    return df
tqqq = get_data("TQQQ")
tmf = get_data("TMF")
qqq = get_data("QQQ")

df = pd.DataFrame({
    'TQQQ_close': tqqq['Close'],
    'TMF_close': tmf['Close'],
    'QQQ_close': qqq['Close']
})
df['TQQQ_ret'] = df['TQQQ_close'].pct_change()
df['TMF_ret'] = df['TMF_close'].pct_change()
df['TQQQ_3mo'] = df['TQQQ_ret'].rolling(3).mean()
df['TMF_3mo'] = df['TMF_ret'].rolling(3).mean()
df['QQQ_MA200'] = qqq['Close'].rolling(200).mean()
df['QQQ_above_MA'] = qqq['Close'] > df['QQQ_MA200']

def decide(row):
    if not row['QQQ_above_MA']:
        return '暫時空手'
    if row['TQQQ_3mo'] > row['TMF_3mo']:
        return '持有 TQQQ'
    else:
        return '持有 TMF'

df['建議'] = df.apply(decide, axis=1)
df = df.tail(12)

st.table(df[['TQQQ_ret','TMF_ret','TQQQ_3mo','TMF_3mo','QQQ_above_MA','建議']].round(3))

st.markdown("**📌 本月建議：**  " + df['建議'].iloc[-1])
