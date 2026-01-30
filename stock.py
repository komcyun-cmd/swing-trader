import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Easy Swing Trader v4.1")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (코스닥/변동성 종목 포함 60개)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # KRX 차단 방지용 주요 종목 리스트
    data = [
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '005490', 'Name': 'POSCO홀딩스'}, {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '207940', 'Name': '삼성바이오로직스'},
        {'Code': '068270', 'Name': '셀트리온'}, {'Code': '105560', 'Name': 'KB금융'},
        {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '042700', 'Name': '한미반도체'},
        {'Code': '247540', 'Name': '에코프로비엠'}, {'Code': '086520', 'Name': '에코프로'},
        {'Code': '028300', 'Name': 'HLB'}, {'Code': '196170', 'Name': '알테오젠'},
        {'Code': '066970', 'Name': '엘앤에프'}, {'Code': '277810', 'Name': '레인보우로보틱스'},
        {'Code': '403870', 'Name': 'HPSP'}, {'Code': '035900', 'Name': 'JYP Ent.'},
        {'Code': '293490', 'Name': '카카오게임즈'}, {'Code': '263750', 'Name': '펄어비스'},
        {'Code': '328130', 'Name': '루닛'}, {'Code': '462510', 'Name': '두산로보틱스'},
        {'Code': '041510', 'Name': '에스엠'}, {'Code': '237690', 'Name': '에스티팜'},
        {'Code': '015760', 'Name': '한국전력'}, {'Code': '032640', 'Name': 'LG유플러스'},
        {'Code': '003550', 'Name': 'LG'}, {'Code': '017670', 'Name': 'SK텔레콤'},
        {'Code': '009830', 'Name': '한화솔루션'}, {'Code': '112610', 'Name': '씨에스윈드'}
    ]
    return pd.DataFrame(data)

