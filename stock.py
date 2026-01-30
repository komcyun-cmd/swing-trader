import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Dual-Core Swing Trader")

@st.cache_data
def get_stock_list():
    # 코스피 상위 50개 (속도를 위해 제한, 추후 확장 가능)
    df_kospi = fdr.StockListing('KOSPI')
    return df_kospi.head(50)

def get_technical_data(code, days=60):
    try:
        df = fdr.DataReader(code, datetime.datetime.now().year - 1)
        if len(df) < 60: return None
        
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        return df.tail(days)
    except:
        return None

def analyze_market(stock_list):
    sniper_list = []
    breaker_list = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, row in stock_list.iterrows():
        name = row['Name']
        code = row['Code']
        status_text.text(f"🔍 분석 중: {name} ({i+1}/{len(stock_list)})")
        progress_bar.progress((i + 1) / len(stock_list))
        
        df = get_technical_data(code)
        if df is None: continue
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # [전략 A] 눌림목
        is_uptrend = today['MA20'] > today['MA60']
        is_pullback = abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.02
        is_dry_volume = today['Volume'] < today['Vol_MA5']
        
        if is_uptrend and is_pullback and is_dry_volume:
            sniper_list.append({
                "종목명": name,
                "현재가": today['Close'],
                "20일선": round(today['MA20']),
                "추천전략": "분할매수"
            })

        # [전략 B] 돌파
        vol_spike = today['Volume'] > (yesterday['Volume'] * 2)
        strong_price = today['Change'] > 0.03
        breakout = today['Close'] >= df['High'][-20:].max()
        
        if vol_spike and strong_price and breakout:
            breaker_list.append({
                "종목명": name,
                "현재가": today['Close'],
                "등락률": f"{round(today['Change']*100, 2)}%",
                "추천전략": "추격매수"
            })
            
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(sniper_list), pd.DataFrame(breaker_list)

st.title("⚖️ Dual-Core Swing Trader (Cloud Ver.)")

if st.button("🔄 시장 스캔 시작"):
    stocks = get_stock_list()
    df_sniper, df_breaker = analyze_market(stocks)
    
    tab1, tab2 = st.tabs(["🛡️ 눌림목", "🚀 돌파"])
    with tab1:
        st.dataframe(df_sniper)
    with tab2:
        st.dataframe(df_breaker)