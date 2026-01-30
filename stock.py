import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Easy Swing Trader v12.0 (Ultimate)")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (TOP 200 하드코딩)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # Top 200 우량주 리스트 (KOSPI + KOSDAQ)
    data = [
        # --- 반도체 & IT ---
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '042700', 'Name': '한미반도체'}, {'Code': '000100', 'Name': '유한양행'},
        {'Code': '018260', 'Name': '삼성에스디에스'}, {'Code': '011070', 'Name': 'LG이노텍'},
        {'Code': '009150', 'Name': '삼성전기'}, {'Code': '403870', 'Name': 'HPSP'},
        {'Code': '005935', 'Name': '삼성전자우'}, {'Code': '003380', 'Name': '하림지주'},
        {'Code': '052690', 'Name': '한전기술'}, {'Code': '022100', 'Name': '포스코DX'},
        {'Code': '036570', 'Name': '엔씨소프트'}, {'Code': '251270', 'Name': '넷마블'},
        
        # --- 자동차 & 운송 ---
        {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
        {'Code': '012330', 'Name': '현대모비스'}, {'Code': '086280', 'Name': '현대글로비스'},
        {'Code': '003490', 'Name': '대한항공'}, {'Code': '011200', 'Name': 'HMM'},
        {'Code': '000120', 'Name': 'CJ대한통운'}, {'Code': '042660', 'Name': '한화오션'},
        {'Code': '009540', 'Name': 'HD한국조선해양'}, {'Code': '010140', 'Name': '삼성중공업'},
        {'Code': '010620', 'Name': '현대미포조선'}, {'Code': '028670', 'Name': '팬오션'},

        # --- 2차전지 & 화학 ---
        {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '051910', 'Name': 'LG화학'}, {'Code': '005490', 'Name': 'POSCO홀딩스'},
        {'Code': '247540', 'Name': '에코프로비엠'}, {'Code': '086520', 'Name': '에코프로'},
        {'Code': '003670', 'Name': '포스코퓨처엠'}, {'Code': '066970', 'Name': '엘앤에프'},
        {'Code': '096770', 'Name': 'SK이노베이션'}, {'Code': '051900', 'Name': 'LG생활건강'},
        {'Code': '090430', 'Name': '아모레퍼시픽'}, {'Code': '010950', 'Name': 'S-Oil'},
        {'Code': '078930', 'Name': 'GS'}, {'Code': '011170', 'Name': '롯데케미칼'},
        {'Code': '010130', 'Name': '고려아연'}, {'Code': '009830', 'Name': '한화솔루션'},
        {'Code': '112610', 'Name': '씨에스윈드'}, {'Code': '034020', 'Name': '두산에너빌리티'},

        # --- 바이오 & 헬스케어 ---
        {'Code': '207940', 'Name': '삼성바이오로직스'}, {'Code': '068270', 'Name': '셀트리온'},
        {'Code': '028300', 'Name': 'HLB'}, {'Code': '196170', 'Name': '알테오젠'},
        {'Code': '128940', 'Name': '한미약품'}, {'Code': '328130', 'Name': '루닛'},
        {'Code': '237690', 'Name': '에스티팜'}, {'Code': '214150', 'Name': '클래시스'},
        {'Code': '145020', 'Name': '휴젤'}, {'Code': '069620', 'Name': '대웅제약'},
        {'Code': '000100', 'Name': '유한양행'}, {'Code': '006280', 'Name': '녹십자'},

        # --- 금융 & 지주 ---
        {'Code': '105560', 'Name': 'KB금융'}, {'Code': '055550', 'Name': '신한지주'},
        {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '316140', 'Name': '우리금융지주'},
        {'Code': '003550', 'Name': 'LG'}, {'Code': '000810', 'Name': '삼성화재'},
        {'Code': '032830', 'Name': '삼성생명'}, {'Code': '024110', 'Name': '기업은행'},
        {'Code': '029780', 'Name': '삼성카드'}, {'Code': '071050', 'Name': '한국금융지주'},

        # --- 플랫폼 & 엔터 & 로봇 ---
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '293490', 'Name': '카카오게임즈'}, {'Code': '263750', 'Name': '펄어비스'},
        {'Code': '035900', 'Name': 'JYP Ent.'}, {'Code': '041510', 'Name': '에스엠'},
        {'Code': '352820', 'Name': '하이브'}, {'Code': '277810', 'Name': '레인보우로보틱스'},
        {'Code': '462510', 'Name': '두산로보틱스'}, {'Code': '012450', 'Name': '한화에어로스페이스'},
        {'Code': '079550', 'Name': 'LIG넥스원'}, {'Code': '017670', 'Name': 'SK텔레콤'},
        {'Code': '030200', 'Name': 'KT'}, {'Code': '032640', 'Name': 'LG유플러스'}
        # (지면 관계상 줄였으나, 실제로는 여기에 200개를 채우시면 됩니다!)
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
        
        # [전략 A] 눌림목
        if (today['MA20'] > today['MA60']) and (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and (today['Volume'] < today['Vol_MA5']):
            ma20_price = int(today['MA20'])
            stop_price = int(current_price * 0.97) if current_price < ma20_price else ma20_price
            result = {"type": "Sniper", "종목명": name, "코드": code, "현재가": f"{current_price:,}원", "🔵손절가": f"{stop_price:,}원", "🔴목표가": f"{int(current_price * 1.05):,}원", "전략": "눌림목"}

        # [전략 B] 돌파
        elif (today['Volume'] > today['Vol_MA5'] * 1.5) and (today['Change'] > 0.02) and (today['Close'] > today['MA60']):
            result = {"type": "Breaker", "종목명": name, "코드": code, "현재가": f"{current_price:,}원", "🔵손절가": f"{int(current_price * 0.97):,}원", "🔴목표가": f"{int(current_price * 1.05):,}원", "전략": "돌파"}
            
        return result
    except:
        return None

def analyze_market_parallel(stock_list):
    sniper_results = []
    breaker_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_stock_data, row['Code'], row['Name']): row for i, row in stock_list.iterrows()}
        total = len(stock_list)
        completed = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                if res['type'] == 'Sniper': sniper_results.append(res)
                elif res['type'] == 'Breaker': breaker_results.append(res)
            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"🚀 Top 200 분석 중... ({completed}/{total})")
            
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] 백테스팅 엔진 (부활!)
# -----------------------------------------------------------
def run_backtest(code, name, strategy_type):
    df = fdr.DataReader(code, datetime.datetime.now() - datetime.timedelta(days=365))
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
    df['Change'] = df['Close'].pct_change()
    
    balance = 1000000
    shares = 0
    trades = []
    
    for i in range(60, len(df)):
        today = df.iloc[i]
        date = df.index[i]
        price = int(today['Close'])
        
        if shares == 0:
            buy_signal = False
            if strategy_type == "Sniper":
                if (today['MA20'] > today['MA60']) and (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and (today['Volume'] < today['Vol_MA5']):
                    buy_signal = True
            elif strategy_type == "Breaker":
                if (today['Volume'] > today['Vol_MA5'] * 1.5) and (today['Change'] > 0.02) and (today['Close'] > today['MA60']):
                    buy_signal = True
            if buy_signal:
                shares = balance // price
                balance -= shares * price
                entry_price = price
                trades.append({"date": date, "type": "BUY", "price": price})
        else:
            profit_rate = (price - entry_price) / entry_price
            if profit_rate >= 0.05 or profit_rate <= -0.03:
                balance += shares * price
                shares = 0
                trades.append({"date": date, "type": "SELL", "price": price, "profit": profit_rate * 100})

    if shares > 0: balance += shares * df.iloc[-1]['Close']
    total_return = (balance - 1000000) / 1000000 * 100
    win_count = sum(1 for t in trades if t.get('profit', 0) > 0)
    total_trades = sum(1 for t in trades if t['type'] == 'SELL')
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    return total_return, win_rate, total_trades, trades, df

def draw_chart_with_backtest(df, trades, name):
    candlestick = go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candles')
    ma20 = go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='20일선')
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
# [4] Gemini AI 뉴스 분석 엔진
# -----------------------------------------------------------
def analyze_news_with_gemini(api_key, url, stock_list_df):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').get_text()
        content = " ".join([p.get_text() for p in soup.find_all('p')])[:3000]

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        stock_names = ", ".join(stock_list_df['Name'].tolist())
        prompt = f"""
        당신은 주식 트레이더입니다. 뉴스 기사를 읽고 '관심 종목 리스트'({stock_names}) 중
        호재 Top 5, 악재 Top 5를 선정해 주세요.
        
        [뉴스] {title}
        {content}

        JSON 형식으로만 답하세요:
        {{ "good": [{{"stock": "종목명", "reason": "이유"}}], "bad": [{{"stock": "종목명", "reason": "이유"}}] }}
        """
        response = model.generate_content(prompt)
        result_text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(result_text)
        return title, result_json['good'], result_json['bad']
    except: return None, [], []

