import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import requests

# 1. 網頁基本設定
st.set_page_config(page_title="台股進階量化回測儀表板", layout="wide")
st.title("🛡️ 台股進階量化回測系統 (歷史資料相容優化版)")
st.markdown("本版本已全面重構資料擷取引擎，採用最穩定的 `yf.Ticker().history` 模式，解決新版套件欄位衝突問題。")

# 2. 側邊欄控制面板 (Sidebar)
st.sidebar.header("🛠️ 策略與資產設定")
stock_code = st.sidebar.text_input("輸入台股代碼", value="0050")
start_date = st.sidebar.date_input("開始日期", pd.to_datetime("2021-01-01"))
end_date = st.sidebar.date_input("結束日期", pd.to_datetime("2026-05-01"))

st.sidebar.subheader("📈 均線參數")
fast_ma = st.sidebar.slider("快線天數", min_value=5, max_value=50, value=5)
slow_ma = st.sidebar.slider("慢線天數", min_value=10, max_value=200, value=20)

st.sidebar.subheader("🧪 RSI 濾網參數")
rsi_filter_enabled = st.sidebar.checkbox("啟用 RSI 濾網", value=True)
rsi_period = st.sidebar.slider("RSI 天數", min_value=5, max_value=30, value=14)
rsi_threshold = st.sidebar.slider("買入 RSI 上限 (超過不買)", min_value=50, max_value=80, value=65)

st.sidebar.subheader("💸 交易成本設定")
is_etf = st.sidebar.checkbox("此股票為 ETF (證交稅 0.1%)", value=True)
broker_discount = st.sidebar.slider("券商手續費折數 (折)", min_value=1.0, max_value=10.0, value=2.8, step=0.1)

# 計算台股真實費率
fee_rate = (0.1425 / 100) * (broker_discount / 10)  # 買賣都要的手續費
tax_rate = 0.001 if is_etf else 0.003              # 賣出才要的證交稅

# 處理台股代碼後綴
full_stock_id = f"{stock_code}.TW" if not stock_code.endswith(('.TW', '.TWO')) else stock_code

@st.cache_data(ttl=3600)
def fetch_stock_data_safely(stock_id, start_str, end_str):
    """
    安全抓取歷史數據，包含瀏覽器標頭偽裝與快取機制
    """
    # 建立一個網路連線 Session
    session = requests.Session()
    # 填入標準的 User-Agent，讓伺服器以為我們是一台正常的 Mac 電腦上的 Chrome 瀏覽器
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    ticker_obj = yf.Ticker(stock_id, session=session)
    data = ticker_obj.history(start=start_str, end=end_str, auto_adjust=True)
    return data

