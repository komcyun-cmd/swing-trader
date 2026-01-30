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
        # 🛡️ [전략 A] 눌림목 스나이퍼 (수정됨)
        # ---------------------------------------------------------
        if (today['MA20'] > today['MA60']) and \
           (abs(today['Close'] - today['MA20']) / today['MA20'] <= 0.03) and \
           (today['Volume'] < today['Vol_MA5']):
            
            # [수정 포인트] 손절가 계산 로직 개선
            ma20_price = int(today['MA20'])
            
            # 만약 현재가가 이미 20일선보다 낮다면? -> 현재가에서 -3%를 손절가로 잡음
            if current_price < ma20_price:
                stop_price = int(current_price * 0.97)
            else:
                # 현재가가 20일선 위에 있다면? -> 20일선을 손절가로 잡음
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
