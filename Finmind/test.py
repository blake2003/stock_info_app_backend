# 取得股價
from FinMind.data import DataLoader
# 繪製k線圖
#from FinMind import plotting
import pandas as pd
import sys # 用來檢查套件

# --- (A) 檢查與載入 mplfinance ---
try:
    import mplfinance as mpf
except ImportError:
    print("錯誤：找不到 'mplfinance' 套件。")
    print("請先執行 'pip install mplfinance' 來安裝它。")
    sys.exit()

dl = DataLoader()
# 下載台股股價資料
print("正在下載股價資料...")
stock_data = dl.taiwan_stock_daily(
    stock_id='2330', start_date='2025-01-01', end_date='2025-11-07'
)

# 下載三大法人資料
stock_data = dl.feature.add_kline_institutional_investors(
    stock_data
)

# 下載融資券資料
stock_data = dl.feature.add_kline_margin_purchase_short_sale(
    stock_data
)

# # 4. 繪製K線圖，並傳入參數
# print("正在繪製K線圖...")
# plotting.kline(
#     stock_data,
# )
# print("繪圖完成！")

# --- (C) 關鍵步驟：資料前處理 ---
# 我們需要將 FinMind 的欄位名稱改成 mplfinance 預設的名稱
print("正在準備繪圖資料...")

# 1. 複製一份資料，避免更動到原始資料
plot_df = stock_data.copy()

# 2. 重新命名 FinMind 欄位
plot_df.rename(columns={
    'date': 'Date',
    'open': 'Open',
    'max': 'High',  # FinMind 使用 'max'
    'min': 'Low',   # FinMind 使用 'min'
    'close': 'Close',
    'Trading_Volume': 'Volume' # FinMind 使用 'Trading_Volume'
}, inplace=True)

# 3. 將 'Date' 欄位轉換為 pandas 的 DatetimeIndex (這是 mplfinance 的要求)
plot_df['Date'] = pd.to_datetime(plot_df['Date'])
plot_df.set_index('Date', inplace=True)


# --- (D) 關鍵步驟：定義繪圖邏輯 ---

# 1. 找出三大法人的欄位
# (你可以自行增減要顯示的欄位)
ii_cols = [
    "Foreign_Investor_Net_Buy_Sell",
    "Investment_Trust_Net_Buy_Sell",
    "Dealer_Net_Buy_Sell",
    # "Institutional_Investor_Net_Buy_Sell" # 總和，通常看上面三個就好
]

# 2. 建立「附加圖表」(addplot) 的列表
#    這是告訴 mplfinance 我們要在 K 線圖和成交量之外「額外」畫什麼
add_plots = [
    # 關鍵：panel=2 
    # panel 0 是主圖 (K線)
    # panel 1 是 volume (成交量，我們下面會設定 volume=True 讓它自動產生)
    # panel 2 是我們指定的新子圖，用來放三大法人
    mpf.make_addplot(
        plot_df[ii_cols],
        type='bar', # 畫成柱狀圖
        panel=2,
        ylabel='Net Buy/Sell' # 設定這個子圖的 Y 軸標籤
    )
]

# --- (E) 執行繪圖 ---
print("正在使用 mplfinance 繪製圖表...")

mpf.plot(
    plot_df, 
    type='candle',        # 繪製 K 線圖
    style='yahoo',        # 使用 'yahoo' 樣式 (你也可以換成 'charles' 等)
    title='2330 K-Line with Institutional Investors',
    ylabel='Price ($)',   # 主圖 (Panel 0) 的 Y 軸標籤
    
    volume=True,          # 自動在 Panel 1 繪製成交量
    ylabel_lower='Volume',# 成交量圖 (Panel 1) 的 Y 軸標籤
    
    addplot=add_plots,    # 加入我們在 Panel 2 定義的三大法人圖
    
    panel_ratios=(3, 1, 1.5) # (可選) 調整三個子圖的高度比例 (K線:成交量:三大法人)
)

print("繪圖完成！")


# 下載三大法人資料
stock_data = dl.taiwan_stock_institutional_investors(
    stock_id="2330",
    start_date='2025-10-01',
    end_date='2025-10-07',
)

print(stock_data.head())