if st.sidebar.button("🚀 開始運行回測"):
    with st.spinner("📡 正在安全抓取歷史數據並進行矩陣運算..."):
        
        # 🚨 【範圍優化】將 Streamlit 的 date 型態明確轉換為 yfinance 最穩定的字串格式
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 🚨 【模式優化】改用 yf.Ticker().history 模式，避開 download 帶來的 MultiIndex 陷阱
        try:
            df = fetch_stock_data_safely(full_stock_id, start_str, end_str)
        except Exception as e:
            st.error(f"連線至 Yahoo Finance 發生錯誤: {e}")
            st.stop()
        
        if df.empty:
            st.error(f"❌ 暫時無法從 Yahoo 取得資料（可能目前封鎖尚未解除）。請等幾分鐘後重試，或嘗試更換其他股票代碼觸發快取更新。")
            st.stop()
        else:
            # 確保索引格式正確
            df.index = pd.to_datetime(df.index).tz_localize(None)
                
            # 🚨 這裡的所有 'Adj Close' 全部更換為穩定的 'Close'
            df['Fast_MA'] = df['Close'].rolling(window=fast_ma).mean()
            df['Slow_MA'] = df['Close'].rolling(window=slow_ma).mean()
            
            # 計算 RSI 指標
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            
            # 避免除以零的警告
            rs = gain / loss.replace(0, np.nan)
            df['RSI'] = 100 - (100 / (1 + rs))
            df['RSI'] = df['RSI'].fillna(50) # 補值
            
            df = df.dropna(subset=['Fast_MA', 'Slow_MA']).copy()
            
            # 5. 核心交易邏輯
            ma_cross = np.where(df['Fast_MA'] > df['Slow_MA'], 1, 0)
            
            signals = []
            current_signal = 0
            for i in range(len(df)):
                rsi_condition = (not rsi_filter_enabled) or (df['RSI'].iloc[i] < rsi_threshold)
                if ma_cross[i] == 1 and rsi_condition:
                    current_signal = 1
                elif ma_cross[i] == 0:
                    current_signal = 0
                signals.append(current_signal)
                
            df['Signal'] = signals
            df['Position'] = df['Signal'].diff()
            
            # 6. 計算包含摩擦成本的報酬率
            df['Market_Return'] = df['Close'].pct_change()
            df['Raw_Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
            
            df['Cost'] = 0.0
            df.loc[df['Position'] == 1, 'Cost'] = fee_rate
            df.loc[df['Position'] == -1, 'Cost'] = fee_rate + tax_rate
            
            df['Strategy_Return'] = df['Raw_Strategy_Return'] - df['Cost']
            
            # 計算財富曲線
            df['Market_Cum'] = (1 + df['Market_Return'].fillna(0)).cumprod()
            df['Strategy_Cum'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
            
            # 7. 數據指標統計
            final_market_ret = (df['Market_Cum'].iloc[-1] - 1) * 100
            final_strategy_ret = (df['Strategy_Cum'].iloc[-1] - 1) * 100
            
            def calc_sharpe(returns):
                return (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
            
            def calc_mdd(returns):
                cum_wealth = (1 + returns.fillna(0)).cumprod()
                if len(cum_wealth) == 0: return 0
                return ((cum_wealth - cum_wealth.cummax()) / cum_wealth.cummax()).min() * 100
            
            # 8. 網頁前端呈現
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="🧘 買入持有 總報酬率", value=f"{final_market_ret:.2f}%")
                st.caption(f"大盤夏普值: {calc_sharpe(df['Market_Return']):.2f} | MDD: {calc_mdd(df['Market_Return']):.2f}%")
            with col2:
                delta_val = f"{final_strategy_ret - final_market_ret:.2f}%"
                st.metric(label="🛡️ 策略交易 總報酬率 (已扣成本)", value=f"{final_strategy_ret:.2f}%", delta=delta_val)
                st.caption(f"策略夏普值: {calc_sharpe(df['Strategy_Return']):.2f} | MDD: {calc_mdd(df['Strategy_Return']):.2f}%")
            with col3:
                total_trades = int((df['Position'] == 1).sum())
                st.metric(label="📥 總交易次數", value=f"{total_trades} 次")
                st.caption(f"已扣除單邊 {broker_discount} 折手續費與稅金")
                
            st.divider()
            
            # 9. 繪製精美雙子圖
            st.subheader("📊 策略多維度視覺化圖表")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['Market_Cum'], name='買入持有 (Market)', line=dict(color='gray', width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Strategy_Cum'], name='新濾網策略 (Strategy)', line=dict(color='blue', width=3)), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI 指標', line=dict(color='orange', width=1.5)), row=2, col=1)
            if rsi_filter_enabled:
                fig.add_trace(go.Scatter(x=df.index, y=[rsi_threshold]*len(df), name='買入 RSI 上限', line=dict(color='red', dash='dash')), row=2, col=1)
            
            fig.update_layout(hovermode="x unified", height=600, margin=dict(l=50, r=50, t=20, b=20))
            fig.update_yaxes(title_text="資產倍數", row=1, col=1)
            fig.update_yaxes(title_text="RSI 數值", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)