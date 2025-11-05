"""
證券代號篩選問題診斷測試腳本

此腳本用於分析為什麼證券代號篩選會失敗
主要檢查：
1. CSV 標頭的實際欄位名稱
2. 證券代號欄位的名稱和格式
3. 資料結構是否符合預期
"""

import requests
import csv
import io
import logging
import time
from typing import List, Dict, Any, Optional

# 設置日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_and_analyze_csv(date_str: str) -> Optional[Dict[str, Any]]:
    """
    抓取 CSV 並詳細分析其結構
    """
    url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?"
    params = {
        'response': 'open_data',
        'date': date_str,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    logging.info(f"[診斷] 開始抓取 {date_str} 的資料...")
    time.sleep(3)  # 減少等待時間用於測試
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        
        if "沒有符合條件的資料" in response.text:
            logging.warning("[診斷] API 回應: 沒有符合條件的資料")
            return None
        
        response.encoding = 'utf-8-sig'
        raw_text = response.text
        
        # 分析原始 CSV 內容
        csv_file_in_memory = io.StringIO(raw_text)
        reader = csv.reader(csv_file_in_memory)
        
        analysis_result = {
            'raw_text_preview': raw_text[:1000],  # 前1000字元
            'header_row': None,
            'header_row_index': None,
            'first_data_rows': [],
            'all_headers_found': [],
            'sample_stock_codes': []
        }
        
        row_index = 0
        found_header = False
        
        for row in reader:
            row_index += 1
            
            if not row:
                continue
            
            # 檢查是否是標頭行（可能有多種格式）
            first_col = row[0].strip() if row else ""
            
            # 記錄所有可能包含「日期」或「證券」的行
            if '日期' in first_col or 'Date' in first_col or '證券' in first_col or 'Code' in first_col:
                logging.info(f"[診斷] 第 {row_index} 行可能是標頭: {row}")
                analysis_result['all_headers_found'].append({
                    'row_index': row_index,
                    'content': row
                })
            
            # 尋找標頭行（根據原始程式碼的邏輯）
            if first_col == '日期':
                analysis_result['header_row'] = row
                analysis_result['header_row_index'] = row_index
                found_header = True
                
                # 標準化標頭（去除引號和空白）
                normalized_header = [h.strip().replace('"', '') for h in row]
                logging.info(f"[診斷] ✓ 找到標頭行 (第 {row_index} 行)")
                logging.info(f"[診斷]   原始標頭: {row}")
                logging.info(f"[診斷]   標準化標頭: {normalized_header}")
                
                # 特別檢查證券代號欄位
                for idx, header_name in enumerate(normalized_header):
                    if '代號' in header_name or 'Code' in header_name or 'code' in header_name.lower():
                        logging.info(f"[診斷]   → 證券代號欄位位於索引 {idx}: '{header_name}'")
                
                continue
            
            # 如果已找到標頭，收集前幾筆資料
            if found_header:
                if len(analysis_result['first_data_rows']) < 10:
                    if len(row) == len(analysis_result['header_row']):
                        analysis_result['first_data_rows'].append(row)
                        
                        # 嘗試找出證券代號欄位
                        normalized_header = [h.strip().replace('"', '') for h in analysis_result['header_row']]
                        code_idx = None
                        for idx, h in enumerate(normalized_header):
                            if '代號' in h or 'Code' in h or 'code' in h.lower():
                                code_idx = idx
                                break
                        
                        if code_idx is not None and code_idx < len(row):
                            code_value = row[code_idx].strip()
                            analysis_result['sample_stock_codes'].append(code_value)
            
            # 限制分析範圍
            if row_index > 50:
                break
        
        return analysis_result
    
    except Exception as e:
        logging.error(f"[診斷] 發生錯誤: {e}", exc_info=True)
        return None


def test_filter_function():
    """
    測試篩選函數的實際行為
    """
    # 模擬資料來測試篩選邏輯
    test_cases = [
        {
            'name': '測試案例 1: 英文欄位名稱 Code',
            'data': [
                {'Code': '0050', 'Name': '元大台灣50'},
                {'Code': '2330', 'Name': '台積電'},
                {'Code': '2317', 'Name': '鴻海'},
            ],
            'filter_codes': ['0050', '2330'],
            'expected_count': 2
        },
        {
            'name': '測試案例 2: 中文欄位名稱 證券代號',
            'data': [
                {'證券代號': '0050', '名稱': '元大台灣50'},
                {'證券代號': '2330', '名稱': '台積電'},
                {'證券代號': '2317', '名稱': '鴻海'},
            ],
            'filter_codes': ['0050', '2330'],
            'expected_count': 2
        },
        {
            'name': '測試案例 3: 欄位名稱包含空白',
            'data': [
                {' Code ': '0050', 'Name': '元大台灣50'},
                {'Code': '2330', 'Name': '台積電'},
            ],
            'filter_codes': ['0050'],
            'expected_count': 1
        },
    ]
    
    from main import filter_stocks_by_codes
    
    print("\n" + "="*60)
    print("測試篩選函數")
    print("="*60)
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print(f"  測試資料: {test_case['data']}")
        print(f"  篩選條件: {test_case['filter_codes']}")
        
        result = filter_stocks_by_codes(test_case['data'], test_case['filter_codes'])
        
        print(f"  實際結果: {len(result)} 筆")
        print(f"  預期結果: {test_case['expected_count']} 筆")
        print(f"  結果資料: {result}")
        
        if len(result) == test_case['expected_count']:
            print(f"  ✓ 測試通過")
        else:
            print(f"  ✗ 測試失敗")
            # 詳細分析
            for item in test_case['data']:
                print(f"    資料項 keys: {list(item.keys())}")
                for key in item.keys():
                    print(f"      '{key}' (去除空白後): '{key.strip()}'")


def main():
    """
    主測試流程
    """
    print("="*60)
    print("證券代號篩選問題診斷測試")
    print("="*60)
    
    # 測試日期
    test_date = '20251028'
    
    # 1. 分析 CSV 結構
    print("\n【步驟 1】分析 CSV 結構")
    print("-" * 60)
    analysis = fetch_and_analyze_csv(test_date)
    
    if analysis:
        print(f"\n原始 CSV 預覽 (前1000字元):")
        print("-" * 60)
        print(analysis['raw_text_preview'])
        print("-" * 60)
        
        if analysis['header_row']:
            print(f"\n✓ 找到標頭行 (第 {analysis['header_row_index']} 行)")
            print(f"  標頭內容: {analysis['header_row']}")
            
            # 標準化標頭
            normalized_header = [h.strip().replace('"', '') for h in analysis['header_row']]
            print(f"  標準化標頭: {normalized_header}")
            
            # 找出證券代號欄位的索引
            code_column_indices = []
            for idx, header in enumerate(normalized_header):
                if '代號' in header or 'Code' in header or header == 'Code':
                    code_column_indices.append((idx, header))
            
            print(f"\n  證券代號欄位分析:")
            if code_column_indices:
                for idx, header_name in code_column_indices:
                    print(f"    索引 {idx}: '{header_name}'")
            else:
                print(f"    ✗ 警告：找不到證券代號欄位！")
                print(f"    請檢查所有欄位名稱:")
                for idx, header in enumerate(normalized_header):
                    print(f"      索引 {idx}: '{header}'")
            
            # 顯示前幾筆資料
            print(f"\n  前 {len(analysis['first_data_rows'])} 筆資料範例:")
            for i, row in enumerate(analysis['first_data_rows'][:5]):
                print(f"    資料 {i+1}: {row}")
                
                # 如果有找到證券代號欄位，顯示該欄位的值
                if code_column_indices:
                    for idx, header_name in code_column_indices:
                        if idx < len(row):
                            code_value = row[idx]
                            print(f"      → 證券代號欄位 ('{header_name}') 的值: '{code_value}'")
            
            # 顯示樣本證券代號
            if analysis['sample_stock_codes']:
                print(f"\n  樣本證券代號 (前10個): {analysis['sample_stock_codes'][:10]}")
        
        else:
            print("\n✗ 找不到標頭行！")
            if analysis['all_headers_found']:
                print("  但找到以下可能是標頭的行:")
                for header_info in analysis['all_headers_found']:
                    print(f"    第 {header_info['row_index']} 行: {header_info['content']}")
    
    # 2. 測試篩選函數
    print("\n\n【步驟 2】測試篩選函數")
    print("-" * 60)
    test_filter_function()
    
    # 3. 實際抓取並測試篩選
    print("\n\n【步驟 3】實際抓取並測試篩選")
    print("-" * 60)
    from main import fetch_twse_market_day_all_csv, filter_stocks_by_codes
    
    actual_data = fetch_twse_market_day_all_csv(test_date)
    
    if actual_data:
        print(f"\n✓ 成功抓取 {len(actual_data)} 筆資料")
        
        if actual_data:
            print(f"\n第一筆資料的結構:")
            first_item = actual_data[0]
            print(f"  Keys: {list(first_item.keys())}")
            print(f"  完整資料: {first_item}")
            
            # 檢查 Code 欄位
            if 'Code' in first_item:
                code_value = first_item['Code']
                print(f"\n  'Code' 欄位的值: '{code_value}' (類型: {type(code_value)})")
                print(f"  去除空白後: '{str(code_value).strip()}'")
            else:
                print(f"\n  ✗ 警告：找不到 'Code' 欄位！")
                print(f"  請檢查所有 keys: {list(first_item.keys())}")
                
                # 嘗試找類似的欄位
                for key in first_item.keys():
                    if '代號' in key or 'code' in key.lower():
                        print(f"    可能的證券代號欄位: '{key}' = '{first_item[key]}'")
            
            # 測試篩選
            test_codes = ['0050', '2330', '2317']
            print(f"\n測試篩選 (證券代號: {test_codes})...")
            
            # 先顯示一些實際的證券代號
            actual_codes = [item.get('Code', 'N/A') for item in actual_data[:20]]
            print(f"實際資料中的前20個證券代號: {actual_codes}")
            
            filtered_result = filter_stocks_by_codes(actual_data, test_codes)
            print(f"\n篩選結果: {len(filtered_result)} 筆")
            
            if filtered_result:
                print("篩選出的資料:")
                for item in filtered_result:
                    print(f"  {item.get('Code', 'N/A')} - {item.get('Name', 'N/A')}")
            else:
                print("\n✗ 篩選結果為空！")
                print("\n可能的原因分析:")
                print("  1. 證券代號欄位名稱不是 'Code'")
                print("  2. 證券代號格式不符（例如有空白、引號等）")
                print("  3. 測試的證券代號不在資料中")
                
                # 詳細比對
                print("\n詳細比對:")
                for test_code in test_codes:
                    found = False
                    for item in actual_data:
                        # 嘗試多種可能的欄位名稱
                        for possible_key in ['Code', 'code', '證券代號', '代號']:
                            if possible_key in item:
                                item_code = str(item[possible_key]).strip()
                                if item_code == test_code:
                                    found = True
                                    print(f"  ✓ '{test_code}' 找到於欄位 '{possible_key}'")
                                    break
                        if found:
                            break
                    
                    if not found:
                        print(f"  ✗ '{test_code}' 未找到")
    
    print("\n" + "="*60)
    print("診斷測試完成")
    print("="*60)


if __name__ == "__main__":
    main()

