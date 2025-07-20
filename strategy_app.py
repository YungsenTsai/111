import streamlit as st
import pandas as pd
import yfinance as yf

# 頁面設定
st.set_page_config(layout="centered", page_title="策略通", page_icon="🎯")
st.markdown("<h1 style='text-align:center; color:white;'>策略通：TQQQ＋TMF 輪動策略</h1>", unsafe_allow_html=True)
st.markdown("<style>body { background-color: #121212; color: white; }</style>", unsafe_allow_html=True)

# ✅ 修正後 get_data 函式（解決 Month 欄位錯誤）
def get_data(ticker, period="2y"):
    df = yf.download(ticker, period=period, interval="1mo", progress=False)

    if df.empty:
        st.error(f"❌ 無法抓取 {ticker} 的資料")
        return None

    # 修正 index 為日期型態並轉為欄位
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            st.error(f"❌ {ticker} 日期轉換失敗：{e}")
            return None

    df.reset_index(inplace=True)

    # 轉換 Date 欄位為 datetime
    try:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    except Exception as e:
        st.error(f"❌ {ticker} Date 欄位轉換失敗：{e}")
        return None

    df = df.dropna(subset=["Date"])  # 確保 Date 沒有 NaT

    if "Close" not in df.columns:
        st.error(f"❌ {ticker} 缺少 Close 欄位")
        return None

    # ✅ 確保 Month 欄位沒有衝突，重新建立
    try:
        if "Month" in df.columns:
            df.drop(columns=["Month"], inplace=True)
        df["Month"] = df["Date"].dt.to_period("M")
    except Exception as e:
        st.error(f"❌ {ticker} 建立 Month 欄位錯誤：{e}")
        return None

    # 保留每月最後一筆
    df = df.sort_values("Date")
    df = df.drop_duplicates(subset="Month", keep="last")
    df.set_index("Date", inplace=True)

    return df

# 讀取三組資料
tqqq = get_data("TQQQ")
tmf = get_data("TMF")
qqq = get_data("QQQ")

if any(x is None or x.empty for x in [tqqq, tmf, qqq]):
    st.stop()

# 整合成同一 DataFrame
df = pd.DataFrame({
    'TQQQ_close': tqqq['Close'],
    'TMF_close': tmf['Close'],
    'QQQ_close': qqq['Close']
})

# 計算報酬與指標
df['TQQQ_ret'] = df['TQQQ_close'].pct_change()
df['TMF_ret'] = df['TMF_close'].pct_change()
df['TQQQ_3mo'] = df['TQQQ_ret'].rolling(3).mean()
df['TMF_3mo'] = df['TMF_ret'].rolling(3).mean()
df['QQQ_MA200'] = df['QQQ_close'].rolling(200).mean()
df['QQQ_above_MA'] = df['QQQ_close'] > df['QQQ_MA200']

# 決策邏輯
def decide(row):
    if not row['QQQ_above_MA']:
        return '暫時空手'
    return '持有 TQQQ' if row['TQQQ_3mo'] > row['TMF_3mo'] else '持有 TMF'

df['建議'] = df.apply(decide, axis=1)
df = df.tail(12)

# 顯示結果
st.table(df[['TQQQ_ret','TMF_ret','TQQQ_3mo','TMF_3mo','QQQ_above_MA','建議']].round(3))
st.markdown("**📌 本月建議：**  " + df['建議'].iloc[-1])
