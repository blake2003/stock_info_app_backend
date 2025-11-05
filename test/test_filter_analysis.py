"""
證券代號篩選問題分析與測試

分析問題的根本原因：
1. CSV 標頭欄位名稱可能是中文「證券代號」而非英文「Code」
2. 篩選函數使用 'Code' 作為 key，但如果實際欄位是「證券代號」就會失敗
"""

from typing import Dict, List, Any


def filter_stocks_by_codes_current(
    market_data_list: List[Dict[str, Any]], 
    stock_codes: List[str]
) -> List[Dict[str, Any]]:
    """
    目前的篩選函數（從 main.py 複製）
    問題：假設欄位名稱是 'Code'，但實際可能是中文「證券代號」
    """
    if not stock_codes:
        return market_data_list
    
    normalized_codes = [str(code).strip() for code in stock_codes]
    
    filtered_data = [
        stock for stock in market_data_list 
        if str(stock.get('Code', '')).strip() in normalized_codes
    ]
    
    return filtered_data


def filter_stocks_by_codes_improved(
    market_data_list: List[Dict[str, Any]], 
    stock_codes: List[str]
) -> List[Dict[str, Any]]:
    """
    改進的篩選函數
    會自動偵測證券代號欄位的名稱（支援中文和英文）
    """
    if not stock_codes:
        return market_data_list
    
    normalized_codes = [str(code).strip() for code in stock_codes]
    
    # 自動偵測證券代號欄位名稱
    code_key = None
    if market_data_list:
        sample_item = market_data_list[0]
        # 嘗試找證券代號欄位
        for key in sample_item.keys():
            if key in ['Code', 'code', '證券代號', '代號']:
                code_key = key
                break
        
        # 如果找不到，嘗試用正則或其他方法
        if not code_key:
            for key in sample_item.keys():
                if '代號' in key or 'code' in key.lower():
                    code_key = key
                    break
    
    if not code_key:
        print(f"[警告] 無法找到證券代號欄位！可用的 keys: {list(sample_item.keys())}")
        return []
    
    print(f"[診斷] 使用欄位名稱: '{code_key}' 進行篩選")
    
    filtered_data = [
        stock for stock in market_data_list 
        if str(stock.get(code_key, '')).strip() in normalized_codes
    ]
    
    return filtered_data


