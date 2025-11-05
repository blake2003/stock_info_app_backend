import logging
from typing import Dict, List, Any, Optional


def filter_stocks_by_codes(
    market_data_list: List[Dict[str, Any]], 
    stock_codes: List[str]
) -> List[Dict[str, Any]]:
    """
    根據證券代號列表篩選股票資料。
    支援自動偵測證券代號欄位名稱（Code、證券代號等）。
    
    這是一個通用的篩選函數，可以在不同腳本中使用。
    支援自動偵測以下欄位名稱：
    - 中文：證券代號、代號
    - 英文：Code、code
    - 模糊匹配：包含「代號」或「code」的欄位名稱
    
    Args:
        market_data_list: 股票資料列表，每個元素為包含股票資料的字典
        stock_codes: 要篩選的證券代號列表 (例如: ['0050', '2330', '2317'])
    
    Returns:
        篩選後的股票資料列表，如果輸入為空則返回空列表或全部資料
    
    Example:
        >>> from 盤後資訊.stock_filter import filter_stocks_by_codes
        >>> data = [{'證券代號': '0050', '證券名稱': '元大台灣50', ...}, ...]
        >>> filtered = filter_stocks_by_codes(data, ['0050', '2330'])
        >>> print(f"篩選結果: {len(filtered)} 筆")
    """
    if not stock_codes:
        logging.warning("[Filter] 未提供證券代號列表，返回全部資料")
        return market_data_list
    
    if not market_data_list:
        logging.warning("[Filter] 資料列表為空")
        return []
    
    # 標準化證券代號（去除空白，轉為字串）
    normalized_codes = [str(code).strip() for code in stock_codes]
    
    # 自動偵測證券代號欄位名稱
    # 優先順序：證券代號 > 代號 > Code > code > 模糊匹配
    code_key = None
    sample_item = market_data_list[0]
    possible_keys = ['證券代號', '代號', 'Code', 'code']
    
    logging.debug(f"[Filter] 開始偵測證券代號欄位，可用 keys: {list(sample_item.keys())}")
    
    # 優先使用標準欄位名稱
    for key in possible_keys:
        if key in sample_item:
            code_key = key
            logging.debug(f"[Filter] 找到證券代號欄位: '{key}'")
            break
    
    # 如果找不到，嘗試模糊匹配
    if not code_key:
        logging.debug(f"[Filter] 標準欄位名稱未找到，嘗試模糊匹配...")
        for key in sample_item.keys():
            if '代號' in key or 'code' in key.lower():
                code_key = key
                logging.debug(f"[Filter] 透過模糊匹配找到欄位: '{key}'")
                break
    
    if not code_key:
        logging.error(f"[Filter] ✗ 無法找到證券代號欄位！")
        logging.error(f"[Filter]   可用的 keys: {list(sample_item.keys())}")
        logging.error(f"[Filter]   第一筆資料範例: {sample_item}")
        return []
    
    logging.info(f"[Filter] 使用欄位名稱 '{code_key}' 進行篩選")
    
    # 驗證欄位是否可用
    sample_code = str(sample_item.get(code_key, '')).strip()
    if not sample_code:
        logging.warning(f"[Filter] ⚠ 證券代號欄位 '{code_key}' 的值為空，可能欄位選擇錯誤")
    else:
        logging.debug(f"[Filter]   範例證券代號值: '{sample_code}'")
    
    # 執行篩選
    filtered_data = [
        stock for stock in market_data_list 
        if str(stock.get(code_key, '')).strip() in normalized_codes
    ]
    
    logging.info(f"[Filter] 從 {len(market_data_list)} 筆資料中篩選出 {len(filtered_data)} 筆符合條件的資料")
    logging.info(f"[Filter] 篩選條件: {normalized_codes}")
    
    return filtered_data


def convert_to_float(value) -> Optional[float]:
    """
    將字串轉換為浮點數，處理逗號分隔符和正負號。
    
    這是一個通用的數值轉換函數，可以在不同腳本中使用。
    
    Args:
        value: 要轉換的值（可能是字串或數字）
    
    Returns:
        轉換後的浮點數，如果轉換失敗則返回 None
    
    Example:
        >>> from funtion.stock_filter import convert_to_float
        >>> convert_to_float('123.45')
        123.45
        >>> convert_to_float('1,234.56')
        1234.56
        >>> convert_to_float('+5.00')
        5.0
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return None
    
    try:
        # 移除逗號、空白和可能的貨幣符號
        cleaned_value = str(value).strip().replace(',', '').replace(' ', '').replace('$', '').replace('NT$', '')
        
        # 處理正負號（可能包含 + 或 - 符號）
        if cleaned_value.startswith('+'):
            cleaned_value = cleaned_value[1:]
        
        if not cleaned_value or cleaned_value == '-':
            return None
        
        return float(cleaned_value)
    except (ValueError, TypeError):
        return None


def sort_by_change(market_data_list: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
    """
    按照漲跌價差對股票資料進行排序。
    
    這是一個通用的排序函數，可以在不同腳本中使用。
    
    Args:
        market_data_list: 股票資料列表
        reverse: True 表示遞減排序（從大到小），False 表示遞增排序（從小到大）
    
    Returns:
        排序後的股票資料列表
    
    Example:
        >>> from funtion.stock_filter import sort_by_change
        >>> data = [{'漲跌價差': '+5.00', ...}, {'漲跌價差': '-2.00', ...}]
        >>> sorted_data = sort_by_change(data, reverse=True)
        >>> # 漲幅最大的會排在前面
    """
    if not market_data_list:
        return market_data_list
    
    def get_change_value(stock_data: Dict[str, Any]) -> float:
        """取得漲跌價差的數值，用於排序"""
        change_str = stock_data.get('漲跌價差', '')
        change_value = convert_to_float(change_str)
        # 如果無法轉換，返回 -999999（讓它排在最後）
        return change_value if change_value is not None else -999999
    
    # 按照漲跌價差排序
    sorted_data = sorted(market_data_list, key=get_change_value, reverse=reverse)
    
    logging.info(f"[Sort] 已按照漲跌價差{'遞減' if reverse else '遞增'}排序")
    return sorted_data

