import requests
import certifi
import ssl
import sys
import os

print("--- Python SSL 環境診斷---")
print(f"Python 可執行檔路徑: {sys.executable}")
print("-" * 30)

# --- 1. 檢查版本 ---
print(f"Requests 版本: {requests.__version__}")
print(f"Certifi 版本: {certifi.__version__}")
print(f"SSL (OpenSSL) 版本: {ssl.OPENSSL_VERSION}")
print("-" * 30)

# --- 2. 檢查 Certifi 路徑 ---
certifi_path = certifi.where()
print(f"Certifi 憑證庫 (CA Bundle) 路徑:\n  {certifi_path}")

# --- 3. 檢查 Requests 使用的路徑 ---
# 這是 requests 預設會去找的路徑
requests_ca_path = requests.utils.DEFAULT_CA_BUNDLE_PATH
print(f"\nRequests 預設使用的 CA Bundle 路徑:\n  {requests_ca_path}")
print(f"  > Requests 是否使用 Certifi? {certifi_path == requests_ca_path}")
print("-" * 30)

# --- 4. 檢查環境變數 (這很重要！) ---
# 環境變數會 *覆蓋* 所有預設值
ssl_cert_file = os.environ.get('SSL_CERT_FILE')
ssl_cert_dir = os.environ.get('SSL_CERT_DIR')
print(f"環境變數 $SSL_CERT_FILE: {ssl_cert_file if ssl_cert_file else '未設置'}")
print(f"環境變數 $SSL_CERT_DIR: {ssl_cert_dir if ssl_cert_dir else '未設置'}")
print("-" * 30)

# --- 5. 實際連線測試 ---
print("正在測試連線...")
try:
    requests.get('https://www.google.com', timeout=5)
    print("  [✓] 成功連線到 Google.com (SSL 驗證成功)")
except Exception as e:
    print(f"  [X] 連線到 Google.com 失敗:\n      {e}")

try:
    requests.get('https://www.twse.com.tw', timeout=5)
    print("  [✓] 成功連線到 TWSE.com.tw (SSL 驗證成功)")
except Exception as e:
    print(f"  [X] 連線到 TWSE.com.tw 失敗:\n      {e}")

print("--- 診斷完畢 ---")