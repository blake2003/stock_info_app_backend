import requests
import logging
import sys
import time
import csv
import io
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# 設置常量
# ============================================

# 設置速率限制
rate_limit_seconds = 3
# 建立中文欄位名稱到英文欄位名稱的對照表（保留供內部處理使用）
field_name_mapping = {
    '日期': 'Date',
    '證券代號': 'Code',
    '證券名稱': 'Name',
    '成交股數': 'TradeVolume',
    '成交金額': 'TradeValue',
    '開盤價': 'Open',
    '最高價': 'High',
    '最低價': 'Low',
    '收盤價': 'Close',
    '漲跌價差': 'Change',
    '成交筆數': 'Transaction',
}
# 設置 URL 和參數 ---
url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?"
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
     '2383', '2408', '8229', '2449', '2454', '2603', '3231', '3264', '6669'
 ]  # 範例：元大台灣50、台積電、鴻海、 台光電, 南亞科, 京元電子, 聯發科, 長榮, 緯創, 世芯

# 排序設定
SORT_BY_CHANGE = False  # True = 按照漲跌價差遞減排序，False = 不排序（保持原始順序）
SORT_REVERSE = True    # True = 遞減排序（漲幅最大在前），False = 遞增排序（跌幅最大在前）
    
# ============================================



# 從 funtion 資料夾導入篩選、排序、日誌設置和 CSV 儲存功能
try:
    # 從 funtion 資料夾導入功能
    from funtion.stock_filter import filter_stocks_by_codes, sort_by_change
    from funtion.logger_config import setup_logger
    from funtion.csv_saver import save_data_to_csv, get_output_dir
except ImportError:
    # 如果導入失敗，嘗試相對路徑
    # (當作主程式執行時，__file__ 會是 '盤後資訊/stock_day.py'，
    # os.path.dirname(__file__) 是 '盤後資訊'
    # '..' 會往上一層到專案根目錄)
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from funtion.stock_filter import filter_stocks_by_codes, sort_by_change
    from funtion.logger_config import setup_logger
    from funtion.csv_saver import save_data_to_csv, get_output_dir

# --- 1. 設置日誌 ---
# (日誌僅寫入檔案，不輸出到控制台)
setup_logger('stock_day', log_subdir='csv_log')

