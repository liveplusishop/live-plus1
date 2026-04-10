# 直播加1系統 - Render.com 部署指南

## 🚀 快速部署（5分鐘完成）

### 步驟一：上傳程式碼到 GitHub

1. **去 GitHub 建立新專案**
   - 開啟 https://github.com
   - 登入後點 "New repository"
   - 名稱輸入 `live-plus1`
   - 選 Public（公開）
   - 點 "Create repository"

2. **上傳所有檔案**
   - 在新建立的 Repo 頁面，點 "uploading an existing file"
   - 把 `live-plus1` 資料夾裡**所有東西**拖進去上傳
   - 確認上傳了這些：
     - `backend/` 資料夾（含 app.py, requirements.txt）
     - `frontend/` 資料夾
     - `render.yaml`
     - `.gitignore`
   - 點 "Commit changes"

### 步驟二：部署到 Render

1. **去 Render.com 註冊**
   - 開啟 https://render.com
   - 用 GitHub 帳號登入（最簡單）

2. **建立 Web Service**
   - 點 "New +" → "Web Service"
   - 找到你的 `live-plus1` repo，點 "Connect"
   - 設定：
     - **Name**: `live-plus1`（或你喜歡的名字）
     - **Region**: Singapore（離台灣近，速度快）
     - **Branch**: main
     - **Root Directory**: （留空）
     - **Runtime**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `cd backend && python app.py`
     - **Plan**: Free

3. **設定環境變數**（在 Environment 分頁）
   - 點 "Environment Variables"
   - 加入：
     - `PYTHON_VERSION` = `3.11`

4. **點 "Create Web Service"**

5. **等它部署完成**
   - 會自動安裝依賴、啟動服務
   - 大約 1-2 分鐘
   - 看到綠色 "Live" 就是成功了！

### 步驟三：取得你的網址

部署成功後，Render 會給你一個 URL，例如：
```
https://live-plus1.onrender.com
```

這就是你的系統網址，在世界各地都能訪問！

---

## 📱 測試功能

用瀏覽器打開你的網址，測試：

1. **首頁**: `https://你的網址/`
2. **賣家後台**: `https://你的網址/dashboard.html`
3. **買家填單**: `https://你的網址/buyer.html`

---

## ⚠️ 免費版限制

Render.com 免費版：
- 閒置 15 分鐘後會休眠
- 下次訪問時需要 30 秒唤醒
- 每月有 750 小時額度

如果需要 24 小時不間斷服務，可以升級付費版（$7/月起）。

---

## 🔧 常見問題

**Q: 部署失敗了？**
A: 點進 Deploy logs 查看錯誤訊息，常見問題：
- requirements.txt 格式錯誤
- 缺少相依套件

**Q: 可以綁定自己的網域？**
A: 可以！在 Render 的 Custom Domains 設定，但需要付費版。

**Q: 資料會不見嗎？**
A: 免費版的硬碟空間有限制，建議定期匯出訂單 Excel 備份。

---

## 🎉 恭喜！

部署成功後，你的直播加1系統就可以在國外訪問了！

把網址分享給需要測試的人，或者自己先試用一遍完整流程。
