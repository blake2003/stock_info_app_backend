import yfinance as yf
import pandas as pd
import numpy as np


def to_taiwan_stock_id(code: str) -> str:
    """將使用者輸入的代碼轉為 Yahoo Finance 台股格式（自動補上 .TW）。"""
    code = code.strip().upper()
    if not code.endswith(".TW"):
        code = f"{code}.TW"
    return code


def run_golden_cross_backtest(stock_id,):
    """
    台股進階回測引擎：加入夏普值、MDD，並鎖定 2022 股災年進行壓力測試
    """
    # 1. 下載資料 (設定 auto_adjust=False 以明確保留經典的 Adj Close 欄位)
    print(f"📡 正在從 Yahoo Finance 下載 {stock_id} 的歷史資料...")
    df = yf.download(stock_id, start="2021-10-01", end="2022-12-31", auto_adjust=False)
    
    if df.empty:
        print("❌ 找不到資料，請確認代碼是否正確（如 0050、2454）。")
        return
    
    # 針對新版 yfinance 的多級索引 (MultiIndex) 進行扁平化處理
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    # 2. 計算均線指標 (利用 Pandas 的 rolling 功能)
    df['MA5'] = df['Adj Close'].rolling(window=5).mean()
    df['MA20'] = df['Adj Close'].rolling(window=20).mean()
    
    # 剔除一開始沒有均線資料的非必要天數
    df = df.dropna(subset=['MA5', 'MA20']).copy()
    
    # 3. 判斷交易訊號
    # 若 05MA > 20MA，則定義持股狀態 (Signal) 為 1，否則為 0
    df['Signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
    
    # 利用 diff() 計算部位變化：1 代表黃金交叉買進，-1 代表死亡交叉賣出
    df['Position'] = df['Signal'].diff()
    
    # 4. 計算報酬率 (簡化版：暫不計手續費與稅金)
    # 計算市場每日的基本報酬率
    df['Market_Return'] = df['Adj Close'].pct_change()
    
    # 策略報酬率 = 昨天的持股狀態 * 今天的市場報酬率 (因為昨晚收盤決定好，今天才享受損益)
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Market_Return']

    # 🚨 【關鍵步驟】截取 2022 年一整年的資料來做績效統計
    df_2022 = df.loc['2022-01-01':'2022-12-31'].copy()
    
    if df_2022.empty:
        print("❌ 2022 年資料篩選無效。")
        return
    
    # 5. 計算核心指標：累積報酬率
    cum_market = (1 + df_2022['Market_Return'].dropna()).prod() - 1
    cum_strategy = (1 + df_2022['Strategy_Return'].dropna()).prod() - 1
    
    # 統計總買進次數
    total_trades = (df['Position'] == 1).sum()

    # 6. 計算核心指標：年化夏普值 (假設無風險利率為 0)
    def calc_sharpe(returns):
        if returns.std() == 0: return 0
        # 每日平均報酬 / 每日標準差 * 根號 252 (一年大約有 252 個交易日)
        return (returns.mean() / returns.std()) * np.sqrt(252)
    
    sharpe_market = calc_sharpe(df['Market_Return'])
    sharpe_strategy = calc_sharpe(df['Strategy_Return'])

    # 7. 計算核心指標：最大回撤 (MDD)
    def calc_mdd(returns):
        # 計算資產累積財富曲線 (從 1 塊錢開始)
        cum_wealth = (1 + returns.fillna(0)).cumprod()
        # 計算歷史滾動最高點
        running_max = cum_wealth.cummax()
        # 計算每次從最高點跌下來的幅度
        drawdowns = (cum_wealth - running_max) / running_max
        return drawdowns.min() # 找出跌最慘的那一次
        
    mdd_market = calc_mdd(df['Market_Return'])
    mdd_strategy = calc_mdd(df['Strategy_Return'])
    
    # 8. 輸出終端機文字報告
    print("\n" + "🔥"*15 + " 2022 股災年壓力測試報告 " + "🔥"*15)
    print(f"📊 測試標的：{stock_id}")
    print(f"📅 統計區間：2022-01-01 ~ 2022-12-31")
    print("-" * 65)
    
    # 做出一個漂亮的對比表格
    print(f"{'績效指標':<15}{'🧘 買入持有 (Market)':<25}{'🤖 均線策略 (Strategy)':<25}")
    print("-" * 65)
    print(f"{'累積總報酬率':<13}{cum_market*100:>10.2f}%{cum_strategy*100:>22.2f}%")
    print(f"{'年化夏普值':<13}{sharpe_market:>11.2f}{sharpe_strategy:>23.2f}")
    print(f"{'歷史最大回撤':<13}{mdd_market*100:>10.2f}%{mdd_strategy*100:>22.2f}%")
    print("-" * 65)
    print(f"📥 策略總波段交易次數：{int((df_2022['Position'] == 1).sum())} 次")
    print("🔥"*38 + "\n")

if __name__ == "__main__":
    stock_code = input("請輸入台股代碼（例如 0050 或 2454）：").strip()
    if not stock_code:
        print("❌ 未輸入股票代碼，程式結束。")
    else:
        stock_id = to_taiwan_stock_id(stock_code)
        run_golden_cross_backtest(stock_id)