def test_scenarios():
    """
    測試各種可能的情況
    """
    print("="*60)
    print("證券代號篩選問題分析測試")
    print("="*60)
    
    # 測試案例 1: 英文欄位名稱 Code（預期的情況）
    print("\n【測試案例 1】英文欄位名稱 'Code'")
    print("-" * 60)
    test_data_1 = [
        {'Code': '0050', 'Name': '元大台灣50', 'Price': '100.5'},
        {'Code': '2330', 'Name': '台積電', 'Price': '500.0'},
        {'Code': '2317', 'Name': '鴻海', 'Price': '150.2'},
        {'Code': '2412', 'Name': '中華電', 'Price': '120.0'},
    ]
    filter_codes = ['0050', '2330', '2317']
    
    print(f"測試資料: {len(test_data_1)} 筆")
    print(f"篩選條件: {filter_codes}")
    print(f"資料欄位: {list(test_data_1[0].keys())}")
    
    result_current = filter_stocks_by_codes_current(test_data_1, filter_codes)
    result_improved = filter_stocks_by_codes_improved(test_data_1, filter_codes)
    
    print(f"\n目前函數結果: {len(result_current)} 筆")
    print(f"  {result_current}")
    print(f"改進函數結果: {len(result_improved)} 筆")
    print(f"  {result_improved}")
    
    if len(result_current) == 3:
        print("  ✓ 目前函數：成功")
    else:
        print("  ✗ 目前函數：失敗")
    
    # 測試案例 2: 中文欄位名稱「證券代號」（實際可能的情況）
    print("\n【測試案例 2】中文欄位名稱 '證券代號'（可能的實際情況）")
    print("-" * 60)
    test_data_2 = [
        {'日期': '20251028', '證券代號': '0050', '證券名稱': '元大台灣50', '成交股數': '1000000'},
        {'日期': '20251028', '證券代號': '2330', '證券名稱': '台積電', '成交股數': '2000000'},
        {'日期': '20251028', '證券代號': '2317', '證券名稱': '鴻海', '成交股數': '1500000'},
        {'日期': '20251028', '證券代號': '2412', '證券名稱': '中華電', '成交股數': '800000'},
    ]
    
    print(f"測試資料: {len(test_data_2)} 筆")
    print(f"篩選條件: {filter_codes}")
    print(f"資料欄位: {list(test_data_2[0].keys())}")
    
    result_current_2 = filter_stocks_by_codes_current(test_data_2, filter_codes)
    result_improved_2 = filter_stocks_by_codes_improved(test_data_2, filter_codes)
    
    print(f"\n目前函數結果: {len(result_current_2)} 筆")
    print(f"  {result_current_2}")
    print(f"改進函數結果: {len(result_improved_2)} 筆")
    print(f"  {result_improved_2}")
    
    if len(result_current_2) == 0:
        print("  ✗ 目前函數：失敗（這就是問題所在！）")
        print("    原因：欄位名稱是 '證券代號' 而不是 'Code'")
    else:
        print("  ✓ 目前函數：成功")
    
    if len(result_improved_2) == 3:
        print("  ✓ 改進函數：成功")
    
    # 測試案例 3: 欄位名稱有空白或引號
    print("\n【測試案例 3】欄位名稱有格式問題")
    print("-" * 60)
    test_data_3 = [
        {' Code ': '0050', 'Name': '元大台灣50'},
        {'Code': '2330', 'Name': '台積電'},
        {'"Code"': '2317', 'Name': '鴻海'},
    ]
    
    print(f"測試資料: {len(test_data_3)} 筆")
    print(f"篩選條件: {filter_codes}")
    print(f"資料欄位: {[repr(k) for k in test_data_3[0].keys()]}")
    
    result_current_3 = filter_stocks_by_codes_current(test_data_3, filter_codes)
    result_improved_3 = filter_stocks_by_codes_improved(test_data_3, filter_codes)
    
    print(f"\n目前函數結果: {len(result_current_3)} 筆")
    print(f"改進函數結果: {len(result_improved_3)} 筆")
    
    # 分析問題
    print("\n" + "="*60)
    print("問題分析總結")
    print("="*60)
    print("""
根據測試結果，問題的根本原因是：

1. CSV 標頭欄位名稱可能不是英文 'Code'，而是中文 '證券代號'
2. 目前的篩選函數固定使用 'Code' 作為欄位名稱：
   stock.get('Code', '')
   
3. 如果實際資料的欄位名稱是 '證券代號'，則：
   - stock.get('Code', '') 會返回空字串 ''
   - 空字串不會匹配任何證券代號
   - 導致篩選結果為空

解決方案：
1. 在解析 CSV 時統一將中文欄位名稱轉換為英文
2. 或者在篩選函數中自動偵測欄位名稱
3. 或者在解析時建立欄位名稱對照表
    """)


def analyze_main_code():
    """
    分析 main.py 中的程式碼邏輯
    """
    print("\n" + "="*60)
    print("程式碼邏輯分析")
    print("="*60)
    
    print("""
在 main.py 中：

1. 第75行：偵測標頭行
   if row[0].strip() == '日期':
   這是正確的，因為 CSV 標頭第一欄是「日期」

2. 第79行：標準化標頭
   header = [h.strip().replace('"', '') for h in header]
   這會保留原始的中文欄位名稱（例如「證券代號」）

3. 第96行：建立字典
   parsed_data = [dict(zip(header, row)) for row in data_rows]
   這裡會使用原始的中文欄位名稱作為 key

4. 第137行：篩選函數
   if str(stock.get('Code', '')).strip() in normalized_codes:
   這裡假設欄位名稱是 'Code'，但實際可能是「證券代號」

結論：
- CSV 解析後的字典 key 是中文「證券代號」
- 但篩選函數使用英文 'Code'
- 兩者不一致導致篩選失敗
    """)


if __name__ == "__main__":
    test_scenarios()
    analyze_main_code()
    
    print("\n" + "="*60)
    print("建議的修正方案")
    print("="*60)
    print("""
方案 1（推薦）：在解析 CSV 時統一欄位名稱
   在 fetch_twse_market_day_all_csv 函數中，解析標頭後：
   - 建立欄位名稱對照表
   - 將中文欄位名稱轉換為英文
   - 例如：「證券代號」→「Code」

方案 2：改進篩選函數
   讓篩選函數自動偵測欄位名稱
   支援多種可能的欄位名稱（Code, 證券代號等）

方案 3：在解析時雙重處理
   同時保留中文和英文欄位名稱
   讓篩選函數可以使用任一種
    """)

