import streamlit as str
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本設定
str.set_page_config(page_title="台股量化回測儀表板", layout="wide")
str.title("📈 台股均線策略量化回測系統")
str.markdown("不用懂微服務，用純 Python 打造你的第一個金融科技 Side Project！")

# 2. 側邊欄控制面板 (Sidebar)
str.sidebar.header("🛠️ 策略參數設定")
stock_code = str.sidebar.text_input("輸入台股代碼", value="0050")
start_date = str.sidebar.date_input("開始日期", pd.to_datetime("2021-01-01"))
end_date = str.sidebar.date_input("結束日期", pd.to_datetime("2025-12-31"))

fast_ma = str.sidebar.slider("快線天數 (短均線)", min_value=5, max_value=50, value=5)
slow_ma = str.sidebar.slider("慢線天數 (長均線)", min_value=10, max_value=200, value=20)

# 轉換成 yfinance 格式
full_stock_id = f"{stock_code}.TW" if not stock_code.endswith(('.TW', '.TWO')) else stock_code

# 點擊按鈕才開始執行
if str.sidebar.button("🚀 開始運行回測"):
    with str.spinner("📡 正在全面全面搜集歷史數據並計算中..."):
        
        # 3. 資料抓取
        df = yf.download(full_stock_id, start=start_date, end=end_date, auto_adjust=False)
        
        if df.empty:
            str.error(f"❌ 找不到 {full_stock_id} 的資料，請確認代碼是否輸入正確（例如上市 0050，或上櫃需手動輸入 .TWO）。")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # 4. 核心計算
            df['Fast_MA'] = df['Adj Close'].rolling(window=fast_ma).mean()
            df['Slow_MA'] = df['Adj Close'].rolling(window=slow_ma).mean()
            df = df.dropna(subset=['Fast_MA', 'Slow_MA']).copy()
            
            df['Signal'] = np.where(df['Fast_MA'] > df['Slow_MA'], 1, 0)
            df['Market_Return'] = df['Adj Close'].pct_change()
            df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']
            
            # 累積財富曲線 (從 1 塊錢開始累積)
            df['Market_Cum'] = (1 + df['Market_Return'].fillna(0)).cumprod()
            df['Strategy_Cum'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()
            
            # 指標統計
            final_market_ret = (df['Market_Cum'].iloc[-1] - 1) * 100
            final_strategy_ret = (df['Strategy_Cum'].iloc[-1] - 1) * 100
            
            def calc_sharpe(returns):
                return (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
            
            sharpe_market = calc_sharpe(df['Market_Return'])
            sharpe_strategy = calc_sharpe(df['Strategy_Return'])
            
            # 5. 網頁視覺化呈現
            # A. 數據資訊看板 (Metrics)
            col1, col2, col3 = str.columns(3)
            with col1:
                str.metric(label="🧘 買入持有 總報酬率", value=f"{final_market_ret:.2f}%")
                str.caption(f"大盤年化夏普值: {sharpe_market:.2f}")
            with col2:
                # 這裡加個顏色反饋，如果策略贏了就顯示綠色/正向
                delta_val = f"{final_strategy_ret - final_market_ret:.2f}%"
                str.metric(label="🤖 均線策略 總報酬率", value=f"{final_strategy_ret:.2f}%", delta=delta_val)
                str.caption(f"策略年化夏普值: {sharpe_strategy:.2f}")
            with col3:
                total_trades = int(df['Signal'].diff().abs().sum() / 2)
                str.metric(label="📥 總交易次數", value=f"{total_trades} 次")
                str.caption("一個完整的買進與賣出算一次")
                
            str.divider()
            
            # B. 繪製互動式財富曲線圖 (Plotly Chart)
            str.subheader("📈 資產累積財富曲線對比圖")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Market_Cum'], name='買入持有 (Market)', line=dict(color='gray', width=2)))
            fig.add_trace(go.Scatter(x=df.index, y=df['Strategy_Cum'], name='均線策略 (Strategy)', line=dict(color='green', width=3)))
            
            fig.update_layout(
                hovermode="x unified",
                xaxis_title="日期",
                yaxis_title="資產倍數 (從 1.0 開始)",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            str.plotly_chart(fig, use_container_width=True)
            
            # C. 顯示原始數據表格
            with str.expander("🔍 點擊查看歷史明細數據"):
                str.dataframe(df[['Adj Close', 'Fast_MA', 'Slow_MA', 'Signal']].tail(100), use_container_width=True)