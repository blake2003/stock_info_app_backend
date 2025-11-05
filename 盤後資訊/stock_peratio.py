import requests
import logging
import sys
import time
import csv
import io
from typing import Dict, List, Optional, Any

# 設置常量
# ============================================

# 設置速率限制
rate_limit_seconds = 5

# 建立中文欄位名稱到英文欄位名稱的對照表（保留供內部處理使用）
field_name_mapping = {
    '日期': 'Date',
    '股票代號': 'Code',
    '股票名稱': 'Name',
    '本益比': 'PEratio',
    '殖利率(%)': 'DividendYield',
    '股價淨值比': 'PBratio',
}

# 設置 URL 和參數
url = "https://www.twse.com.tw/exchangeReport/BWIBBU_ALL?"
params = {
    'response': 'open_data', # 請求 CSV 格式
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
timeout = 20

# ============================================
# 查詢設定
# ============================================

# 證券代號篩選設定
ENABLE_FILTER = True  # True = 啟用篩選，False = 不篩選（顯示全部股票）
STOCK_CODES_TO_FILTER = [
    '0050', '2330', '2317',
    '2383', '2408', '2449', '2454', '2603', '3231', '3264', '6669'
]  # 範例：元大台灣50、台積電、鴻海、 台光電, 南亞科, 京元電子, 聯發科, 長榮, 緯創, 世芯

# ============================================

# 從 funtion 資料夾導入篩選功能
try:
    # 從 funtion 資料夾導入功能
    from funtion.stock_filter import filter_stocks_by_codes
except ImportError:
    # 如果導入失敗，嘗試相對路徑
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'funtion'))
    from stock_filter import filter_stocks_by_codes

# --- 1. 設置日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_twse_stock_peratio_csv() -> Optional[List[Dict[str, Any]]]:
    """
    抓取台灣證券交易所 (TWSE) 的「上市個股日本益比、殖利率及股價淨值比」。
    (CSV 版本 - 根據 API Schema: BWIBBU_ALL)
    """
    
    # --- 2.1 設置速率限制 ---
    logging.info(f"[Rate Limit] 尊重伺服器，暫停 {rate_limit_seconds} 秒...")
    time.sleep(rate_limit_seconds)

    logging.info(f"[Request] 開始請求「上市個股日本益比、殖利率及股價淨值比」CSV 資料")

    # --- 2.2 發出請求 ---
    try:
        response = requests.get(
            url, 
            params=params, 
            headers=headers, 
            timeout=timeout,
        )
        response.raise_for_status()
        
        if "沒有符合條件的資料" in response.text:
            logging.warning(f"[Data Error] API 回應: 沒有符合條件的資料")
            return None
            
        response.encoding = 'utf-8-sig' # 處理 BOM
        csv_file_in_memory = io.StringIO(response.text)
        reader = csv.reader(csv_file_in_memory)

        # --- 2.3 解析 CSV 資料 ---
        header = []
        header_chinese = []  # 保留原始中文標頭用於輸出
        data_rows = []
        found_header = False

        for row in reader:
            if not row:
                continue
                
            if row[0].strip() == '說明:':
                logging.info("[Parser] 偵測到 CSV 底部說明，停止解析。")
                break
                
            # --- 2.4 偵測標頭行 ---
            
            if row[0].strip() == '日期' or row[0].strip() == 'Date' or '日期' in row[0] or 'Date' in row[0]:
                header_raw = row
                found_header = True
                # 將標頭中的引號和空白去除，確保 .zip() 能夠正確對應
                # 處理全形空白、半形空白、引號、BOM 等格式問題
                header_chinese = [h.strip().replace('"', '').replace('\ufeff', '').replace('\u2000', ' ').replace('\u3000', ' ') for h in header_raw]
                
                # 將中文欄位名稱轉換為英文（僅用於日誌和內部處理參考）
                header = [field_name_mapping.get(h, h) for h in header_chinese]
                
                # 詳細日誌記錄轉換過程
                logging.info(f"[Parser] 找到 CSV 標頭行")
                logging.info(f"[Parser] 原始標頭 (中文): {header_chinese}")
                logging.debug(f"[Parser] 對照表轉換後標頭 (英文): {header}")
                
                # 檢查關鍵欄位
                if '股票代號' in header_chinese or '證券代號' in header_chinese or '代號' in header_chinese:
                    code_key = '股票代號' if '股票代號' in header_chinese else ('證券代號' if '證券代號' in header_chinese else '代號')
                    code_idx = header_chinese.index(code_key)
                    logging.info(f"[Parser] ✓ 股票代號欄位位於位置 {code_idx}: '{header_chinese[code_idx]}'")
                else:
                    logging.warning(f"[Parser] ⚠ 無法找到股票代號欄位")
                    logging.warning(f"[Parser]   所有欄位名稱: {header_chinese}")
                
                logging.debug(f"[Parser] 原始標頭 (未處理): {row}")
                continue 

            if found_header:
                # --- 2.5 確保欄位數和資料數一致 ---
                if len(row) == len(header_chinese):
                    data_rows.append(row)
                else:
                    logging.warning(f"[Parser] 忽略格式不符的資料行 (長度 {len(row)}，應為 {len(header_chinese)}): {row}")

        if not found_header:
            logging.error(f"[Parse Error] 找不到標頭行，無法解析 CSV。")
            logging.debug(f"  > 檔案開頭 (前 500 字元): {response.text[:500]}...")
            return None

        # 轉換 (Transform) - 使用原始中文標頭建立字典
        parsed_data = [dict(zip(header_chinese, row)) for row in data_rows]

        logging.info(f"[Request] ✓ 成功解析 {len(parsed_data)} 筆 (支) 股票本益比資料。")
        return parsed_data

    # 錯誤處理 (保持不變)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"[HTTP Error] {http_err.response.status_code} {http_err.response.reason}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"[Timeout Error] 請求超時")
    except csv.Error as csv_err:
        logging.error(f"[Parse Error] CSV 解析失敗: {csv_err}")
    except Exception as e:
        logging.error(f"[Unexpected Error] 發生未預期錯誤: {e}", exc_info=True)
        
    return None


