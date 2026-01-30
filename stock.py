import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import concurrent.futures
import plotly.graph_objects as go

# -----------------------------------------------------------
# [1] 기본 설정
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Easy Swing Trader v6.0 (Max)")

# -----------------------------------------------------------
# [2] 데이터 수집 엔진 (스마트 하이브리드 모드)
# -----------------------------------------------------------
@st.cache_data
def get_stock_list():
    try:
        # 1차 시도: 시장 전체에서 시가총액 상위 500개 긁어오기 (약 30초 소요)
        df_kospi = fdr.StockListing('KOSPI')
        df_kosdaq = fdr.StockListing('KOSDAQ')
        
        # 유동성이 좋은 상위 종목만 추림 (잡주 제외)
        kospi_top = df_kospi.sort_values('Marcap', ascending=False).head(300)
        kosdaq_top = df_kosdaq.sort_values('Marcap', ascending=False).head(200)
        
        # 합치기
        combined = pd.concat([kospi_top, kosdaq_top])
        return combined[['Code', 'Name']]
        
    except Exception as e:
        # 실패 시 (서버 차단 등): 안전한 핵심 종목 60개로 자동 전환
        # st.toast("⚠️ 전체 데이터 수집 실패! 안전 모드(60개)로 전환합니다.") 
        data = [
            {'Code': '005930', 'Name': '삼성전자'}, {'Code': '000660', 'Name': 'SK하이닉스'},
            {'Code': '005380', 'Name': '현대차'}, {'Code': '000270', 'Name': '기아'},
            {'Code': '035420', 'Name': 'NAVER'}, {'Code': '035720', 'Name': '카카오'},
            {'Code': '005490', 'Name': 'POSCO홀딩스'}, {'Code': '006400', 'Name': '삼성SDI'},
            {'Code': '373220', 'Name': 'LG에너지솔루션'}, {'Code': '207940', 'Name': '삼성바이오로직스'},
            {'Code': '068270', 'Name': '셀트리온'}, {'Code': '105560', 'Name': 'KB금융'},
            {'Code': '086790', 'Name': '하나금융지주'}, {'Code': '042700', 'Name': '한미반도체'},
            {'Code': '247540', 'Name': '에코프로비엠'},
