#!/bin/bash

# --- 自動清除日誌腳本 (Linux/macOS) ---
#
# 功能：
# 1. 取得腳本所在的絕對路徑 (專案根目錄)。
# 2. 定位到 logs 資料夾。
# 3. 刪除所有 .log 檔案。

echo "--- $(date) ---"
echo "開始清除日誌腳本..."

# 取得腳本所在的目錄 (也就是專案根目錄)
BASE_DIR=$(dirname "$(realpath "$0")")

# 定義日誌檔案路徑
LOG_DIR="$BASE_DIR/logs"

if [ -d "$LOG_DIR" ]; then
    echo "正在清除 $LOG_DIR 目錄下的 *.log 檔案..."
    # 使用 find 指令尋找並刪除 .log 檔案
    # -type f 確保只刪除檔案 (而非目錄)
    # -name "*.log" 指定要刪除的檔案名稱模式
    # -delete 執行刪除
    find "$LOG_DIR" -type f -name "*.log" -delete
    echo "清除完畢。"
else
    echo "日誌目錄 $LOG_DIR 不存在，無需清除。"
fi

echo "--- 腳本執行完畢 ---"
