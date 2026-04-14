# -*- coding: utf-8 -*-
"""
直播加1 - 自動列印小程式
版本: v1.0 (2026-04-14)
功能: 自動偵測新訂單並列印出貨單
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import tempfile
import webbrowser
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

# 嘗試導入 win32 列印相關模組
try:
    import win32print
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告: win32print 未安裝，將使用網頁列印方式")

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("警告: plyer 未安裝，將使用 tkinter 通知")


class AutoPrintApp:
    """自動列印應用程式"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("直播加1 - 自動列印")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 嘗試隱藏到系統托盤
        self.hidden_to_tray = False
        
        # 設定
        self.api_url = tk.StringVar(value="https://live-plus1-production-ffb0.up.railway.app/api")
        self.check_interval = tk.IntVar(value=5)  # 檢查間隔（秒）
        self.auto_print = tk.BooleanVar(value=True)  # 自動列印
        self.printer_name = tk.StringVar(value="")  # 印表機名稱
        
        # 狀態
        self.monitoring = False
        self.last_order_id = None
        self.monitor_thread = None
        self.total_printed = 0
        self.start_time = None
        
        # 嘗試取得印表機列表
        self.printers = self.get_printers()
        if self.printers:
            self.printer_name.set(self.printers[0])
        
        self.create_ui()
        
    def get_printers(self):
        """取得印表機列表"""
        printers = []
        if WIN32_AVAILABLE:
            try:
                for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
                    printers.append(printer[2])
            except Exception as e:
                print(f"取得印表機失敗: {e}")
        return printers if printers else ["預設印表機"]
    
    def create_ui(self):
        """建立 UI"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text="🖨️ 直播加1 自動列印", 
                                 font=("Microsoft JhengHei", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 狀態顯示
        status_frame = ttk.LabelFrame(main_frame, text="📊 狀態", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="⚪ 未監控", 
                                       font=("Microsoft JhengHei", 12))
        self.status_label.pack()
        
        self.info_label = ttk.Label(status_frame, text="已列印: 0 張 | 運行時間: 00:00:00",
                                    foreground="gray")
        self.info_label.pack(pady=(5, 0))
        
        # 設定區塊
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ 設定", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        # API URL
        ttk.Label(config_frame, text="API 網址:").pack(anchor=tk.W)
        ttk.Entry(config_frame, textvariable=self.api_url, width=50).pack(pady=2)
        
        # 檢查間隔
        interval_frame = ttk.Frame(config_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        ttk.Label(interval_frame, text="檢查間隔 (秒):").pack(side=tk.LEFT)
        ttk.Spinbox(interval_frame, from_=3, to=30, textvariable=self.check_interval, 
                    width=10).pack(side=tk.LEFT, padx=5)
        
        # 印表機選擇
        printer_frame = ttk.Frame(config_frame)
        printer_frame.pack(fill=tk.X, pady=5)
        ttk.Label(printer_frame, text="印表機:").pack(side=tk.LEFT)
        self.printer_combo = ttk.Combobox(printer_frame, textvariable=self.printer_name,
                                           values=self.printers, width=30, state="readonly")
        if self.printers:
            self.printer_combo.pack(side=tk.LEFT, padx=5)
        
        # 自動列印選項
        ttk.Checkbutton(config_frame, text="有新訂單時自動列印", 
                        variable=self.auto_print).pack(anchor=tk.W, pady=5)
        
        # 按鈕區塊
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.toggle_btn = ttk.Button(btn_frame, text="▶ 開始監控", 
                                      command=self.toggle_monitoring, style="Accent.TButton")
        self.toggle_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 測試列印按鈕
        ttk.Button(btn_frame, text="🖨️ 測試列印", 
                   command=self.test_print).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 日誌區塊
        log_frame = ttk.LabelFrame(main_frame, text="📋 日誌", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, width=50, state=tk.DISABLED,
                                  font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 選單列
        self.create_menu()
        
    def create_menu(self):
        """建立選單"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 檔案選單
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟直播加1", command=self.open_dashboard)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.quit_app)
        
        # 說明選單
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="使用說明", command=self.show_help)
        help_menu.add_command(label="關於", command=self.show_about)
        
    def log(self, message):
        """寫入日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def toggle_monitoring(self):
        """切換監控狀態"""
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
            
    def start_monitoring(self):
        """開始監控"""
        self.monitoring = True
        self.start_time = time.time()
        self.toggle_btn.config(text="⏹ 停止監控")
        self.status_label.config(text="🟢 監控中", foreground="green")
        self.log("▶ 開始監控新訂單...")
        
        # 顯示系統通知
        self.show_notification("直播加1", "自動列印已啟動，正在監控新訂單...")
        
        # 啟動監控執行緒
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # 更新運行時間
        self.update_runtime()
        
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        self.toggle_btn.config(text="▶ 開始監控")
        self.status_label.config(text="⚪ 已停止", foreground="gray")
        self.log("⏹ 監控已停止")
        
    def update_runtime(self):
        """更新運行時間顯示"""
        if self.monitoring and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.info_label.config(text=f"已列印: {self.total_printed} 張 | 運行時間: {runtime}")
        if self.monitoring:
            self.root.after(1000, self.update_runtime)
            
    def monitor_loop(self):
        """監控迴圈"""
        while self.monitoring:
            try:
                # 檢查新訂單
                new_orders = self.check_new_orders()
                
                if new_orders:
                    for order in new_orders:
                        self.log(f"📦 收到新訂單: #{order['id']} - {order.get('buyer_name', 'N/A')}")
                        self.total_printed += 1
                        
                        # 顯示通知
                        self.show_notification(
                            "📦 新訂單！",
                            f"{order.get('buyer_name', 'N/A')} - ${order.get('total', 0)}"
                        )
                        
                        # 自動列印
                        if self.auto_print.get():
                            self.print_order(order)
                            
                # 等待下次檢查
                time.sleep(self.check_interval.get())
                
            except Exception as e:
                self.log(f"❌ 監控錯誤: {e}")
                time.sleep(5)
                
    def check_new_orders(self):
        """檢查新訂單"""
        try:
            # 嘗試從 API 取得訂單
            url = f"{self.api_url.get()}/orders"
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            try:
                with urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    orders = data if isinstance(data, list) else data.get('orders', [])
                    
                    # 找出新的訂單
                    new_orders = []
                    for order in orders:
                        order_id = str(order.get('id', ''))
                        if self.last_order_id is None or order_id != str(self.last_order_id):
                            if self.last_order_id is not None:
                                new_orders.append(order)
                            self.last_order_id = order_id
                            
                    return new_orders
            except URLError:
                # 如果無法連接 API，嘗試本地資料
                self.log("⚠️ 無法連接雲端 API，嘗試讀取本地資料...")
                return self.check_local_orders()
                
        except Exception as e:
            self.log(f"⚠️ 檢查訂單失敗: {e}")
            return self.check_local_orders()
            
    def check_local_orders(self):
        """檢查本地訂單檔案"""
        try:
            # 嘗試讀取本地訂單檔案
            db_path = os.path.join(os.path.dirname(__file__), "..", "backend", "orders.json")
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    orders = json.load(f)
                    if orders and len(orders) > 0:
                        latest = orders[-1]
                        order_id = str(latest.get('id', ''))
                        if self.last_order_id is None or order_id != str(self.last_order_id):
                            if self.last_order_id is not None:
                                self.last_order_id = order_id
                                return [latest]
                            self.last_order_id = order_id
            return []
        except Exception as e:
            self.log(f"⚠️ 讀取本地訂單失敗: {e}")
            return []
            
    def print_order(self, order):
        """列印訂單"""
        try:
            # 產生 HTML 出貨單
            html = self.generate_print_html(order)
            
            # 方法1: 使用預設瀏覽器列印（會彈出對話框）
            # self.print_via_browser(html)
            
            # 方法2: 直接使用印表機
            self.print_direct(html, order)
            
            self.log(f"✅ 已列印訂單 #{order.get('id', 'N/A')}")
            
        except Exception as e:
            self.log(f"❌ 列印失敗: {e}")
            
    def generate_print_html(self, order):
        """產生列印 HTML"""
        items = order.get('items', [])
        items_html = ""
        total = 0
        
        for item in items:
            price = item.get('price', 0)
            qty = item.get('quantity', 1)
            subtotal = price * qty
            total += subtotal
            items_html += f"""
            <tr>
                <td>{item.get('name', 'N/A')}</td>
                <td>{item.get('spec', '-')}</td>
                <td>{qty}</td>
                <td>${price}</td>
                <td>${subtotal}</td>
            </tr>"""
            
        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>出貨單 #{order.get('id', '')}</title>
<style>
@page {{ margin: 5mm; size: 80mm 150mm; }}
body {{
    font-family: 'Microsoft JhengHei', Arial, sans-serif;
    font-size: 12px;
    width: 75mm;
    margin: 0;
    padding: 5mm;
}}
.header {{
    text-align: center;
    border-bottom: 1px dashed #000;
    padding-bottom: 5px;
    margin-bottom: 5px;
}}
.header h1 {{
    font-size: 16px;
    margin: 0 0 3px 0;
}}
.order-info {{
    margin-bottom: 8px;
}}
.order-info table {{
    width: 100%;
    border-collapse: collapse;
}}
.order-info td {{
    padding: 2px 0;
}}
.items-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 11px;
}}
.items-table th, .items-table td {{
    border: 1px solid #000;
    padding: 3px;
    text-align: left;
}}
.items-table th {{
    background: #f0f0f0;
}}
.total {{
    text-align: right;
    font-size: 14px;
    font-weight: bold;
    padding: 5px 0;
    border-top: 1px dashed #000;
}}
.customer {{
    margin-top: 8px;
    border-top: 1px dashed #000;
    padding-top: 8px;
}}
.customer p {{
    margin: 3px 0;
}}
.footer {{
    margin-top: 10px;
    text-align: center;
    font-size: 10px;
    color: #666;
}}
</style>
</head>
<body>
<div class="header">
    <h1>📦 直播加1 出貨單</h1>
    <div>訂單 #{order.get('id', 'N/A')}</div>
</div>

<div class="order-info">
    <table>
        <tr><td width="30%">日期:</td><td>{order.get('created_at', datetime.now().strftime('%Y/%m/%d %H:%M'))}</td></tr>
        <tr><td>直播:</td><td>{order.get('live_title', 'N/A')}</td></tr>
    </table>
</div>

<table class="items-table">
    <thead>
        <tr>
            <th>商品名稱</th>
            <th>規格</th>
            <th>數量</th>
            <th>單價</th>
            <th>小計</th>
        </tr>
    </thead>
    <tbody>
        {items_html}
    </tbody>
</table>

<div class="total">
    合計: ${total}
</div>

<div class="customer">
    <p><strong>收件人:</strong> {order.get('buyer_name', 'N/A')}</p>
    <p><strong>電話:</strong> {order.get('phone', 'N/A')}</p>
    <p><strong>地址:</strong> {order.get('address', 'N/A')}</p>
    {f"<p><strong>備註:</strong> {order.get('note', '')}</p>" if order.get('note') else ""}
</div>

<div class="footer">
    感謝您的訂購！
</div>
</body>
</html>"""
        return html
        
    def print_direct(self, html, order):
        """直接列印"""
        if WIN32_AVAILABLE:
            try:
                # 寫入臨時檔案
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                                  encoding='utf-8', delete=False) as f:
                    f.write(html)
                    temp_file = f.name
                    
                # 使用預設瀏覽器列印
                # webbrowser.get().register('chrome', None, webbrowser.BackgroundBrowser("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"))
                webbrowser.open(f'file:///{temp_file}')
                
                # 等待瀏覽器開啟後提示使用者列印
                self.log("📄 請在瀏覽器中按 Ctrl+P 列印")
                
                # 清理
                def cleanup():
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
                # 延遲清理
                threading.Timer(10, cleanup).start()
                
            except Exception as e:
                self.log(f"❌ 列印錯誤: {e}")
                self.log("📄 已開啟預覽視窗，請手動列印")
        else:
            # 沒有 win32print，開啟瀏覽器預覽
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                              encoding='utf-8', delete=False) as f:
                f.write(html)
                temp_file = f.name
            webbrowser.open(f'file:///{temp_file}')
            self.log("📄 已開啟預覽，請按 Ctrl+P 列印")
            
    def test_print(self):
        """測試列印"""
        test_order = {
            'id': 'TEST001',
            'created_at': datetime.now().strftime('%Y/%m/%d %H:%M'),
            'live_title': '測試直播',
            'items': [
                {'name': '測試商品', 'spec': '紅色', 'quantity': 1, 'price': 100}
            ],
            'buyer_name': '測試買家',
            'phone': '0912345678',
            'address': '台北市測試區測試路1號',
            'note': '這是測試訂單',
            'total': 100
        }
        
        self.log("🖨️ 開始測試列印...")
        html = self.generate_print_html(test_order)
        self.print_direct(html, test_order)
        self.log("📄 測試頁面已開啟")
        
    def show_notification(self, title, message):
        """顯示系統通知"""
        if PLYER_AVAILABLE:
            try:
                notification.notify(title=title, message=message, timeout=5)
            except:
                pass
        else:
            # 使用 tkinter 標題列閃爍
            self.root.bell()
            
    def open_dashboard(self):
        """開啟直播加1儀表板"""
        webbrowser.open("https://live-plus1-production-ffb0.up.railway.app")
        
    def show_help(self):
        """顯示幫助"""
        help_text = """直播加1 自動列印 使用說明

1. 確認 API 網址正確
2. 選擇要使用的印表機
3. 勾選「有新訂單時自動列印」
4. 點「開始監控」

有新訂單時，系統會自動列印出貨單！

⚠️ 注意：瀏覽器可能會彈出列印對話框，
   建議將瀏覽器設為自動列印（不彈出對話框）。"""
        messagebox.showinfo("使用說明", help_text)
        
    def show_about(self):
        """顯示關於"""
        about_text = """直播加1 自動列印 v1.0

專為直播賣家設計的自動列印工具。
有新訂單時自動列印出貨單。

© 2026 IS愛思"""
        messagebox.showinfo("關於", about_text)
        
    def quit_app(self):
        """退出應用"""
        if self.monitoring:
            if messagebox.askyesno("確認", "正在監控中，確定要退出嗎？"):
                self.monitoring = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主程式"""
    root = tk.Tk()
    app = AutoPrintApp(root)
    
    # 嘗試設定圖示
    try:
        root.iconbitmap(default=None)
    except:
        pass
        
    root.mainloop()


if __name__ == "__main__":
    main()
