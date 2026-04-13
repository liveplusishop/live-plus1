# 直播加1系統 - Windows 伺服器安裝指南

## 系統需求

- Windows Server 2012 / 2016 / 2019 / 2022
- Python 3.8 或以上
- IIS 網頁伺服器（可選）
- 對外 port 5000（後端 API）

---

## 第一步：確認 Python 安裝

在伺服器上開啟 PowerShell，執行：

```
python --version
```

如果出現「找不到命令」，表示沒有 Python，請 MIS 安裝：
- 下載 Python：https://www.python.org/downloads/
- 安裝時勾選「Add Python to PATH」

---

## 第二步：上傳檔案

將 `live-plus1` 資料夾完整上傳到伺服器，例如：
```
C:\inetpub\live-plus1
```

---

## 第三步：安裝相依套件

在 PowerShell 中執行：

```
cd C:\inetpub\live-plus1
pip install -r requirements.txt
```

---

## 第四步：設定環境變數

在 PowerShell 中執行：

```
$env:FLASK_ENV = "production"
$env:FLASK_APP = "backend/app.py"
```

或者建立一個 `start.bat` 檔案：

```batch
@echo off
cd /d C:\inetpub\live-plus1
set FLASK_ENV=production
set FLASK_APP=backend/app.py
python -m flask run --host=0.0.0.0 --port=5000
```

---

## 第五步：測試執行

執行：
```
python -m flask run --host=0.0.0.0 --port=5000
```

用瀏覽器開啟 `http://伺服器IP:5000`，應該能看到登入頁面。

---

## 第六步：設定 IIS 反向代理（可選）

如果要用網域 + 80/443 port 訪問：

1. 安裝 IIS URL Rewrite 模組
2. 安裝 ARR (Application Request Routing)
3. 設定反向代理將流量轉到 port 5000

---

## 第七步：常見問題

**Q: 找不到 flask 命令**
A: 執行 `pip install flask` 安裝

**Q: Port 5000 被佔用**
A: 改用其他 port，如 `--port=5001`

**Q: 資料庫無法寫入**
A: 確認 `data/` 資料夾有寫入權限

---

## 需要問 MIS 的問題

1. 伺服器是 Windows Server 哪個版本？
2. 有沒有安裝 Python？如果沒有，需要安裝 Python 3.8+
3. 對外要開放哪個 port？（建議 5000 或 8080）
4. 要綁定哪個網域？
5. 防火牆規則是否允許外部存取？

---

## 聯絡技術支援

如有任何問題，請聯繫系統開發者。
