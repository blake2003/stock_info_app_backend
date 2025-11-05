"""
測試欄位名稱對照表的邏輯
驗證轉換是否正確運作
"""

def test_field_mapping():
    """
    測試欄位名稱對照表
    """
    # 模擬main.py中的對照表
    field_name_mapping = {
        '日期': 'Date',
        '證券代號': 'Code',
        '代號': 'Code',
        '證券名稱': 'Name',
        '名稱': 'Name',
        '成交股數': 'TradeVolume',
        '成交金額': 'TradeValue',
        '開盤價': 'Open',
        '最高價': 'High',
        '最低價': 'Low',
        '收盤價': 'Close',
        '漲跌價差': 'Change',
        '成交筆數': 'Transaction',
    }
    
    print("="*60)
    print("測試欄位名稱對照表")
    print("="*60)
    
    # 測試案例1：標準中文欄位名稱
    print("\n【測試案例 1】標準中文欄位名稱")
    print("-" * 60)
    header_chinese = ['日期', '證券代號', '證券名稱', '成交股數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '成交筆數']
    header_converted = [field_name_mapping.get(h, h) for h in header_chinese]
    
    print(f"原始標頭: {header_chinese}")
    print(f"轉換後標頭: {header_converted}")
    
    # 檢查證券代號是否正確轉換
    code_idx_original = header_chinese.index('證券代號') if '證券代號' in header_chinese else -1
    code_idx_converted = header_converted.index('Code') if 'Code' in header_converted else -1
    
    print(f"\n證券代號欄位:")
    print(f"  原始位置: {code_idx_original}")
    print(f"  轉換後位置: {code_idx_converted}")
    print(f"  轉換結果: {'✓ 正確' if code_idx_converted >= 0 and code_idx_original == code_idx_converted else '✗ 錯誤'}")
    
    # 測試案例2：可能存在的格式問題
    print("\n【測試案例 2】可能的格式問題（空白、引號）")
    print("-" * 60)
    
    # 模擬可能出現的格式問題
    test_cases = [
        ['日期', '證券代號 ', '證券名稱', '成交股數'],  # 有尾隨空白
        ['日期', '"證券代號"', '證券名稱', '成交股數'],  # 有引號
        ['日期', ' 證券代號 ', '證券名稱', '成交股數'],  # 前後空白
    ]
    
    for i, test_header in enumerate(test_cases):
        print(f"\n  測試 {i+1}: {test_header}")
        # 先標準化（去除引號和空白）
        normalized = [h.strip().replace('"', '') for h in test_header]
        print(f"    標準化後: {normalized}")
        # 再轉換
        converted = [field_name_mapping.get(h, h) for h in normalized]
        print(f"    轉換後: {converted}")
        
        if 'Code' in converted:
            print(f"    ✓ 成功轉換為 'Code'")
        else:
            print(f"    ✗ 轉換失敗，仍為原始名稱")
    
    # 測試案例3：模擬實際資料結構
    print("\n【測試案例 3】模擬實際資料結構")
    print("-" * 60)
    
    # 假設標頭已經標準化和轉換
    sample_header = ['Date', 'Code', 'Name', 'TradeVolume']
    sample_data_row = ['20251028', '0050', '元大台灣50', '1000000']
    
    # 建立字典
    data_dict = dict(zip(sample_header, sample_data_row))
    print(f"標頭: {sample_header}")
    print(f"資料: {sample_data_row}")
    print(f"字典: {data_dict}")
    
    # 測試篩選邏輯
    test_codes = ['0050', '2330']
    code_value = data_dict.get('Code', '')
    print(f"\n篩選測試:")
    print(f"  證券代號欄位值: '{code_value}'")
    print(f"  篩選條件: {test_codes}")
    print(f"  匹配結果: {'✓ 匹配' if code_value in test_codes else '✗ 不匹配'}")
    
    # 如果標頭沒有正確轉換的情況
    print("\n【測試案例 4】如果標頭未正確轉換（仍為中文）")
    print("-" * 60)
    chinese_header = ['日期', '證券代號', '證券名稱', '成交股數']
    chinese_data_row = ['20251028', '0050', '元大台灣50', '1000000']
    chinese_data_dict = dict(zip(chinese_header, chinese_data_row))
    
    print(f"標頭（中文）: {chinese_header}")
    print(f"字典: {chinese_data_dict}")
    
    # 使用自動偵測的邏輯
    possible_keys = ['Code', 'code', '證券代號', '代號']
    code_key = None
    for key in possible_keys:
        if key in chinese_data_dict:
            code_key = key
            break
    
    if code_key:
        code_value = chinese_data_dict.get(code_key, '')
        print(f"\n自動偵測結果:")
        print(f"  找到欄位: '{code_key}'")
        print(f"  證券代號值: '{code_value}'")
        print(f"  篩選條件: {test_codes}")
        print(f"  匹配結果: {'✓ 匹配' if code_value in test_codes else '✗ 不匹配'}")
    else:
        print(f"\n✗ 無法找到證券代號欄位")

if __name__ == "__main__":
    test_field_mapping()
    
    print("\n" + "="*60)
    print("問題診斷建議")
    print("="*60)
    print("""
如果實際執行時篩選失敗，可能的原因：

1. 欄位名稱對照表不完整
   - API 回傳的欄位名稱可能不在對照表中
   - 需要檢查實際 API 回傳的標頭

2. 標準化步驟有問題
   - 可能還有其他格式問題（例如全形空白等）
   - 需要更詳細的標準化邏輯

3. 欄位名稱對照表的匹配邏輯
   - 確認 field_name_mapping.get(h, h) 正確運作
   - 如果對照表中沒有，會保留原始名稱

4. 建議：
   - 在實際執行時輸出原始標頭和轉換後的標頭
   - 確認 'Code' 欄位是否存在
   - 如果沒有，檢查是否有 '證券代號' 欄位（作為備援）
    """)