# --- 2. 抓取全市場資料 ---
def fetch_twse_market_day_all_csv() -> Optional[List[Dict[str, Any]]]:
    """
    抓取台灣證券交易所 (TWSE) 的「全市場」每日成交資料。
    (CSV 版本 - 已修正標頭偵測)
    注意：此 API 不支援日期篩選，將返回最新的全市場資料。
    """

    # --- 2.1 設置速率限制 ---
    logging.info(f"[Rate Limit] 暫歇 {rate_limit_seconds} 秒...")
    time.sleep(rate_limit_seconds)

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
        date_logged = False  # 追蹤是否已記錄日期日誌
        

        for row in reader:
            if not row:
                continue
                
            if row[0].strip() == '說明:':
                logging.info("[Parser] 偵測到 CSV 底部說明，停止解析。")
                break
                
            # --- 2.5 偵測標頭行 ---
            if row[0].strip() == '日期':
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
                if '證券代號' in header_chinese or '代號' in header_chinese:
                    code_idx = header_chinese.index('證券代號') if '證券代號' in header_chinese else header_chinese.index('代號')
                    logging.info(f"[Parser] ✓ 證券代號欄位位於位置 {code_idx}: '{header_chinese[code_idx]}'")
                else:
                    logging.warning(f"[Parser] ⚠ 無法找到證券代號欄位")
                    logging.warning(f"[Parser]   所有欄位名稱: {header_chinese}")
                
                logging.debug(f"[Parser] 原始標頭 (未處理): {row}")
                continue 

            if found_header:
                # --- 2.6 確保欄位數和資料數一致 ---
                if len(row) == len(header_chinese):
                    data_rows.append(row)
                    
                    # --- 2.6.1 從第一筆資料中提取日期（僅執行一次）---
                    if len(data_rows) == 1 and '日期' in header_chinese and not date_logged:
                        date_idx = header_chinese.index('日期')
                        date_str = row[date_idx].strip() if date_idx < len(row) else None
                        if date_str:
                            logging.info(f"[Request] 開始請求(日期: {date_str})「個股日成交資訊」CSV 資料")
                            date_logged = True
                else:
                    logging.warning(f"[Parser] 忽略格式不符的資料行 (長度 {len(row)}，應為 {len(header_chinese)}): {row}")

        if not found_header:
            logging.error(f"[Parse Error] 找不到標頭行，無法解析 CSV。")
            logging.debug(f"  > 檔案開頭 (前 500 字元): {response.text[:500]}...")
            return None

        # 轉換 (Transform) - 使用原始中文標頭建立字典
        parsed_data = [dict(zip(header_chinese, row)) for row in data_rows]

        # --- 2.6.2 計算昨收價（自建欄位：收盤價 - 漲跌價差）---
        for stock_data in parsed_data:
            try:
                # 取得收盤價和漲跌價差
                close_price_str = stock_data.get('收盤價', '').strip()
                change_str = stock_data.get('漲跌價差', '').strip()
                
                # 嘗試轉換為數值並計算昨收價
                if close_price_str and change_str and close_price_str != '--' and change_str != '--':
                    try:
                        # 移除可能的逗號分隔符（例如：1,234.56）
                        close_price = float(close_price_str.replace(',', ''))
                        change = float(change_str.replace(',', ''))
                        
                        # 計算昨收價：收盤價 - 漲跌價差
                        yesterday_close = close_price - change
                        
                        # 將結果轉回字串格式，保留小數點後兩位
                        stock_data['昨收價'] = f"{yesterday_close:.2f}"
                    except (ValueError, TypeError) as e:
                        # 如果轉換失敗，設為空值
                        logging.debug(f"[計算昨收價] 無法計算，收盤價: {close_price_str}, 漲跌價差: {change_str}, 錯誤: {e}")
                        stock_data['昨收價'] = ''
                else:
                    # 如果缺少必要欄位或值為 '--'，設為空值
                    stock_data['昨收價'] = ''
            except Exception as e:
                # 處理其他可能的錯誤
                logging.debug(f"[計算昨收價] 發生錯誤: {e}")
                stock_data['昨收價'] = ''

        # --- 2.7 如果沒有在第一筆資料中記錄日期，則嘗試從解析後的資料中提取 ---
        if not date_logged:
            if parsed_data and '日期' in parsed_data[0]:
                date_str = parsed_data[0].get('日期', '').strip()
                if date_str:
                    logging.info(f"[Request] 開始請求(日期: {date_str})「個股日成交資訊」CSV 資料")
                else:
                    logging.info(f"[Request] 開始請求「個股日成交資訊」CSV 資料")
            else:
                logging.info(f"[Request] 開始請求「個股日成交資訊」CSV 資料")

        logging.info(f"[Request] ✓ 成功解析 {len(parsed_data)} 筆 (支) 股票資料。")
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
    logging.info(f"------------------------------------------------------------------------------------------------")
    logging.info(f"------------------------------------------------------------------------------------------------")
    logging.info(f"--- 開始抓取全市場資料 ---")
    
    
    # 調用抓取全市場資料函數
    market_data_list = fetch_twse_market_day_all_csv()
    
    if market_data_list:
        # --- 4.1 如果有啟用篩選，則進行篩選 ---
        if ENABLE_FILTER:
            logging.info(f"--- 篩選證券代號: {STOCK_CODES_TO_FILTER} ---")
            market_data_list = filter_stocks_by_codes(market_data_list, STOCK_CODES_TO_FILTER)
        
        # (日誌) [結果] ...
        logging.info(f"\n[結果] 抓取成功！總共 {len(market_data_list)} 支股票。")
        
        if ENABLE_FILTER:
            logging.info(f"--- 顯示篩選後的資料 (證券代號: {STOCK_CODES_TO_FILTER}) ---")
        else:
            logging.info(f"--- 顯示全部資料 ---")
        
        # --- 4.2 按照漲跌價差排序（可選） ---
        if SORT_BY_CHANGE:
            market_data_list = sort_by_change(market_data_list, reverse=SORT_REVERSE)
        
        # --- 4.3 儲存資料到 CSV ---
        try:
            # 決定儲存路徑 (存在專案根目錄下的 'output_csv' 資料夾中)
            output_dir = get_output_dir(__file__, subdir='output_csv')
            
            save_data_to_csv(
                market_data_list, 
                output_dir, 
                filename_prefix='stock_day',
                date_field='日期'
            )
            
        except Exception as e:
            logging.error(f"[Main] 呼叫 save_data_to_csv 時發生錯誤: {e}", exc_info=True)

        
        # --- 4.4 輸出到控制台 (print) ---
        # (這部分使用 print 輸出到控制台，logging 僅用於日誌檔案)
        if market_data_list:
            print(f"\n所有欄位名稱: {list(market_data_list[0].keys())}")
            print(f"\n{'='*80}")
        if market_data_list[0].get('日期'):
            print(f"[Print] 最新日期: {market_data_list[0].get('日期')}")
        if SORT_BY_CHANGE:
            sort_direction = "遞減" if SORT_REVERSE else "遞增"
            sort_desc = "漲幅最大在前" if SORT_REVERSE else "跌幅最大在前"
            print(f"[Print] 資料已按照漲跌價差{sort_direction}排序（{sort_desc}）")
        # 輸出所有資料，排除日期欄位
        for i, stock_data in enumerate(market_data_list):
            print(f"\n第 {i+1} 筆資料:")
            # 顯示所有欄位和對應的值，但排除日期欄位
            for key, value in stock_data.items():
                if key != '日期':
                    print(f"  {key}: {value}")
        
        print(f"\n{'='*80}")
        print(f"[提示] 總共顯示 {len(market_data_list)} 筆資料。")
        if market_data_list:
            print(f"[提示] 每筆資料包含 {len(market_data_list[0])} 個欄位。")
    else:
        print("\n[結果] 抓取失敗。請檢查上方的 ERROR/WARNING 日誌。")