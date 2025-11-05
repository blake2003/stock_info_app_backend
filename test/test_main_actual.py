"""
實際測試 main.py 的功能
檢查欄位名稱轉換和篩選是否正常運作
"""

import sys
import logging

# 設置日誌為DEBUG級別以看到詳細資訊
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from main import fetch_twse_market_day_all_csv, filter_stocks_by_codes

def test_main_functionality():
    """
    測試 main.py 的實際功能
    """
    print("="*60)
    print("實際測試 main.py 的功能")
    print("="*60)
    
    # 測試日期
    test_date = '20251028'
    test_codes = ['0050', '2330', '2317']
    
    print(f"\n【測試 1】抓取資料並檢查欄位名稱")
    print("-" * 60)
    
    # 抓取資料
    market_data = fetch_twse_market_day_all_csv(test_date)
    
    if not market_data:
        print("✗ 無法抓取資料，測試終止")
        return
    
    print(f"✓ 成功抓取 {len(market_data)} 筆資料")
    
    # 檢查第一筆資料的欄位
    if market_data:
        first_item = market_data[0]
        print(f"\n第一筆資料的欄位名稱（keys）:")
        print(f"  {list(first_item.keys())}")
        
        print(f"\n第一筆資料的完整內容:")
        for key, value in first_item.items():
            print(f"  {key}: {value}")
        
        # 特別檢查證券代號欄位
        print(f"\n證券代號欄位檢查:")
        code_found = False
        for key in ['Code', 'code', '證券代號', '代號']:
            if key in first_item:
                code_value = first_item[key]
                print(f"  ✓ 找到欄位 '{key}': '{code_value}'")
                code_found = True
                break
        
        if not code_found:
            print(f"  ✗ 找不到證券代號欄位！")
            print(f"  嘗試模糊搜尋...")
            for key in first_item.keys():
                if '代號' in key or 'code' in key.lower():
                    print(f"    可能匹配: '{key}' = '{first_item[key]}'")
        
        # 檢查前10筆資料的證券代號
        print(f"\n前10筆資料的證券代號:")
        for i, item in enumerate(market_data[:10]):
            code_value = None
            for key in ['Code', '證券代號', '代號']:
                if key in item:
                    code_value = item[key]
                    break
            if code_value:
                print(f"  {i+1}. {code_value}")
            else:
                print(f"  {i+1}. [無法找到證券代號]")
    
    print(f"\n【測試 2】測試篩選功能")
    print("-" * 60)
    print(f"篩選條件: {test_codes}")
    
    # 執行篩選
    filtered_result = filter_stocks_by_codes(market_data, test_codes)
    
    print(f"\n篩選結果: {len(filtered_result)} 筆")
    
    if filtered_result:
        print("\n✓ 篩選成功！篩選出的資料:")
        for i, item in enumerate(filtered_result):
            # 嘗試取得證券代號和名稱
            code = None
            name = None
            for key in ['Code', '證券代號', '代號']:
                if key in item:
                    code = item[key]
                    break
            for key in ['Name', '證券名稱', '名稱']:
                if key in item:
                    name = item[key]
                    break
            
            print(f"  {i+1}. {code} - {name}")
            print(f"     完整資料: {item}")
    else:
        print("\n✗ 篩選結果為空！")
        print("\n診斷資訊:")
        
        # 檢查資料中是否有這些證券代號
        print(f"\n檢查資料中是否存在這些證券代號:")
        all_codes = []
        for item in market_data:
            for key in ['Code', '證券代號', '代號']:
                if key in item:
                    all_codes.append(str(item[key]).strip())
                    break
        
        print(f"  資料中總共有 {len(set(all_codes))} 個不同的證券代號")
        print(f"  前20個證券代號: {list(set(all_codes))[:20]}")
        
        for test_code in test_codes:
            if test_code in all_codes:
                print(f"  ✓ '{test_code}' 存在於資料中")
            else:
                print(f"  ✗ '{test_code}' 不存在於資料中")
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)

if __name__ == "__main__":
    test_main_functionality()

