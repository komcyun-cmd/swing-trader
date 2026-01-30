import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Easy Swing Trader v8.0 (Top 200)")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (TOP 200 하드코딩)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    # Streamlit Cloud 차단 방지를 위한 우량주 200개 리스트 (KOSPI+KOSDAQ)
    data = [
        # --- 반도체 & IT & 하드웨어 ---
        {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
        {'Code': '042700', 'Name': '한미반도체'}, {'Code': '000100', 'Name': '유한양행'},
        {'Code': '018260', 'Name': '삼성에스디에스'}, {'Code': '011070', 'Name': 'LG이노텍'},
        {'Code': '009150', 'Name': '삼성전기'}, {'Code': '403870', 'Name': 'HPSP'},
        {'Code': '005935', 'Name': '삼성전자우'}, {'Code': '003380', 'Name': '하림지주'},
        {'Code': '052690', 'Name': '한전기술'}, {'Code': '022100', 'Name': '포스코DX'},
        {'Code': '036570', 'Name': '엔씨소프트'}, {'Code': '251270', 'Name': '넷마블'},
        {'Code': '068240', 'Name': '다원시스'}, {'Code': '322000', 'Name': 'HD현대에너지솔루션'},
        {'Code': '008770', 'Name': '호텔신라'}, {'Code': '030000', 'Name': '제일기획'},
        
        # --- 플랫폼 & 게임 & 엔터 ---
        {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
        {'Code': '293490', 'Name': '카카오게임즈'}, {'Code': '263750', 'Name': '펄어비스'},
        {'Code': '035900', 'Name': 'JYP Ent.'}, {'Code': '041510', 'Name': '에스엠'},
        {'Code': '122870', 'Name': '와이지엔터테인먼트'}, {'Code': '352820', 'Name': '하이브'},
        {'Code': '090350', 'Name': '노랑풍선'}, {'Code': '079160', 'Name': 'CJ CGV'},
        {'Code': '053800', 'Name': '안랩'}, {'Code': '033640', 'Name': '네패스'},

        # --- 자동차 & 운송 & 조선 ---
        {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
        {'Code': '012330', 'Name': '현대모비스'}, {'Code': '086280', 'Name': '현대글로비스'},
        {'Code': '003490', 'Name': '대한항공'}, {'Code': '011200', 'Name': 'HMM'},
        {'Code': '000120', 'Name': 'CJ대한통운'}, {'Code': '042660', 'Name': '한화오션'},
        {'Code': '009540', 'Name': 'HD한국조선해양'}, {'Code': '010140', 'Name': '삼성중공업'},
        {'Code': '010620', 'Name': '현대미포조선'}, {'Code': '028670', 'Name': '팬오션'},
        {'Code': '003620', 'Name': '쌍용C&E'}, {'Code': '000720', 'Name': '현대건설'},

        # --- 2차전지 & 화학 & 에너지 ---
        {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '006400', 'Name': '삼성SDI'},
        {'Code': '051910', 'Name': 'LG화학'}, {'Code': '005490', 'Name': 'POSCO홀딩스'},
        {'Code': '247540', 'Name': '에코프로비엠'}, {'Code': '086520', 'Name': '에코프로'},
        {'Code': '003670', 'Name': '포스코퓨처엠'}, {'Code': '066970', 'Name': '엘앤에프'},
        {'Code': '096770', 'Name': 'SK이노베이션'}, {'Code': '051900', 'Name': 'LG생활건강'},
        {'Code': '090430', 'Name': '아모레퍼시픽'}, {'Code': '010950', 'Name': 'S-Oil'},
        {'Code': '078930', 'Name': 'GS'}, {'Code': '271560', 'Name': '오리온'},
        {'Code': '097950', 'Name': 'CJ제일제당'}, {'Code': '011170', 'Name': '롯데케미칼'},
        {'Code': '011780', 'Name': '금호석유'}, {'Code': '004020', 'Name': '현대제철'},
        {'Code': '010130', 'Name': '고려아연'}, {'Code': '009830', 'Name': '한화솔루션'},
        {'Code': '112610', 'Name': '씨에스윈드'}, {'Code': '034020', 'Name': '두산에너빌리티'},
        {'Code': '015760', 'Name': '한국전력'}, {'Code': '036460', 'Name': '한국가스공사'},
        
        # --- 바이오 & 헬스케어 ---
        {'Code': '207940', 'Name': '삼성바이오로직스'}, {'Code': '068270', 'Name': '셀트리온'},
        {'Code': '028300', 'Name': 'HLB'}, {'Code': '196170', 'Name': '알테오젠'},
        {'Code': '128940', 'Name': '한미약품'}, {'Code': '328130', 'Name': '루닛'},
        {'Code': '237690', 'Name': '에스티팜'}, {'Code': '214150', 'Name': '클래시스'},
        {'Code': '145020', 'Name': '휴젤'}, {'Code': '069620', 'Name': '대웅제약'},
        {'Code': '000100', 'Name': '유한양행'}, {'Code': '019170', 'Name': '신풍제약'},
        {'Code': '091990', 'Name': '셀트리온제약'}, {'Code': '214320', 'Name': '이노션'},
        {'Code': '235980', 'Name': '메드팩토'}, {'Code': '006280', 'Name': '녹십자'},
        {'Code': '185750', 'Name': '종근당'}, {'Code': '009290', 'Name': '광동제약'},

        # --- 금융 & 지주 & 방산 & 로봇 ---
        {'Code': '105560', 'Name': 'KB금융'}, {'Code': '055550', 'Name': '신한지주'},
        {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '316140', 'Name': '우리금융지주'},
        {'Code': '003550', 'Name': 'LG'}, {'Code': '000810', 'Name': '삼성화재'},
        {'Code': '032830', 'Name': '삼성생명'}, {'Code': '024110', 'Name': '기업은행'},
        {'Code': '029780', 'Name': '삼성카드'}, {'Code': '071050', 'Name': '한국금융지주'},
        {'Code': '277810', 'Name': '레인보우로보틱스'}, {'Code': '462510', 'Name': '두산로보틱스'},
        {'Code': '047050', 'Name': '포스코인터내셔널'}, {'Code': '012450', 'Name': '한화에어로스페이스'},
        {'Code': '064350', 'Name': '현대로템'}, {'Code': '079550', 'Name': 'LIG넥스원'},
        {'Code': '005950', 'Name': '이수화학'}, {'Code': '001450', 'Name': '현대해상'},
        {'Code': '028260', 'Name': '삼성물산'}, {'Code': '030200', 'Name': 'KT'},
        {'Code': '017670', 'Name': 'SK텔레콤'}, {'Code': '032640', 'Name': 'LG유플러스'},
        {'Code': '026960', 'Name': '동서'}, {'Code': '008930', 'Name': '한미사이언스'},
        {'Code': '016360', 'Name': '종합화학'}, {'Code': '001440', 'Name': '대한전선'},
        {'Code': '010120', 'Name': 'LS산전'}, {'Code': '006800', 'Name': '미래에셋증권'},
        {'Code': '005830', 'Name': 'DB손해보험'}, {'Code': '000080', 'Name': '하이트진로'},
        {'Code': '004990', 'Name': '롯데지주'}, {'Code': '007070', 'Name': 'GS리테일'},
        {'Code': '010060', 'Name': 'OCI'}, {'Code': '002380', 'Name': 'KCC'},
        {'Code': '039490', 'Name': '키움증권'}, {'Code': '036830', 'Name': '솔브레인'},
        {'Code': '240810', 'Name': '원익IPS'}, {'Code': '003000', 'Name': '부광약품'},
        {'Code': '088800', 'Name': '에이스테크'}, {'Code': '034220', 'Name': 'LG디스플레이'},
        {'Code': '056190', 'Name': '아미코젠'}, {'Code': '064260', 'Name': '다날'},
        {'Code': '010100', 'Name': '한국무브넥스'}, {'Code': '004370', 'Name': '농심'},
        {'Code': '280360', 'Name': '롯데웰푸드'}, {'Code': '005610', 'Name': 'SPC삼립'},
        {'Code': '003230', 'Name': '삼양식품'}, {'Code': '007310', 'Name': '오뚜기'},
        {'Code': '000990', 'Name': 'DB하이텍'}, {'Code': '020150', 'Name': '일진머티리얼즈'},
        {'Code': '036810', 'Name': '에프에스티'}, {'Code': '137400', 'Name': '피앤이솔루션'},
        {'Code': '095610', 'Name': '테스'}, {'Code': '046890', 'Name': '서울반도체'},
        {'Code': '131970', 'Name': '테크윙'}, {'Code': '074600', 'Name': '원익QnC'},
        {'Code': '051600', 'Name': '한전KPS'}, {'Code': '052690', 'Name': '한전기술'},
        {'Code': '213420', 'Name': '덕산네오룩스'}, {'Code': '089600', 'Name': '나스미디어'},
        {'Code': '039030', 'Name': '이오테크닉스'}, {'Code': '032500', 'Name': '케이엠더블유'},
        {'Code': '022100', 'Name': '포스코DX'}, {'Code': '060720', 'Name': 'KH바텍'},
        {'Code': '051915', 'Name': 'LG화학우'}, {'Code': '009155', 'Name': '삼성전기우'},
        {'Code': '066570', 'Name': 'LG전자'}, {'Code': '011210', 'Name': '현대위아'},
        {'Code': '009420', 'Name': '한올바이오파마'}, {'Code': '111770', 'Name': '영원무역'},
        {'Code': '002790', 'Name': '아모레G'}, {'Code': '034730', 'Name': 'SK'},
        {'Code': '030200', 'Name': 'KT'}, {'Code': '012630', 'Name': 'HDC'},
        {'Code': '000210', 'Name': 'DL'}, {'Code': '001040', 'Name': 'CJ'},
        {'Code': '021240', 'Name': '코웨이'}, {'Code': '032620', 'Name': '유비쿼스'},
        {'Code': '036930', 'Name': '주성엔지니어링'}, {'Code': '061970', 'Name': '소룩스'},
        {'Code': '067630', 'Name': '에이치엘비생명과학'}, {'Code': '175330', 'Name': 'JB금융지주'},
        {'Code': '000070', 'Name': '삼양홀딩스'}, {'Code': '014830', 'Name': '유니드'},
        {'Code': '001740', 'Name': 'SK네트웍스'}, {'Code': '011170', 'Name': '롯데케미칼'},
        {'Code': '011790', 'Name': 'SKC'}, {'Code': '020000', 'Name': '한섬'},
        {'Code': '030190', 'Name': '나이스정보통신'}, {'Code': '036580', 'Name': '팜스코'},
        {'Code': '093050', 'Name': 'LF'}, {'Code': '003240', 'Name': '태광산업'},
        {'Code': '004800', 'Name': '효성'}, {'Code': '009970', 'Name': '영원무역홀딩스'},
        {'Code': '010780', 'Name': '아이에스동서'}, {'Code': '023530', 'Name': '롯데쇼핑'},
        {'Code': '031430', 'Name': '신세계인터내셔날'}, {'Code': '069960', 'Name': '현대백화점'},
        {'Code': '139480', 'Name': '이마트'}, {'Code': '282330', 'Name': 'BGF리테일'},
        {'Code': '330860', 'Name': '네패스아크'}, {'Code': '348370', 'Name': '엔켐'},
        {'Code': '375500', 'Name': 'DL이앤씨'}, {'Code': '402340', 'Name': 'SK스퀘어'}
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
    
    # 200개 종목이므로 20스레드로 빠르게 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
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
            if total > 0:
                progress_bar.progress(completed / total)
            status_text.text(f"🚀 AI가 시장 정밀 타격 중... ({completed}/{total})")
            
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(sniper_results), pd.DataFrame(breaker_results)

# -----------------------------------------------------------
# [3] 백테스팅 엔진
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
                if (today['MA20'] > today['MA60']) and \
                   (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
                   (today['Volume'] < today['Vol_MA5']):
                    buy_signal = True
            elif strategy_type == "Breaker":
                if (today['Volume'] > today['Vol_MA5'] * 1.5) and \
                   (today['Change'] > 0.02) and \
                   (today['Close'] > today['MA60']):
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

    if shares > 0:
        balance += shares * df.iloc[-1]['Close']
        
    total_return = (balance - 1000000) / 1000000 * 100
    win_count = sum(1 for t in trades if t.get('profit', 0) > 0)
    total_trades = sum(1 for t in trades if t['type'] == 'SELL')
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    return total_return, win_rate, total_trades, trades, df

# -----------------------------------------------------------
# [4] 차트 시각화
# -----------------------------------------------------------
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
# [5] 메인 UI
# -----------------------------------------------------------
st.title("💸 주린이 맞춤 백테스팅 시스템 v8.0 (Top 200)")

with st.expander("📘 초보자를 위한 1분 사용설명서"):
    st.info("한국 증시를 대표하는 **Top 200 종목**을 모두 스캔합니다. (차단 걱정 없는 안전 모드)")

st.divider()

if 'scanned' not in st.session_state:
    st.session_state.scanned = False
    st.session_state.sniper_df = pd.DataFrame()
    st.session_state.breaker_df = pd.DataFrame()

if st.button("🔄 종목 & 가격표 뽑기"):
    stocks = get_stock_list()
    st.toast(f"총 {len(stocks)}개 대장주를 분석합니다. 약 1분 정도 소요됩니다!")
    
    df_s, df_b = analyze_market_parallel(stocks)
    st.session_state.sniper_df = df_s
    st.session_state.breaker_df = df_b
    st.session_state.scanned = True

if st.session_state.scanned:
    tab1, tab2 = st.tabs(["🛡️ 눌림목 (Sniper)", "🚀 돌파매매 (Breaker)"])
    
    with tab1:
        st.subheader(f"발굴된 종목: {len(st.session_state.sniper_df)}개")
        if not st.session_state.sniper_df.empty:
            st.dataframe(st.session_state.sniper_df, selection_mode="single-row", on_select="rerun", use_container_width=True, hide_index=True, key="t1")
            if len(st.session_state.t1.selection.rows) > 0:
                idx = st.session_state.t1.selection.rows[0]
                row = st.session_state.sniper_df.iloc[idx]
                st.divider()
                st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Sniper")
                c1, c2, c3 = st.columns(3)
                c1.metric("총 수익률 (1년)", f"{ret:.1f}%", delta_color="normal")
                c2.metric("승률", f"{win:.1f}%")
                c3.metric("매매 횟수", f"{cnt}회")
                draw_chart_with_backtest(hist_df, trades, row['종목명'])
        else:
            st.write("해당 조건의 종목이 없습니다.")

    with tab2:
        st.subheader(f"발굴된 종목: {len(st.session_state.breaker_df)}개")
        if not st.session_state.breaker_df.empty:
            st.dataframe(st.session_state.breaker_df, selection_mode="single-row", on_select="rerun", use_container_width=True, hide_index=True, key="t2")
            if len(st.session_state.t2.selection.rows) > 0:
                idx = st.session_state.t2.selection.rows[0]
                row = st.session_state.breaker_df.iloc[idx]
                st.divider()
                st.write(f"### 🧪 [{row['종목명']}] 백테스팅 결과")
                ret, win, cnt, trades, hist_df = run_backtest(row['코드'], row['종목명'], "Breaker")
                c1, c2, c3 = st.columns(3)
                c1.metric("총 수익률 (1년)", f"{ret:.1f}%")
                c2.metric("승률", f"{win:.1f}%")
                c3.metric("매매 횟수", f"{cnt}회")
                draw_chart_with_backtest(hist_df, trades, row['종목명'])
        else:
            st.write("해당 조건의 종목이 없습니다.")