# --- 3. 執行主程式 ---
if __name__ == "__main__":
    
    # ============================================
    # 執行查詢
    # ============================================
    
    logging.info(f"--- 開始抓取本益比資料 ---")
    
    # 調用抓取本益比資料函數
    market_data_list = fetch_twse_stock_peratio_csv()
    
    if market_data_list:
        # --- 3.1 如果有啟用篩選，則進行篩選 ---
        if ENABLE_FILTER:
            logging.info(f"--- 篩選證券代號: {STOCK_CODES_TO_FILTER} ---")
            market_data_list = filter_stocks_by_codes(market_data_list, STOCK_CODES_TO_FILTER)
        
        print(f"\n[結果] 抓取成功！總共 {len(market_data_list)} 支股票。")
        
        if ENABLE_FILTER:
            print(f"--- 顯示篩選後的資料 (證券代號: {STOCK_CODES_TO_FILTER}) ---")
        else:
            print(f"--- 顯示全部資料 ---")
        
        # 顯示所有欄位名稱
        if market_data_list:
            print(f"\n所有欄位名稱: {list(market_data_list[0].keys())}")
            print(f"\n{'='*80}")
        
        # 輸出所有資料，包含所有欄位
        for i, stock_data in enumerate(market_data_list):
            print(f"\n第 {i+1} 筆資料:")
            # 顯示所有欄位和對應的值
            for key, value in stock_data.items():
                print(f"  {key}: {value}")
        
        print(f"\n{'='*80}")
        print(f"[提示] 總共顯示 {len(market_data_list)} 筆資料。")
        if market_data_list:
            print(f"[提示] 每筆資料包含 {len(market_data_list[0])} 個欄位。")
    else:
        print("\n[結果] 抓取失敗。請檢查上方的 ERROR/WARNING 日誌。")
