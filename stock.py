import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Easy Swing Trader v5.0 (Backtest)")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
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
        
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Change'] = df['Close'].pct_change()
        
        today = df.iloc[-1]
        current_price = int(today['Close'])
        
        result = None
        
        # [전략 A] 눌림목 스나이퍼
        if (today['MA20'] > today['MA60']) and \
           (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
           (today['Volume'] < today['Vol_MA5']):
            
            ma20_price = int(today['MA20'])
            if current_price < ma20_price:
                stop_price = int(current_price * 0.97)
            else:
                stop_price = ma20_price
                
            target_price = int(current_price * 1.05)
            
            result = {
                "type": "Sniper", "종목명": name, "코드": code,
                "현재가": f"{current_price:,}원", 
                "🔵손절가": f"{stop_price:,}원", 
                "🔴목표가": f"{target_price:,}원 (+5%)",
                "전략": "안전하게 줍기"
            }

        # [전략 B] 돌파매매 브레이커
        elif (today['Volume'] > today['Vol_MA5'] * 1.5) and \
             (today['Change'] > 0.02) and \
             (today['Close'] > today['Open']) and \
             (today['Close'] > today['MA60']):
            
            stop_price = int(current_price * 0.97)
            target_price = int(current_price * 1.05)

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
            status_text.text(f"🚀 AI 분석 중... ({completed}/{total})")
            
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] 백테스팅 엔진 (New!)
# -----------------------------------------------------------
def run_backtest(code, name, strategy_type):
    # 1년치 데이터 로드
    df = fdr.DataReader(code, datetime.datetime.now() - datetime.timedelta(days=365))
    
    # 지표 계산
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
    df['Change'] = df['Close'].pct_change()
    
    balance = 1000000 # 초기 자본금 100만원 가정
    shares = 0
    trades = [] # 매매 기록
    
    for i in range(60, len(df)): # 초기 60일은 지표 계산용으로 스킵
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        date = df.index[i]
        price = int(today['Close'])
        
        # --- 매수 로직 ---
        if shares == 0:
            buy_signal = False
            
            if strategy_type == "Sniper": # 눌림목
                if (today['MA20'] > today['MA60']) and \
                   (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
                   (today['Volume'] < today['Vol_MA5']):
                    buy_signal = True
                    
            elif strategy_type == "Breaker": # 돌파
                if (today['Volume'] > today['Vol_MA5'] * 1.5) and \
                   (today['Change'] > 0.02) and \
                   (today['Close'] > today['MA60']):
                    buy_signal = True
            
            if buy_signal:
                shares = balance // price
                balance -= shares * price
                entry_price = price
                trades.append({"date": date, "type": "BUY", "price": price})
                
        # --- 매도 로직 (보유 중일 때) ---
        else:
            # 익절: +5%, 손절: -3% (단순화)
            profit_rate = (price - entry_price) / entry_price
            
            if profit_rate >= 0.05 or profit_rate <= -0.03:
                balance += shares * price
                shares = 0
                trades.append({"date": date, "type": "SELL", "price": price, "profit": profit_rate * 100})

    # 최종 평가
    if shares > 0: # 아직 보유 중이라면 현재가로 청산 가정
        balance += shares * df.iloc[-1]['Close']
        
    total_return = (balance - 1000000) / 1000000 * 100
    win_count = sum(1 for t in trades if t.get('profit', 0) > 0)
    total_trades = sum(1 for t in trades if t['type'] == 'SELL')
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    return total_return, win_rate, total_trades, trades, df

# -----------------------------------------------------------
# [4] 차트 및 결과 시각화
# -----------------------------------------------------------
def draw_chart_with_backtest(df, trades, name):
    candlestick = go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candles')
    ma20 = go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='20일선')
    
    # 매수/매도 지점 표시
    buy_x = [t['date'] for t in trades if t['type'] == 'BUY']
    buy_y = [t['price'] for t in trades if t['type'] == 'BUY']
    sell_x = [t['date'] for t in trades if t['type'] == 'SELL']
    sell_y = [t['price'] for t in trades if t['type'] == 'SELL']
    
    buy_markers = go.Scatter(x=buy_x, y=buy_y, mode='markers', marker=dict(color='red', size=10, symbol='triangle-up'), name='Buy')
    sell_markers = go.Scatter(x=sell_x, y=sell_y, mode='markers', marker=dict(color='blue', size=10, symbol='triangle-down'), name='Sell')

    fig = go.Figure(data=[candlestick, ma20, buy_markers, sell_markers])
    fig.update_layout(title=f"{name} 1년 매매 복기", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# [5] 메인 UI
# -----------------------------------------------------------
st.title("💸 주린이 맞춤 백테스팅 시스템 v5.0")

with st.expander("📘 초보자를 위한 1분 사용설명서"):
    st.info("이 종목을 지난 1년간 **앱이 시키는 대로 사고 팔았을 때** 얼마를 벌었는지 확인해보세요.")

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
    tab1, tab2 = st.tabs(["🛡️ 눌림목 (Sniper)", "🚀 돌파매매 (Breaker)"])
    
    # [Tab 1] 눌림목
    with tab1:
        st.subheader(f"발굴된 종목: {len(st.session_state.sniper_df)}개")
        if not st.session_state.sniper_df.empty:
            st.dataframe(st.session_state.sniper_df, selection_mode="single-row", on_select="rerun", use_container_width=True, hide_index=True, key="t1")
            
            if len(st.session_state.t1.selection.rows) > 0:
                idx = st.session_state.t1.selection.rows[0]
                row = st.session_state.sniper_df.iloc[idx]
                st.divider()
                st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                
                # 백테스팅 실행
                ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Sniper")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("총 수익률 (1년)", f"{ret:.1f}%", delta_color="normal")
                c2.metric("승률 (Win Rate)", f"{win:.1f}%")
                c3.metric("매매 횟수", f"{cnt}회")
                
                draw_chart_with_backtest(hist_df, trades, row['종목명'])
        else:
            st.write("해당 조건의 종목이 없습니다.")

    # [Tab 2] 돌파매매
    with tab2:
        st.subheader(f"발굴된 종목: {len(st.session_state.breaker_df)}개")
        if not st.session_state.breaker_df.empty:
            st.dataframe(st.session_state.breaker_df, selection_mode="single-row", on_select="rerun", use_container_width=True, hide_index=True, key="t2")
            
            if len(st.session_state.t2.selection.rows) > 0:
                idx = st.session_state.t2.selection.rows[0]
                row = st.session_state.breaker_df.iloc[idx]
                st.divider()
                st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                
                # 백테스팅 실행
                ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Breaker")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("총 수익률 (1년)", f"{ret:.1f}%")
                c2.metric("승률 (Win Rate)", f"{win:.1f}%")
                c3.metric("매매 횟수", f"{cnt}회")
                
                draw_chart_with_backtest(hist_df, trades, row['종목명'])
        else:
            st.write("해당 조건의 종목이 없습니다.")
