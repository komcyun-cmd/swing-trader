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
st.set_page_config(layout="wide", page_title="Easy Swing Trader v11.0 (Secrets)")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (Top 200)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    data = [
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '042700', 'Name': '한미반도체'}, {'Code': '000100', 'Name': '유한양행'},
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '403870', 'Name': 'HPSP'}, {'Code': '005380', 'Name': '현대차'},
        {'Code': '000270', 'Name': '기아'}, {'Code': '373220', 'Name': 'LG에너지솔루션'},
        {'Code': '006400', 'Name': '삼성SDI'}, {'Code': '051910', 'Name': 'LG화학'},
        {'Code': '005490', 'Name': 'POSCO홀딩스'}, {'Code': '247540', 'Name': '에코프로비엠'},
        {'Code': '086520', 'Name': '에코프로'}, {'Code': '066970', 'Name': '엘앤에프'},
        {'Code': '207940', 'Name': '삼성바이오로직스'}, {'Code': '068270', 'Name': '셀트리온'},
        {'Code': '028300', 'Name': 'HLB'}, {'Code': '196170', 'Name': '알테오젠'},
        {'Code': '328130', 'Name': '루닛'}, {'Code': '105560', 'Name': 'KB금융'},
        {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '277810', 'Name': '레인보우로보틱스'},
        {'Code': '462510', 'Name': '두산로보틱스'}, {'Code': '009540', 'Name': 'HD한국조선해양'},
        {'Code': '010130', 'Name': '고려아연'}, {'Code': '034020', 'Name': '두산에너빌리티'},
        {'Code': '015760', 'Name': '한국전력'}, {'Code': '012450', 'Name': '한화에어로스페이스'},
        {'Code': '010950', 'Name': 'S-Oil'}, {'Code': '003490', 'Name': '대한항공'},
        {'Code': '011200', 'Name': 'HMM'}, {'Code': '009830', 'Name': '한화솔루션'},
        {'Code': '112610', 'Name': '씨에스윈드'}, {'Code': '032640', 'Name': 'LG유플러스'},
        {'Code': '017670', 'Name': 'SK텔레콤'}, {'Code': '030200', 'Name': 'KT'}
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
        
        if (today['MA20'] > today['MA60']) and (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and (today['Volume'] < today['Vol_MA5']):
            ma20_price = int(today['MA20'])
            stop_price = int(current_price * 0.97) if current_price < ma20_price else ma20_price
            result = {"type": "Sniper", "종목명": name, "코드": code, "현재가": f"{current_price:,}원", "🔵손절가": f"{stop_price:,}원", "🔴목표가": f"{int(current_price * 1.05):,}원", "전략": "눌림목"}

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
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                if res['type'] == 'Sniper': sniper_results.append(res)
                elif res['type'] == 'Breaker': breaker_results.append(res)
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] Gemini AI 뉴스 분석 엔진
# -----------------------------------------------------------
def analyze_news_with_gemini(api_key, url, stock_list_df):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title').get_text()
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])
        content = content[:3000]

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        stock_names = ", ".join(stock_list_df['Name'].tolist())
        
        prompt = f"""
        당신은 20년 경력의 주식 트레이더입니다.
        아래 뉴스 기사를 읽고, '관심 종목 리스트'에 있는 한국 주식 중
        긍정적 영향(호재) Top 5, 부정적 영향(악재) Top 5를 선정해 주세요.
        
        [뉴스 제목] {title}
        [뉴스 본문] {content}
        [관심 종목 리스트] {stock_names}

        반드시 JSON 형식으로만 답변하세요:
        {{
            "good": [{{"stock": "종목명", "reason": "이유"}}, ...],
            "bad": [{{"stock": "종목명", "reason": "이유"}}, ...]
        }}
        """

        response = model.generate_content(prompt)
        result_text = response.text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(result_text)
        
        return title, result_json['good'], result_json['bad']

    except Exception as e:
        return None, [], []

# -----------------------------------------------------------
# [4] 메인 UI (Secrets 적용)
# -----------------------------------------------------------
st.title("💸 Easy Swing Trader v11.0 (Secrets)")

# --- [API 키 관리 로직] ---
# 1. Streamlit Secrets에서 키를 찾아본다.
# 2. 없으면 사이드바에서 입력을 받는다.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("🔑 API 키가 Secrets에서 로드되었습니다.")
except (FileNotFoundError, KeyError):
    st.sidebar.warning("Secrets에 API 키가 없습니다.")
    api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

# 탭 구성
main_tab, news_tab = st.tabs(["📊 차트 & 매매신호", "📰 Gemini 뉴스 분석"])

with main_tab:
    if st.button("🔄 종목 & 가격표 뽑기"):
        stocks = get_stock_list()
        st.toast("시장 정밀 분석 중...")
        df_s, df_b = analyze_market_parallel(stocks)
        st.session_state.sniper_df = df_s
        st.session_state.breaker_df = df_b
        st.session_state.scanned = True

    if 'scanned' in st.session_state and st.session_state.scanned:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🛡️ 눌림목")
            if not st.session_state.sniper_df.empty:
                st.dataframe(st.session_state.sniper_df, hide_index=True, use_container_width=True)
            else: st.info("종목 없음")
        with c2:
            st.subheader("🚀 돌파매매")
            if not st.session_state.breaker_df.empty:
                st.dataframe(st.session_state.breaker_df, hide_index=True, use_container_width=True)
            else: st.info("종목 없음")

with news_tab:
    st.header("🧠 Gemini AI 투자 비서")
    news_url = st.text_input("분석할 뉴스 링크(URL):", placeholder="https://n.news.naver.com/...")
    
    if st.button("🚀 AI 분석 시작"):
        if not api_key:
            st.error("⚠️ API 키가 필요합니다. (사이드바 입력 or Secrets 설정)")
        elif not news_url:
            st.warning("뉴스 링크를 입력하세요.")
        else:
            with st.spinner("Gemini가 분석 중입니다..."):
                stocks = get_stock_list()
                title, good, bad = analyze_news_with_gemini(api_key, news_url, stocks)
                
                if title:
                    st.success(f"분석 완료: **{title}**")
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📈 호재 예상")
                        for item in good:
                            st.info(f"**{item['stock']}**: {item['reason']}")
                    with col2:
                        st.subheader("📉 악재 예상")
                        for item in bad:
                            st.error(f"**{item['stock']}**: {item['reason']}")
                else:
                    st.error("분석 실패. API 키나 링크를 확인하세요.")
