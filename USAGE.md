# 使用說明

## 功能說明

此程式可以從台灣證券交易所 (TWSE) 抓取股票市場資料，並支援：
- 單一日期查詢
- 日期區間查詢
- 證券代號篩選

## 設定方式

在 `main.py` 的「篩選設定區」進行設定：

### 1. 選擇查詢模式

```python
# 方式一：單一日期查詢
USE_DATE_RANGE = False  # 設為 True 則使用日期區間查詢
DATE_TO_QUERY = '20251028'  # 單一日期 (格式: YYYYMMDD)

# 方式二：日期區間查詢
USE_DATE_RANGE = True   # 啟用日期區間查詢
START_DATE = '20251001'  # 起始日期 (格式: YYYYMMDD)
END_DATE = '20251031'    # 結束日期 (格式: YYYYMMDD)
```

### 2. 設定證券代號篩選（可選）

```python
# 選項 A：不篩選，顯示全部股票
STOCK_CODES_TO_FILTER = None

# 選項 B：篩選特定證券代號
STOCK_CODES_TO_FILTER = ['0050', '2330', '2317']  # 元大台灣50、台積電、鴻海
```

## 執行方式

### 方法一：直接執行

```bash
python3 main.py
```

### 方法二：使用虛擬環境（推薦）

```bash
# 1. 建立虛擬環境（首次執行）
python3 -m venv venv

# 2. 啟動虛擬環境
source venv/bin/activate

# 3. 安裝依賴套件
pip install requests

# 4. 執行程式
python3 main.py

# 5. 退出虛擬環境
deactivate
```

### 方法三：使用 pipx（適用於 macOS）

```bash
# 安裝 pipx（如果還沒有）
brew install pipx

# 安裝 requests 到獨立環境
pipx inject requests
```

## 日期格式說明

日期格式必須為：`YYYYMMDD`

範例：
- `20251001` → 2025年10月1日
- `20251031` → 2025年10月31日
- `20251028` → 2025年10月28日

## 使用範例

### 範例 1：查詢整個10月的全部股票資料

```python
USE_DATE_RANGE = True
START_DATE = '20251001'
END_DATE = '20251031'
STOCK_CODES_TO_FILTER = None
```

### 範例 2：查詢10月特定幾支股票

```python
USE_DATE_RANGE = True
START_DATE = '20251001'
END_DATE = '20251031'
STOCK_CODES_TO_FILTER = ['0050', '2330', '2317']
```

### 範例 3：查詢單一日期的全部股票

```python
USE_DATE_RANGE = False
DATE_TO_QUERY = '20251028'
STOCK_CODES_TO_FILTER = None
```

### 範例 4：查詢單一日期的特定股票

```python
USE_DATE_RANGE = False
DATE_TO_QUERY = '20251028'
STOCK_CODES_TO_FILTER = ['0050', '2330']
```

## 輸出結果說明

### 日期區間查詢結果

```
[結果] 日期區間查詢成功！
--- 成功抓取的日期: ['20251001', '20251002', ...] ---

[日期: 20251001] 共 3 筆資料
  1. 0050 - 元大台灣50
  2. 2330 - 台積電
  3. 2317 - 鴻海
...
```

### 單一日期查詢結果

```
[結果] 抓取成功！總共 1000 支股票。
--- 顯示篩選後的資料 (證券代號: ['0050', '2330', '2317']) ---
  第 1 筆: {'Code': '0050', 'Name': '元大台灣50', ...}
  第 2 筆: {'Code': '2330', 'Name': '台積電', ...}
  ...
```

## 注意事項

1. **API 速率限制**
   - 程式會自動在每次請求之間暫停 5 秒
   - 日期區間查詢時，總時間 = 日期數 × 5 秒
   - 例如：查詢 31 天的資料約需 31 × 5 = 155 秒（約 2.6 分鐘）

2. **非交易日**
   - 週末和國定假日無法查詢到資料
   - 程式會自動跳過非交易日
   - 只會顯示成功抓取的交易日資料

3. **日期格式**
   - 必須使用 8 位數字格式：YYYYMMDD
   - 不支援 `YYYY-MM-DD` 或 `YYYY/MM/DD` 格式

4. **證券代號格式**
   - 使用 4 位數字代號，例如：`0050`、`2330`
   - 不需要前導零（會自動處理）

5. **日誌級別**
   - 預設為 INFO 級別
   - 如需更詳細的除錯資訊，可修改日誌設定為 DEBUG

## 常見問題

### Q: 為什麼查詢結果為空？

A: 可能的原因：
1. 選擇的日期是週末或國定假日（非交易日）
2. 篩選的證券代號不在資料中
3. API 暫時無法連線

解決方法：
- 檢查日誌中的 WARNING 和 ERROR 訊息
- 確認日期是否為交易日
- 嘗試不篩選證券代號，查看是否有資料

### Q: 如何查看更詳細的除錯資訊？

A: 修改 `main.py` 中的日誌設定：

```python
logging.basicConfig(
    level=logging.DEBUG,  # 從 INFO 改為 DEBUG
    ...
)
```

### Q: 查詢日期區間很慢怎麼辦？

A: 這是正常的，因為：
1. 每個日期之間有 5 秒的延遲（尊重 API 限制）
2. 31 天的資料需要 31 次 API 請求
3. 總時間約為：日期數 × 5 秒

如果需要更快，可以：
- 減少日期區間範圍
- 只查詢週一到週五（跳過週末）

## 當前設定（已設定為10月全月）

```python
USE_DATE_RANGE = True
START_DATE = '20251001'  # 10月1日
END_DATE = '20251031'    # 10月31日
STOCK_CODES_TO_FILTER = None  # 顯示全部股票
```

執行方式：
```bash
python3 main.py
```

