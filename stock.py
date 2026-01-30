import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Dual-Core Swing Trader")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (에러 방지용 하드코딩)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # KRX 접속 차단을 피하기 위해 주요 우량주 리스트를 직접 정의합니다.
    data = [
        {'Code': '005930', 'Name': '삼성전자'},
        {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '373220', 'Name': 'LG에너지솔루션'},
        {'Code': '207940', 'Name': '삼성바이오로직스'},
        {'Code': '005380', 'Name': '현대차'},
        {'Code': '000270', 'Name': '기아'},
        {'Code': '068270', 'Name': '셀트리온'},
        {'Code': '005490', 'Name': 'POSCO홀딩스'},
        {'Code': '035420', 'Name': 'NAVER'},
        {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '051910', 'Name': 'LG화학'},
        {'Code': '003550', 'Name': 'LG'},
        {'Code': '000810', 'Name': '삼성화재'},
        {'Code': '035720', 'Name': '카카오'},
        {'Code': '012330', 'Name': '현대모비스'},
        {'Code': '105560', 'Name': 'KB금융'},
        {'Code': '055550', 'Name': '신한지주'},
        {'Code': '086790', 'Name': '하나금융지주'},
        {'Code': '032830', 'Name': '삼성생명'},
        {'Code': '009150', 'Name': '삼성전기'}
    ]
    return pd.DataFrame(data)

def get_technical_data(code, days=60):
    try:
        # 최근 1년치 데이터를 가져옴
        df = fdr.DataReader(code, datetime.datetime.now().year - 1)
        if len(df) < 60: return None
        
        # 이동평균선 및 지표 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        
        return df.tail(days)
    except:
        return None

# -----------------------------------------------------------
# [3] 전략 필터링 로직
# -----------------------------------------------------------
def analyze_market(stock_list):
    sniper_list = []
    breaker_list = []
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(stock_list)
    
    for i, row in stock_list.iterrows():
        name = row['Name']
        code = row['Code']
        
        # 진행률 업데이트
        status_text.text(f"🔍 분석 중: {name} ({i+1}/{total})")
        progress_bar.progress((i + 1) / total)
        
        df = get_technical_data(code)
        if df is None: continue
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # [전략 A] 눌림목 스나이퍼
        # 1. 정배열 (MA20 > MA60)
        # 2. 눌림목 (20일선 근접, 이격도 2% 이내)
        # 3. 거래량 감소
        is_uptrend = today['MA20'] > today['MA60']
        is_pullback = abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.02
        is_dry_volume = today['Volume'] < today['Vol_MA5']
        
        if is_uptrend and is_pullback and is_dry_volume:
            sniper_list.append({
                "종목명": name,
                "현재가": f"{today['Close']:,}원",
                "20일선": f"{int(today['MA20']):,}원",
                "추천전략": "분할매수"
            })

        # [전략 B] 돌파매매 브레이커
        # 1. 거래량 폭발 (전일 대비 2배 이상)
        # 2. 강한 상승 (+3% 이상)
        # 3. 신고가 (20일 내 최고가)
        vol_spike = today['Volume'] > (yesterday['Volume'] * 2)
        strong_price = today['Change'] > 0.03
        breakout = today['Close'] >= df['High'][-20:].max()
        
        if vol_spike and strong_price and breakout:
            breaker_list.append({
                "종목명": name,
                "현재가": f"{today['Close']:,}원",
                "등락률": f"{round(today['Change']*100, 2)}%",
                "거래량급증": f"{round(today['Volume']/yesterday['Volume'], 1)}배",
                "추천전략": "추격매수"
            })
            
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(sniper_list), pd.DataFrame(breaker_list)

# -----------------------------------------------------------
# [4] 메인 화면 구성
# -----------------------------------------------------------
st.title("⚖️ Dual-Core Swing Trader (Cloud Ver.)")
st.markdown("### 당신의 선택: **🛡️ 안전한 눌림목** vs **🚀 강력한 돌파**")

if st.button("🔄 시장 스캔 시작"):
    stocks = get_stock_list()
    df_sniper, df_breaker = analyze_market(stocks)
    
    tab1, tab2 = st.tabs(["🛡️ 눌림목 스나이퍼", "🚀 돌파 브레이커"])
    
    with tab1:
        st.subheader(f"발굴된 종목: {len(df_sniper)}개")
        if not df_sniper.empty:
            st.dataframe(df_sniper)
            st.info("💡 Tip: 20일선을 손절 라인으로 잡고 분할 매수하세요.")
        else:
            st.write("현재 조건에 맞는 눌림목 종목이 없습니다.")
            
    with tab2:
        st.subheader(f"발굴된 종목: {len(df_breaker)}개")
        if not df_breaker.empty:
            st.dataframe(df_breaker)
            st.error("🔥 Warning: 변동성이 큽니다. 짧게 먹고 나오세요.")
        else:
            st.write("현재 조건에 맞는 돌파 종목이 없습니다.")
