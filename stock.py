# [수정 전 코드] (이걸 지우세요)
# @st.cache_data
# def get_stock_list():
#     df_kospi = fdr.StockListing('KOSPI')
#     return df_kospi.head(50)

# [수정 후 코드] (이걸 붙여넣으세요) - 주요 종목 하드코딩 방식
@st.cache_data
def get_stock_list():
    # KRX 차단 방지를 위해 주요 우량주 20개를 직접 정의합니다.
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
