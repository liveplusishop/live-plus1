# 直播加1 - 自動列印小程式

## 📋 功能說明

全自動監控直播訂單，有新訂單時自動列印出貨單，無需手動操作。

---

## 🖥️ 系統需求

| 項目 | 需求 |
|------|------|
| 作業系統 | Windows 10 / Windows 11 |
| Python | 3.8 以上 |
| 印表機 | 任何 Windows 支援的印表機 |

---

## 📥 安裝步驟

### 步驟 1：安裝 Python

Python 是程式的執行環境，**必須先安裝**。

**下載 Python（選擇其一）：**

| 方式 | 網址 | 說明 |
|------|------|------|
| 官網下載 | https://www.python.org/downloads/windows/ | 免費官方版本 |
| Microsoft Store | 開啟 Microsoft Store 搜尋「Python」 | 最簡單，點一下就裝好 |

**⚠️ 安裝時一定要勾選：**
```
☑️ Add Python to PATH（加入路徑）
```

---

### 步驟 2：下載直播加1自動列印程式

從直播加1官網下載或聯繫客服取得：
- `auto_print.py` - 主程式
- `啟動.bat` - 啟動腳本
- `README.md` - 說明文件

**建議建立一個資料夾存放：**
```
C:\直播加1\
├── auto_print.py
├── 啟動.bat
└── README.md
```

---

### 步驟 3：首次執行

**方式一：雙擊啟動（推薦）**
1. 確保 Python 已安裝
2. 雙擊 `啟動.bat`
3. 等待自動開啟程式視窗

**方式二：命令列執行**
1. 按 Win + R，輸入 `cmd`，按 Enter
2. 輸入：
```cmd
cd C:\直播加1
python auto_print.py
```

---

## 🔧 如遇問題

### Q1：雙擊 .bat 檔案沒反應

**原因：** Python 未安裝或未加入 PATH

**解決方式：**
1. 確認已安裝 Python：開啟命令列，輸入 `python --version`
2. 如果顯示版本號，代表安裝成功
3. 重新雙擊 `啟動.bat`

### Q2：出現「找不到模組」錯誤

**解決方式：**
在命令列執行：
```cmd
pip install requests pillow
```

### Q3：印表機沒有出現

**解決方式：**
1. 確認印表機已開機
2. 確認印表機已連接電腦
3. 確認印表機已設為「預設印表機」
4. 控制台 → 裝置和印表機 → 查看

### Q4：程式視窗太小或跑版

**解決方式：**
1. 將視窗最大化
2. 或調整螢幕解析度

---

## 📌 常見錯誤訊息

| 錯誤訊息 | 原因 | 解決方式 |
|----------|------|----------|
| `'python' 不是內部或外部命令` | Python 未安裝或未加入 PATH | 重新安裝 Python，勾選 Add to PATH |
| `ModuleNotFoundError: No module named 'requests'` | 缺少套件 | 執行 `pip install requests pillow` |
| `ConnectionError` | 無法連線雲端 | 檢查網路連線 |

---

## 🔄 更新應用程式

當有新版本時：
1. 下載新版的 `auto_print.py`
2. 覆蓋舊檔案
3. 重新執行 `啟動.bat`

---

## 📞 技術支援

如遇問題請聯繫：
- LINE：@liveplus1
- Email：support@liveplus1.com

---

## 📄 授權資訊

直播加1 © 2026 | 仅供授权用户使用
