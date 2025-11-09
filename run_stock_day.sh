#!/bin/bash

# --- 自動排程啟動腳本 (Linux/macOS) ---
#
# 功能：
# 1. 取得腳本所在的絕對路徑 (專案根目錄)。
# 2. 設定日誌檔路徑 (logs/stock_day_YYYY-MM-DD.log)。
# 3. 進入專案根目錄 (確保相對路徑導入正確)。
# 4. 啟動 .venv 虛擬環境。
# 5. 執行 stock_day.py 腳本。
# 6. 將所有執行訊息 (stdout) 和錯誤訊息 (stderr) 附加到日誌檔。

# 取得腳本所在的目錄 (也就是專案根目錄)
# (使用 realpath 確保解析了軟連結)
BASE_DIR=$(dirname "$(realpath "$0")")

# 定義日誌檔案路徑 (範例：放在專案根目錄下的 logs 資料夾)
LOG_DIR="$BASE_DIR/logs/sh_log"
LOG_FILE="$LOG_DIR/stock_day_$(date +%Y-%m-%d).log" # 每天產生一個新的日誌檔

# 確保 logs 資料夾存在
mkdir -p "$LOG_DIR"

# 變更工作目錄到專案根目錄 (這很重要，因為 stock_day.py 用了相對路徑導入 funtion)
cd "$BASE_DIR" || {
    echo "--- $(date) ---" >> "$LOG_FILE"
    echo "錯誤：無法切換到目錄 $BASE_DIR" >> "$LOG_FILE" 2>&1
    exit 1
}

# 啟動虛擬環境
source "$BASE_DIR/.venv/bin/activate"

# 執行 Python 腳本，並將標準輸出 (stdout) 和標準錯誤 (stderr) 都附加到日誌檔
# ">>" 代表附加內容，"2>&1" 代表將 stderr 導向到 stdout
echo "--- $(date) ---" >> "$LOG_FILE"
python3 "$BASE_DIR/盤後資訊/stock_day.py" >> "$LOG_FILE" 2>&1
echo "--- 執行完畢 ---" >> "$LOG_FILE"

# 停用虛擬環境 (可選)
#deactivate