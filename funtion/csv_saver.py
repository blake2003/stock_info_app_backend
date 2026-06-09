"""
CSV 儲存模組

提供統一的 CSV 資料儲存功能，用於將股票資料儲存為 CSV 檔案。
"""

import csv
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def save_data_to_csv(
    data_list: List[Dict[str, Any]], 
    output_dir: str,
    filename_prefix: str = "stock_data",
    date_field: str = "日期"
) -> Optional[str]:
    """
    將處理過的資料儲存為 CSV 檔案。
    
    這是一個通用的 CSV 儲存函數，可以在不同腳本中使用。
    檔案將儲存在指定的 output_dir 中，並根據資料中的日期或當前日期命名。
    
    Args:
        data_list: 要儲存的資料列表，每個元素為包含資料的字典
        output_dir: 輸出資料夾路徑
        filename_prefix: 檔案名稱前綴，預設為 "stock_data"
        date_field: 日期欄位名稱，預設為 "日期"
    
    Returns:
        成功時返回檔案完整路徑，失敗時返回 None
    
    Example:
        >>> from funtion.csv_saver import save_data_to_csv
        >>> data = [{'日期': '113/11/08', '證券代號': '2330', ...}, ...]
        >>> filepath = save_data_to_csv(data, 'output_csv', filename_prefix='stock_day')
        >>> print(f"資料已儲存至: {filepath}")
    """
    if not data_list:
        logging.warning("[CSV Save] 沒有資料可儲存。")
        return None

    try:
        # --- 決定檔案名稱 ---
        # 嘗試從資料中獲取日期
        date_str = data_list[0].get(date_field, '').strip() if data_list else None
        if date_str:
            # 轉換民國年 (e.g., 113/11/08) 為西元年 (e.g., 2024-11-08)
            try:
                parts = date_str.split('/')
                roc_year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                year = roc_year + 1911
                file_date_str = f"{year}-{month:02d}-{day:02d}"
            except Exception:
                # 如果日期格式解析失敗，退回使用今天的日期
                logging.warning(f"[CSV Save] 無法解析資料日期 '{date_str}'，將使用今天日期命名。")
                file_date_str = datetime.now().strftime('%Y-%m-%d')
        else:
            # 如果沒有日期欄位，使用今天的日期
            logging.warning(f"[CSV Save] 資料中無日期欄位 '{date_field}'，將使用今天日期命名。")
            file_date_str = datetime.now().strftime('%Y-%m-%d')

        filename = f"{filename_prefix}_{file_date_str}.csv"
        
        # --- 建立資料夾並組合路徑 ---
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        # --- 寫入 CSV ---
        # 取得所有欄位名稱 (以第一筆資料為準)
        headers = list(data_list[0].keys())
        
        logging.info(f"[CSV Save] 準備寫入資料至: {filepath}")
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            # 使用 DictWriter 寫入字典列表
            writer = csv.DictWriter(f, fieldnames=headers)
            
            # 寫入標頭
            writer.writeheader()
            
            # 寫入所有資料
            writer.writerows(data_list)

        logging.info(f"[CSV Save] ✓ 成功將 {len(data_list)} 筆資料儲存至 {filepath}")
        return filepath

    except csv.Error as csv_err:
        logging.error(f"[CSV Save Error] 寫入 CSV 失敗: {csv_err}")
        return None
    except IOError as io_err:
        logging.error(f"[CSV Save Error] 檔案寫入錯誤: {io_err}")
        return None
    except Exception as e:
        logging.error(f"[CSV Save Error] 儲存 CSV 時發生未預期錯誤: {e}", exc_info=True)
        return None


def get_output_dir(script_file: str, subdir: str = "output_csv") -> str:
    """
    根據腳本檔案路徑，取得輸出資料夾路徑。
    
    這是一個輔助函數，用於自動計算輸出資料夾路徑。
    輸出資料夾會建立在專案根目錄下。
    
    Args:
        script_file: 當前腳本檔案的 __file__ 路徑
        subdir: 輸出子資料夾名稱，預設為 "output_csv"
    
    Returns:
        輸出資料夾完整路徑
    
    Example:
        >>> from funtion.csv_saver import get_output_dir
        >>> output_dir = get_output_dir(__file__)
        >>> save_data_to_csv(data, output_dir)
    """
    script_dir = os.path.dirname(script_file)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    output_dir = os.path.join(project_root, subdir)
    return output_dir

