"""
日誌設置模組

提供統一的日誌配置功能，用於設置日誌記錄。
日誌僅寫入檔案，不輸出到控制台。
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(
    log_name: str,
    log_subdir: Optional[str] = None,
    level: int = logging.INFO,
    format_str: Optional[str] = None
) -> str:
    """
    設置日誌記錄器，將日誌寫入檔案。
    
    這是一個通用的日誌設置函數，可以在不同腳本中使用。
    日誌檔案會儲存在專案根目錄下的 logs 資料夾中。
    
    Args:
        log_name: 日誌檔案名稱（不含副檔名，會自動加上日期和 .log 副檔名）
        log_subdir: 日誌子資料夾名稱（例如：'csv_log'），如果為 None 則直接放在 logs 資料夾下
        level: 日誌級別，預設為 logging.INFO
        format_str: 日誌格式字串，如果為 None 則使用預設格式
    
    Returns:
        日誌檔案完整路徑
    
    Example:
        >>> from funtion.logger_config import setup_logger
        >>> log_file = setup_logger('stock_day', log_subdir='csv_log')
        >>> logging.info("這條訊息會寫入日誌檔案")
    """
    # 決定日誌檔案路徑
    # 取得當前腳本所在目錄，然後往上找到專案根目錄
    current_file = os.path.abspath(__file__)
    # funtion/logger_config.py -> funtion -> 專案根目錄
    project_root = os.path.abspath(os.path.join(os.path.dirname(current_file), '..'))
    
    # 建立日誌資料夾路徑
    if log_subdir:
        log_dir = os.path.join(project_root, 'logs', log_subdir)
    else:
        log_dir = os.path.join(project_root, 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # 建立日誌檔案名稱（加上日期）
    log_filename = f'{log_name}_{datetime.now().strftime("%Y%m%d")}.log'
    log_file = os.path.join(log_dir, log_filename)
    
    # 設定日誌格式（如果未提供則使用預設格式）
    if format_str is None:
        format_str = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    
    # 配置日誌記錄器
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.FileHandler(log_file, encoding='utf-8')],
        force=True  # 強制重新配置（如果已經配置過）
    )
    
    return log_file

