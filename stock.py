import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures # 병렬 처리를 위한 핵심 라이브러리
import plotly.graph_objects as go # 멋진 차트를 그리기 위한 도구

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Dual-Core Swing Trader v2.0")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (안전모드 + 병렬처리)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # [클라우드 배포용] KRX 차단 방지: 주요 종목 30개 (테스트용)
    # 로컬에서 실행할 땐 아래 주석을 풀고 fdr.StockListing('KOSPI')를 쓰셔도 됩니다.
    data = [
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '207940', 'Name': '삼성바이오로직스'},
        {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
        {'Code': '068270', 'Name': '셀트리온'}, {'Code': '005490', 'Name': 'POSCO홀딩스'},
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '051910', 'Name': 'LG화학'}, {'Code': '003550', 'Name': 'LG'},
        {'Code': '000810', 'Name': '삼성화재'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '012330', 'Name': '현대모비스'}, {'Code': '105560', 'Name': 'KB금융'},
        {'Code': '055550', 'Name': '신한지주'}, {'Code': '086790', 'Name': '하나금융지주'},
        {'Code': '032830', 'Name': '삼성생명'}, {'Code': '009150', 'Name': '삼성전기'},
        {'Code': '034020', 'Name': '두산에너빌리티'}, {'Code': '015760', 'Name': '한국전력'},
        {'Code': '003490', 'Name': '대한항공'}, {'Code': '032640', 'Name': 'LG유플러스'},
        {'Code': '011200', 'Name': 'HMM'}, {'Code': '010130', 'Name': '고려아연'},
        {'Code': '000100', 'Name': '유한양행'}, {'Code': '090430', 'Name': '아모레퍼시픽'},
        {'Code': '017670', 'Name': 'SK텔레콤'}, {'Code': '316140', 'Name': '우리금융지주'}
    ]
    return pd.DataFrame(data)

def fetch_stock_data(code, name):
    """개별 종목 데이터를 가져와 분석하는 함수 (병렬 작업자용)"""
    try:
        # 최근 120일 데이터만 가져옴 (속도 최적화)
        df = fdr.DataReader(code, datetime.datetime.now().year - 1)
        if len(df) < 60: return None
        
        # 지표 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        result = None
        
        # [전략 A] 눌림목 스나이퍼
        if (today['MA20'] > today['MA60']) and \
           (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.02) and \
           (today['Volume'] < today['Vol_MA5']):
            result = {
                "type": "Sniper", "종목명": name, "코드": code,
                "현재가": int(today['Close']), "20일선": int(today['MA20']),
                "전략": "눌림목 매수"
            }

        # [전략 B] 돌파매매 브레이커
        elif (today['Volume'] > yesterday['Volume'] * 2) and \
             (today['Change'] > 0.03) and \
             (today['Close'] >= df['High'][-20:].max()):
            result = {
                "type": "Breaker", "종목명": name, "코드": code,
                "현재가": int(today['Close']), "등락률": round(today['Change']*100, 2),
                "전략": "돌파 매수"
            }
            
        return result
    except:
        return None

def analyze_market_parallel(stock_list):
    """병렬 처리를 통해 빠르게 시장을 스캔하는 함수"""
    sniper_results = []
    breaker_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # ThreadPoolExecutor: 작업자(쓰레드) 10명을 고용해서 동시에 일을 시킴
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock_data, row['Code'], row['Name']): row for i, row in stock_list.iterrows()}
        
        total = len(stock_list)
        completed = 0
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                if res['type'] == 'Sniper':
                    sniper_results.append(res)
                elif res['type'] == 'Breaker':
                    breaker_results.append(res)
            
            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"🚀 고속 스캔 중... ({completed}/{total})")
            
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] 차트 시각화 함수
# -----------------------------------------------------------
def draw_chart(code, name):
    df = fdr.DataReader(code, datetime.datetime.now().year - 1)
    
    # 캔들 차트 생성
    candlestick = go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='Candles')
    
    # 이동평균선 추가
    ma20 = go.Scatter(x=df.index, y=df['Close'].rolling(window=20).mean(), 
                      line=dict(color='orange', width=2), name='MA20')
    ma60 = go.Scatter(x=df.index, y=df['Close'].rolling(window=60).mean(), 
                      line=dict(color='green', width=1), name='MA60')

    fig = go.Figure(data=[candlestick, ma20, ma60])
    fig.update_layout(title=f"{name} ({code}) 상세 분석", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# [4] 메인 UI
# -----------------------------------------------------------
st.title("⚖️ Dual-Core Swing Trader v2.0")

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.sniper_df = pd.DataFrame()
    st.session_state.breaker_df = pd.DataFrame()

if st.button("🔄 고속 시장 스캔 시작"):
    stocks = get_stock_list()
    df_s, df_b = analyze_market_parallel(stocks)
    st.session_state.sniper_df = df_s
    st.session_state.breaker_df = df_b
    st.session_state.scanned = True

if st.session_state.scanned:
    tab1, tab2 = st.tabs(["🛡️ 눌림목 스나이퍼", "🚀 돌파 브레이커"])
    
    # [Tab 1] 눌림목
    with tab1:
        st.subheader(f"발굴된 종목: {len(st.session_state.sniper_df)}개")
        if not st.session_state.sniper_df.empty:
            # 데이터프레임에서 행을 선택할 수 있게 설정 (single selection)
            event1 = st.dataframe(
                st.session_state.sniper_df, 
                selection_mode="single-row", 
                on_select="rerun",
                use_container_width=True,
                hide_index=True
            )
            
            # 선택된 종목이 있으면 차트 그리기
            if len(event1.selection.rows) > 0:
                selected_row_index = event1.selection.rows[0]
                selected_code = st.session_state.sniper_df.iloc[selected_row_index]['코드']
                selected_name = st.session_state.sniper_df.iloc[selected_row_index]['종목명']
                st.divider()
                draw_chart(selected_code, selected_name)
        else:
            st.info("조건에 맞는 종목이 없습니다.")

    # [Tab 2] 돌파매매
    with tab2:
        st.subheader(f"발굴된 종목: {len(st.session_state.breaker_df)}개")
        if not st.session_state.breaker_df.empty:
            event2 = st.dataframe(
                st.session_state.breaker_df, 
                selection_mode="single-row", 
                on_select="rerun",
                use_container_width=True,
                hide_index=True
            )
            
            if len(event2.selection.rows) > 0:
                selected_row_index = event2.selection.rows[0]
                selected_code = st.session_state.breaker_df.iloc[selected_row_index]['코드']
                selected_name = st.session_state.breaker_df.iloc[selected_row_index]['종목명']
                st.divider()
                draw_chart(selected_code, selected_name)
        else:
            st.info("조건에 맞는 종목이 없습니다.")