# -----------------------------------------------------------
# [5] 메인 UI (모든 기능 통합)
# -----------------------------------------------------------
st.title("💸 Easy Swing Trader v12.0 (Ultimate)")

# API 키 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("🔑 API 키 로드 완료")
except:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

main_tab, news_tab = st.tabs(["📊 차트/백테스트", "📰 뉴스 AI 분석"])

# --- Tab 1: 차트 & 백테스트 ---
with main_tab:
    if st.button("🔄 Top 200 스캔 시작"):
        stocks = get_stock_list()
        df_s, df_b = analyze_market_parallel(stocks)
        st.session_state.sniper_df = df_s
        st.session_state.breaker_df = df_b
        st.session_state.scanned = True

    if 'scanned' in st.session_state and st.session_state.scanned:
        t1, t2 = st.tabs(["🛡️ 눌림목", "🚀 돌파매매"])
        
        with t1:
            st.subheader(f"발굴된 종목: {len(st.session_state.sniper_df)}개")
            if not st.session_state.sniper_df.empty:
                st.dataframe(st.session_state.sniper_df, selection_mode="single-row", on_select="rerun", hide_index=True, key="grid1")
                if len(st.session_state.grid1.selection.rows) > 0:
                    idx = st.session_state.grid1.selection.rows[0]
                    row = st.session_state.sniper_df.iloc[idx]
                    st.divider()
                    st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                    ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Sniper")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("1년 수익률", f"{ret:.1f}%")
                    c2.metric("승률", f"{win:.1f}%")
                    c3.metric("매매횟수", f"{cnt}회")
                    draw_chart_with_backtest(hist_df, trades, row['종목명'])
            else: st.info("종목 없음")

        with t2:
            st.subheader(f"발굴된 종목: {len(st.session_state.breaker_df)}개")
            if not st.session_state.breaker_df.empty:
                st.dataframe(st.session_state.breaker_df, selection_mode="single-row", on_select="rerun", hide_index=True, key="grid2")
                if len(st.session_state.grid2.selection.rows) > 0:
                    idx = st.session_state.grid2.selection.rows[0]
                    row = st.session_state.breaker_df.iloc[idx]
                    st.divider()
                    st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                    ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Breaker")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("1년 수익률", f"{ret:.1f}%")
                    c2.metric("승률", f"{win:.1f}%")
                    c3.metric("매매횟수", f"{cnt}회")
                    draw_chart_with_backtest(hist_df, trades, row['종목명'])
            else: st.info("종목 없음")

# --- Tab 2: 뉴스 AI ---
with news_tab:
    st.header("🧠 Gemini AI 투자 비서")
    url = st.text_input("뉴스 링크 입력:")
    if st.button("🚀 AI 분석 시작"):
        if api_key and url:
            with st.spinner("분석 중..."):
                stocks = get_stock_list()
                title, good, bad = analyze_news_with_gemini(api_key, url, stocks)
                if title:
                    st.success(f"**{title}**")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("📈 호재")
                        for i in good: st.success(f"**{i['stock']}**: {i['reason']}")
                    with c2:
                        st.subheader("📉 악재")
                        for i in bad: st.error(f"**{i['stock']}**: {i['reason']}")
        else: st.error("API 키와 링크를 확인하세요.")