def fetch_stock_data(code, name):
    try:
        df = fdr.DataReader(code, datetime.datetime.now().year - 1)
        if len(df) < 60: return None
        
        # 지표 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        
        today = df.iloc[-1]
        current_price = int(today['Close'])
        
        result = None
        
        # ---------------------------------------------------------
        # 🛡️ [전략 A] 눌림목 스나이퍼 (손절가 로직 수정 완료)
        # ---------------------------------------------------------
        if (today['MA20'] > today['MA60']) and \
           (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
           (today['Volume'] < today['Vol_MA5']):
            
            ma20_price = int(today['MA20'])
            
            # [수정된 로직] 
            # 현재가가 20일선보다 낮으면 -> 현재가에서 -3%를 손절가로 설정
            # 현재가가 20일선보다 높으면 -> 20일선을 손절가로 설정
            if current_price < ma20_price:
                stop_price = int(current_price * 0.97)
            else:
                stop_price = ma20_price
                
            target_price = int(current_price * 1.05) # 목표가: +5%
            
            result = {
                "type": "Sniper", "종목명": name, "코드": code,
                "현재가": f"{current_price:,}원", 
                "🔵손절가": f"{stop_price:,}원", 
                "🔴목표가": f"{target_price:,}원 (+5%)",
                "전략": "안전하게 줍기"
            }

        # ---------------------------------------------------------
        # 🚀 [전략 B] 돌파매매 브레이커
        # ---------------------------------------------------------
        elif (today['Volume'] > today['Vol_MA5'] * 1.5) and \
             (today['Change'] > 0.02) and \
             (today['Close'] > today['Open']) and \
             (today['Close'] > today['MA60']):
            
            stop_price = int(current_price * 0.97) # 손절가: -3%
            target_price = int(current_price * 1.05) # 목표가: +5%

            result = {
                "type": "Breaker", "종목명": name, "코드": code,
                "현재가": f"{current_price:,}원", 
                "🔵손절가": f"{stop_price:,}원 (-3%)",
                "🔴목표가": f"{target_price:,}원 (+5%)",
                "전략": "빠르게 먹기"
            }
            
        return result
    except:
        return None

def analyze_market_parallel(stock_list):
    sniper_results = []
    breaker_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
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
            status_text.text(f"🚀 AI가 가격표 계산 중... ({completed}/{total})")
            
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
                      line=dict(color='orange', width=2), name='20일선(생명선)')
    
    fig = go.Figure(data=[candlestick, ma20])
    fig.update_layout(title=f"{name} 차트", xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# [4] 메인 UI
# -----------------------------------------------------------
st.title("💸 주린이 맞춤 가격표 생성기 v4.1 (Fix)")

with st.expander("📘 초보자를 위한 1분 사용설명서 (눌러서 보세요)"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 🛡️ 1. 눌림목 (Sniper)")
        st.markdown("""
        **"명품 세일 기간에 줍자"**
        - **상황:** 잘 오르던 주식이 잠깐 힘들어서 쉴 때.
        - **전략:** 쌀 때 사서 비싸게 팔기.
        - **🔵 손절가:** 가격이 이 선 밑으로 떨어지면 **"세일이 아니라 폐업"**이니까 도망가세요.
        - **🔴 목표가:** 욕심부리지 말고 여기서 챙기세요.
        """)
        
    with col2:
        st.error("### 🚀 2. 돌파매매 (Breaker)")
        st.markdown("""
        **"출발하는 고속버스에 타자"**
        - **상황:** 주식이 갑자기 거래량이 터지며 급등할 때.
        - **전략:** 비싸게 사서 더 비싸게 팔기.
        - **🔵 손절가:** 버스가 후진하면 큰일 납니다. **-3%** 되면 뒤도 보지 말고 내리세요.
        - **🔴 목표가:** 짧고 굵게 먹고 내리세요.
        """)

st.divider()

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.sniper_df = pd.DataFrame()
    st.session_state.breaker_df = pd.DataFrame()

if st.button("🔄 종목 & 가격표 뽑기"):
    stocks = get_stock_list()
    df_s, df_b = analyze_market_parallel(stocks)
    st.session_state.sniper_df = df_s
    st.session_state.breaker_df = df_b
    st.session_state.scanned = True

if st.session_state.scanned:
    tab1, tab2 = st.tabs(["🛡️ 안전하게 (눌림목)", "🚀 빠르게 (돌파)"])
    
    # [Tab 1] 눌림목
    with tab1:
        st.subheader(f"발굴된 종목: {len(st.session_state.sniper_df)}개")
        if not st.session_state.sniper_df.empty:
            st.dataframe(
                st.session_state.sniper_df, 
                selection_mode="single-row", 
                on_select="rerun",
                use_container_width=True,
                hide_index=True,
                key="sniper_table"
            )
            if len(st.session_state.sniper_table.selection.rows) > 0:
                idx = st.session_state.sniper_table.selection.rows[0]
                code = st.session_state.sniper_df.iloc[idx]['코드']
                name = st.session_state.sniper_df.iloc[idx]['종목명']
                st.divider()
                draw_chart(code, name)
        else:
            st.write("지금 싸게 살만한 종목이 없네요.")

    # [Tab 2] 돌파매매
    with tab2:
        st.subheader(f"발굴된 종목: {len(st.session_state.breaker_df)}개")
        if not st.session_state.breaker_df.empty:
            st.dataframe(
                st.session_state.breaker_df, 
                selection_mode="single-row", 
                on_select="rerun",
                use_container_width=True,
                hide_index=True,
                key="breaker_table"
            )
            if len(st.session_state.breaker_table.selection.rows) > 0:
                idx = st.session_state.breaker_table.selection.rows[0]
                code = st.session_state.breaker_df.iloc[idx]['코드']
                name = st.session_state.breaker_df.iloc[idx]['종목명']
                st.divider()
                draw_chart(code, name)
        else:
            st.write("지금 급등하는 종목이 없네요.")
