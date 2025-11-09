from FinMind.data import DataLoader
from FinMind import plotting


dl = DataLoader()

# 1. 下載股價
print("正在下載股價資料...")
stock_data = dl.taiwan_stock_daily(
    stock_id='2330', 
    start_date='2025-01-01', 
    end_date='2025-11-07'
)

# 2. 加入三大法人資料
# print("正在整合三大法人資料...")
# stock_data = dl.feature.add_kline_institutional_investors(
#     stock_data
# ) 

# # 3. 直接繪圖
# # (更新套件後，kline() 函式應能自動偵測並分開繪製)
print("正在繪製K線圖...")
plotting.kline(stock_data)
