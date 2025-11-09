from FinMind.data import DataLoader
import pandas as pd
import sys

# --- (A) 載入 mplfinance ---
try:
    import mplfinance as mpf
except ImportError:
    print("錯誤：找不到 'mplfinance' 套件。")
    print("請先執行 'pip install mplfinance' 來安裝它。")
    sys.exit()

# --- (B) FinMind 資料載入 ---
dl = DataLoader()

print("正在下載股價資料...")
stock_data = dl.taiwan_stock_daily(
    stock_id='2330', 
    start_date='2025-01-01', 
    end_date='2025-11-07'
)

print("正在整合三大法人資料...")
stock_data = dl.feature.add_kline_institutional_investors(
    stock_data
) 

# --- (C) 關鍵修改點：加入偵錯 (Debug) ---
# 讓我們檢查 FinMind 到底回傳了哪些欄位
print("\n--- 檢查 FinMind 回傳的欄位 ---")
print(stock_data.columns)
print("---------------------------------\n")


# --- (D) 資料前處理 (改成 mplfinance 格式) ---
print("正在準備 mplfinance 繪圖資料...")
plot_df = stock_data.copy()

plot_df.rename(columns={
    'date': 'Date',
    'open': 'Open',
    'max': 'High',
    'min': 'Low',
    'close': 'Close',
    'Trading_Volume': 'Volume'
}, inplace=True)

plot_df['Date'] = pd.to_datetime(plot_df['Date'])
plot_df.set_index('Date', inplace=True)


# --- (E) 關鍵修改點：穩健的繪圖邏輯 ---

# 1. 定義我們「想要」畫的三大法人欄位（只包含數值欄位）
ii_cols_we_want = [
    "buy",      # 買進
    "sell",     # 賣出
]

# 2. 檢查這些欄位「實際存在」於 plot_df 中的有哪些
available_ii_cols = [col for col in ii_cols_we_want if col in plot_df.columns]

# 3. 過濾出數值類型的欄位（排除字串、日期等非數值欄位）
numeric_ii_cols = []
for col in available_ii_cols:
    if col in plot_df.columns:
        # 檢查欄位是否為數值類型
        if pd.api.types.is_numeric_dtype(plot_df[col]):
            numeric_ii_cols.append(col)
        else:
            print(f"⚠️ 跳過非數值欄位: {col} (類型: {plot_df[col].dtype})")

add_plots = [] # 先建立一個空的附加圖表列表

# 4. 只有在「真的有」數值類型的三大法人欄位時，才去建立附加圖表
if numeric_ii_cols:
    print(f"偵測到可用的數值型三大法人欄位: {numeric_ii_cols}")
    # 準備三大法人資料，確保都是數值類型
    ii_data = plot_df[numeric_ii_cols].copy()
    # 確保所有欄位都是數值類型
    for col in numeric_ii_cols:
        ii_data[col] = pd.to_numeric(ii_data[col], errors='coerce')
    
    # 只選擇數值欄位進行繪圖
    add_plots = [
        mpf.make_addplot(
            ii_data, # 只畫數值類型的欄位
            type='bar',
            panel=2, # 畫在第 2 號子圖
            ylabel='Net Buy/Sell'
        )
    ]
else:
    print("⚠️ 警告：在資料中找不到可繪製的數值型三大法人欄位。")
    print("將只繪製 K 線與成交量。")


# --- (F) 執行繪圖 ---
print("正在使用 mplfinance 繪製圖表...")

# 確保 plot_df 只包含 K 線所需的 OHLCV 欄位
ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
plot_data = plot_df[ohlcv_cols].copy()

# 確保所有數值欄位都是數值類型
for col in ohlcv_cols:
    if col in plot_data.columns:
        plot_data[col] = pd.to_numeric(plot_data[col], errors='coerce')

mpf.plot(
    plot_data,  # 只使用 OHLCV 欄位
    type='candle',
    style='yahoo',
    title='2330 K-Line with Volume and Institutional Investors',
    ylabel='Price ($)',
    
    volume=True,          # 自動在 Panel 1 繪製成交量
    ylabel_lower='Volume',
    
    addplot=add_plots if add_plots else None,    # 加入我們的圖表（如果有的話）
    
    # 根據 add_plots 是否為空，動態調整子圖比例
    panel_ratios=(3, 1, 1.5) if add_plots else (3, 1) 
)

print("繪圖完成！")