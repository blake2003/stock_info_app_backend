import requests
import pandas as pd
import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
# 請在專案根目錄建立 .env 檔案，內容如下：
# STOCK_API_KEY=your_actual_api_key_here
load_dotenv()

# 從環境變數讀取 API 金鑰
token = os.getenv("STOCK_API_KEY")

if not token or token == "STOCK_API_KEY":
    raise ValueError(
        "請在 .env 檔案中設定 STOCK_API_KEY 環境變數。\n"
        "建立 .env 檔案並加入：STOCK_API_KEY=your_actual_api_key_here"
    )

url = "https://api.finmindtrade.com/api/v4/data"
headers = {"Authorization": f"Bearer {token}"}
parameter = {
    "dataset": "TaiwanStockPrice",
    "data_id": "2330",
    "start_date": "2025-01-01",
    "end_date": "2025-11-07",
}
resp = requests.get(url, headers=headers, params=parameter)
data = resp.json()
data = pd.DataFrame(data["data"])
print(data)

# 將資料儲存為 CSV 檔案
#data.to_csv("taiwanstock_info_2330.csv", index=False)