import yfinance as yf
import pandas as pd

def fetch_taiwan_stock(stock_id, period="1y"):
    """
    抓取台股歷史資料的函式
    """
    print(f"📡 正在從 Yahoo Finance 下載 {stock_id} 的歷史資料...")
    
    # 下載資料
    df = yf.download(stock_id, period=period)
    
    # 檢查資料是否為空
    if df.empty:
        print(f"❌ 找不到 {stock_id} 的資料，請檢查代碼是否正確。")
        return None
        
    print("✅ 資料下載成功！")
    return df

if __name__ == "__main__":
    # 測試抓取 0050
    target_stock = "0050.TW"
    stock_data = fetch_taiwan_stock(target_stock, period="1y")
    
    if stock_data is not None:
        # 顯示資料的前 5 筆與後 5 筆
        print("\n--- 資料預覽 (前 5 筆) ---")
        print(stock_data.head())
        
        print("\n--- 資料預覽 (後 5 筆) ---")
        print(stock_data.tail())
        
        # 顯示資料的欄位資訊
        print("\n--- 資料結構資訊 ---")
        print(stock_data.info())