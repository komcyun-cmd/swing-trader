import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Dual-Core Swing Trader v2.1")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (코스닥/변동성 종목 대거 추가)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # KRX 차단 방지를 위한 하드코딩 리스트 (KOSPI 우량주 + KOSDAQ 주도주 혼합 60개)
    data = [
        # [KOSPI] 반도체/자동차/플랫폼/금융
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '005490', 'Name': 'POSCO홀딩스'}, {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '207940', 'Name': '삼성바이오로직스'},
        {'Code': '068270', 'Name': '셀트리온'}, {'Code': '105560', 'Name': 'KB금융'},
        {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '042700', 'Name': '한미반도체'},
        {'Code': '010130', 'Name': '고려아연'}, {'Code': '034020', 'Name': '두산에너빌리티'},
        {'Code': '000100', 'Name': '유한양행'}, {'Code': '011200', 'Name': 'HMM'},
        
        # [KOSDAQ] 2차전지/바이오/로봇/AI (변동성 큰 종목들)
        {'Code': '247540', 'Name': '에코프로비엠'}, {'Code': '086520', 'Name': '에코프로'},
        {'Code': '028300', 'Name': 'HLB'}, {'Code': '196170', 'Name': '알테오젠'},
        {'Code': '066970', 'Name': '엘앤에프'}, {'Code': '277810', 'Name': '레인보우로보틱스'},
        {'Code': '403870', 'Name': 'HPSP'}, {'Code': '035900', 'Name': 'JYP Ent.'},
        {'Code': '293490', 'Name': '카카오게임즈'}, {'Code': '263750', 'Name': '펄어비스'},
        {'Code': '328130', 'Name': '루닛'}, {'Code': '462510', 'Name': '두산로보틱스'},
        {'Code': '041510', 'Name': '에스엠'}, {'Code': '237690', 'Name': '에스티팜'},
        {'Code': '091990', 'Name': '셀트리온제약'}, {'Code': '214150', 'Name': '클래시스'},
        {'Code': '051900', 'Name': 'LG생활건강'}, {'Code': '090430', 'Name': '아모레퍼시픽'},
        {'Code': '009540', 'Name': 'HD한국조선해양'}, {'Code': '010950', 'Name': 'S-Oil'},
        {'Code': '015760', 'Name': '한국전력'}, {'Code': '032640', 'Name': 'LG유플러스'},
        {'Code': '003550', 'Name': 'LG'}, {'Code': '029780', 'Name': '삼성카드'},
        {'Code': '071050', 'Name': '한국금융지주'}, {'Code': '030200', 'Name': 'KT'},
        {'Code': '017670', 'Name': 'SK텔레콤'}, {'Code': '033780', 'Name': 'KT&G'},
        {'Code': '096770', 'Name': 'SK이노베이션'}, {'Code': '009830', 'Name': '한화솔루션'},
        {'Code': '112610', 'Name': '씨에스윈드'}, {'Code': '000810', 'Name': '삼성화재'}
    ]
    return pd.DataFrame(data)

def fetch_stock_data(code, name):
    try:
        # 최근 120일 데이터 (병렬 처리 최적화)
        df = fdr.DataReader(code, datetime.datetime.now().year - 1)
        if len(df) < 60: return None
        
        # 지표 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        
        today = df.iloc[-1]
        
        result = None
        
        # [전략 A] 눌림목 스나이퍼 (조건 완화: 3% 이내 접근)
        if (today['MA20'] > today['MA60']) and \
           (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
           (today['Volume'] < today['Vol_MA5']):
            result = {
                "type": "Sniper", "종목명": name, "코드": code,
                "현재가": int(today['Close']), "20일선": int(today['MA20']),
                "전략": "눌림목 매수"
            }

        # [전략 B] 돌파매매 브레이커 (조건 현실화)
        # 1. 거래량이 5일 평균보다 50% 더 터짐 (1.5배)
        # 2. 주가가 2% 이상 상승 & 양봉
        # 3. 60일선(수급선) 위에 위치
        elif (today['Volume'] > today['Vol_MA5'] * 1.5) and \
             (today['Change'] > 0.02) and \
             (today['Close'] > today['Open']) and \
             (today['Close'] > today['MA60']):
            result = {
                "type": "Breaker", "종목명": name, "코드": code,
                "현재가": int(today['Close']), 
                "등락률": round(today['Change']*100, 2),
                "전략": "추세 돌파"
            }
            
        return result
    except:
        return None

def analyze_market_parallel(stock_list):
    sniper_results = []
    breaker_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 10개씩 동시에 가져오기 (속도 10배)
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
            status_text.text(f"🚀 AI 고속 스캔 중... ({completed}/{total})")
            
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] 차트 시각화
# -----------------------------------------------------------
def draw_chart(code, name):
    df = fdr.DataReader(code, datetime.datetime.now().year - 1)
    
    candlestick = go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='Candles')
    
    ma20 = go.Scatter(x=df.index, y=df['Close'].rolling(window=20).mean(), 
                      line=dict(color='orange', width=2), name='MA20')
    ma60 = go.Scatter(x=df.index, y=df['Close'].rolling(window=60).mean(), 
                      line=dict(color='green', width=1), name='MA60')

    fig = go.Figure(data=[candlestick, ma20, ma60])
    fig.update_layout(title=f"{name} ({code}) 차트 분석", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# [4] 메인 UI
# -----------------------------------------------------------
st.title("⚖️ Dual-Core Swing Trader v2.1")
st.caption("Updated: KOSPI/KOSDAQ 주요 60개 종목 스캔")

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.sniper_df = pd.DataFrame()
    st.session_state.breaker_df = pd.DataFrame()

if st.button("🔄 시장 스캔 시작"):
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
            event1 = st.dataframe(
                st.session_state.sniper_df, 
                selection_mode="single-row", 
                on_select="rerun",
                use_container_width=True,
                hide_index=True
            )
            if len(event1.selection.rows) > 0:
                idx = event1.selection.rows[0]
                code = st.session_state.sniper_df.iloc[idx]['코드']
                name = st.session_state.sniper_df.iloc[idx]['종목명']
                st.divider()
                draw_chart(code, name)
        else:
            st.info("조건에 맞는 눌림목 종목이 없습니다.")

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
                idx = event2.selection.rows[0]
                code = st.session_state.breaker_df.iloc[idx]['코드']
                name = st.session_state.breaker_df.iloc[idx]['종목명']
                st.divider()
                draw_chart(code, name)
        else:
            st.info("오늘 돌파 조건을 만족하는 종목이 없습니다. (장이 조용할 수 있습니다)")
