"""
直播加1系統 - 主後端
IS愛思 / 小龍蝦AI
"""

import os, json, uuid, datetime, sqlite3, threading, time, re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Render 健康檢查
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'liveplus1.db')

# ========== 資料庫初始化 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # 賣家帳號
    c.execute('''CREATE TABLE IF NOT EXISTS sellers (
        id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        plan TEXT DEFAULT 'free',
        fb_page_id TEXT,
        fb_access_token TEXT,
        created_at TEXT
    )''')

    # 商品
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        seller_id TEXT,
        name TEXT,
        code TEXT,
        price INTEGER,
        stock INTEGER DEFAULT 0,
        specs TEXT,
        created_at TEXT,
        FOREIGN KEY (seller_id) REFERENCES sellers(id)
    )''')

    # 直播/貼文
    c.execute('''CREATE TABLE IF NOT EXISTS streams (
        id TEXT PRIMARY KEY,
        seller_id TEXT,
        fb_post_id TEXT,
        title TEXT,
        keywords TEXT,
        status TEXT DEFAULT 'active',
        start_time TEXT,
        end_time TEXT,
        created_at TEXT,
        FOREIGN KEY (seller_id) REFERENCES sellers(id)
    )''')

    # 訂單
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        seller_id TEXT,
        stream_id TEXT,
        product_id TEXT,
        buyer_name TEXT,
        buyer_phone TEXT,
        buyer_address TEXT,
        quantity INTEGER DEFAULT 1,
        unit_price INTEGER,
        total_price INTEGER,
        status TEXT DEFAULT 'pending',
        fb_user_id TEXT,
        fb_user_name TEXT,
        fb_comment_id TEXT,
        note TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (seller_id) REFERENCES sellers(id)
    )''')

    # 買家黑名單
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        id TEXT PRIMARY KEY,
        seller_id TEXT,
        fb_user_id TEXT,
        reason TEXT,
        created_at TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ========== 工具函式 ==========
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row) if row else None

def gen_id():
    return uuid.uuid4().hex[:12].upper()

def now_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_plan_limits(plan):
    """取得方案限制"""
    if plan == 'premium':
        return {'max_pages': 999, 'max_orders': 999999, 'max_products': 999999, 'max_keywords': 5, 'analytics': True, 'blacklist': True, 'auto_remind': True}
    else:  # free
        return {'max_pages': 1, 'max_orders': 50, 'max_products': 10, 'max_keywords': 1, 'analytics': False, 'blacklist': False, 'auto_remind': False}

# ========== 認證 ==========
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    if not email or not password or not name:
        return jsonify({'error': '請填寫所有欄位'}), 400

    conn = get_db()
    c = conn.cursor()
    existing = c.execute('SELECT id FROM sellers WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': '此信箱已註冊'}), 400

    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    seller_id = gen_id()
    c.execute('''INSERT INTO sellers (id, name, email, password_hash, plan, created_at)
                 VALUES (?, ?, ?, ?, 'free', ?)''', (seller_id, name, email, pwd_hash, now_str()))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'seller_id': seller_id, 'name': name, 'plan': 'free'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    c = conn.cursor()
    seller = c.execute('SELECT * FROM sellers WHERE email = ? AND password_hash = ?', (email, pwd_hash)).fetchone()
    conn.close()

    if not seller:
        return jsonify({'error': '信箱或密碼錯誤'}), 401

    return jsonify({
        'success': True,
        'seller_id': seller['id'],
        'name': seller['name'],
        'email': seller['email'],
        'plan': seller['plan'],
        'fb_page_id': seller['fb_page_id'] or '',
        'fb_access_token': seller['fb_access_token'] or ''
    })

# ========== 方案升級 ==========
@app.route('/api/subscription/upgrade', methods=['POST'])
def upgrade_plan():
    data = request.json
    seller_id = data.get('seller_id')

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE sellers SET plan = 'premium' WHERE id = ?", (seller_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'plan': 'premium'})

# ========== FB 授權設定 ==========
@app.route('/api/fb/set-token', methods=['POST'])
def set_fb_token():
    data = request.json
    seller_id = data.get('seller_id')
    page_id = data.get('fb_page_id', '').strip()
    access_token = data.get('fb_access_token', '').strip()

    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE sellers SET fb_page_id = ?, fb_access_token = ? WHERE id = ?',
             (page_id, access_token, seller_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 商品管理 ==========
@app.route('/api/products', methods=['GET'])
def list_products():
    seller_id = request.args.get('seller_id')
    conn = get_db()
    c = conn.cursor()

    # 檢查方案限制
    seller = c.execute('SELECT plan FROM sellers WHERE id = ?', (seller_id,)).fetchone()
    limits = get_plan_limits(seller['plan'] if seller else 'free')

    products = c.execute('SELECT * FROM products WHERE seller_id = ? ORDER BY created_at DESC', (seller_id,)).fetchall()
    conn.close()

    return jsonify({
        'products': [row_to_dict(p) for p in products],
        'limits': limits,
        'product_count': len(products)
    })

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    seller_id = data.get('seller_id')
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    price = int(data.get('price', 0))
    stock = int(data.get('stock', 0))
    specs = data.get('specs', '')

    if not name or price <= 0:
        return jsonify({'error': '商品名稱和價格必填'}), 400

    conn = get_db()
    c = conn.cursor()

    # 檢查商品數量限制
    seller = c.execute('SELECT plan FROM sellers WHERE id = ?', (seller_id,)).fetchone()
    limits = get_plan_limits(seller['plan'] if seller else 'free')
    count = c.execute('SELECT COUNT(*) FROM products WHERE seller_id = ?', (seller_id,)).fetchone()[0]
    if count >= limits['max_products']:
        conn.close()
        return jsonify({'error': f'免費版最多{limits["max_products"]}個商品，請升級進階版'}), 403

    product_id = gen_id()
    c.execute('''INSERT INTO products (id, seller_id, name, code, price, stock, specs, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (product_id, seller_id, name, code, price, stock, specs, now_str()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'product_id': product_id})

@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE products SET name=?, code=?, price=?, stock=?, specs=? WHERE id=?''',
              (data['name'], data['code'], data['price'], data['stock'], data['specs'], product_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 直播/貼文管理 ==========
@app.route('/api/streams', methods=['GET'])
def list_streams():
    seller_id = request.args.get('seller_id')
    conn = get_db()
    c = conn.cursor()
    streams = c.execute('SELECT * FROM streams WHERE seller_id = ? ORDER BY created_at DESC', (seller_id,)).fetchall()
    conn.close()
    return jsonify({'streams': [row_to_dict(s) for s in streams]})

@app.route('/api/streams', methods=['POST'])
def create_stream():
    data = request.json
    seller_id = data.get('seller_id')
    title = data.get('title', '').strip()
    fb_post_id = data.get('fb_post_id', '').strip()
    keywords_str = data.get('keywords', '+1').strip()

    if not title:
        return jsonify({'error': '請填寫直播標題'}), 400

    conn = get_db()
    c = conn.cursor()

    # 檢查直播數量限制
    seller = c.execute('SELECT plan FROM sellers WHERE id = ?', (seller_id,)).fetchone()
    limits = get_plan_limits(seller['plan'] if seller else 'free')
    count = c.execute('SELECT COUNT(*) FROM streams WHERE seller_id = ? AND status = ?', (seller_id, 'active')).fetchone()[0]
    if count >= limits['max_streams'] if 'max_streams' in limits else True:
        pass  # 暫時不限制

    stream_id = gen_id()
    c.execute('''INSERT INTO streams (id, seller_id, fb_post_id, title, keywords, status, start_time, created_at)
                 VALUES (?, ?, ?, ?, ?, 'active', ?, ?)''',
              (stream_id, seller_id, fb_post_id, title, keywords_str, now_str(), now_str()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'stream_id': stream_id})

@app.route('/api/streams/<stream_id>/end', methods=['POST'])
def end_stream(stream_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE streams SET status='ended', end_time=? WHERE id=?", (now_str(), stream_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/streams/<stream_id>', methods=['DELETE'])
def delete_stream(stream_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM streams WHERE id = ?', (stream_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 訂單管理 ==========
@app.route('/api/orders', methods=['GET'])
def list_orders():
    seller_id = request.args.get('seller_id')
    status = request.args.get('status', '')
    stream_id = request.args.get('stream_id', '')

    conn = get_db()
    c = conn.cursor()
    query = 'SELECT * FROM orders WHERE seller_id = ?'
    params = [seller_id]
    if status:
        query += ' AND status = ?'
        params.append(status)
    if stream_id:
        query += ' AND stream_id = ?'
        params.append(stream_id)
    query += ' ORDER BY created_at DESC'
    orders = c.execute(query, params).fetchall()
    conn.close()
    return jsonify({'orders': [row_to_dict(o) for o in orders]})

@app.route('/api/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE orders SET status=?, buyer_name=?, buyer_phone=?, buyer_address=?, note=?, updated_at=? WHERE id=?''',
              (data['status'], data.get('buyer_name'), data.get('buyer_phone'),
               data.get('buyer_address'), data.get('note'), now_str(), order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 買家填單 ==========
@app.route('/api/buyer/submit', methods=['POST'])
def buyer_submit():
    """買家填寫收件資料"""
    data = request.json
    order_id = data.get('order_id', '').strip()
    buyer_name = data.get('buyer_name', '').strip()
    buyer_phone = data.get('buyer_phone', '').strip()
    buyer_address = data.get('buyer_address', '').strip()
    note = data.get('note', '').strip()

    if not buyer_name or not buyer_phone or not buyer_address:
        return jsonify({'error': '請填寫完整收件資料'}), 400

    conn = get_db()
    c = conn.cursor()
    order = c.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'error': '找不到訂單'}), 404

    c.execute('''UPDATE orders SET buyer_name=?, buyer_phone=?, buyer_address=?, note=?, updated_at=? WHERE id=?''',
              (buyer_name, buyer_phone, buyer_address, note, now_str(), order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/buyer/order/<order_id>', methods=['GET'])
def buyer_get_order(order_id):
    conn = get_db()
    c = conn.cursor()
    order = c.execute('''SELECT o.*, p.name as product_name FROM orders o
                         LEFT JOIN products p ON o.product_id = p.id
                         WHERE o.id = ?''', (order_id,)).fetchone()
    conn.close()
    if not order:
        return jsonify({'error': '找不到訂單'}), 404
    return jsonify({'order': row_to_dict(order)})

# ========== 從 FB 抓留言並自動建立訂單 ==========
@app.route('/api/streams/<stream_id>/fetch-comments', methods=['POST'])
def fetch_comments(stream_id):
    """手動觸發抓取 FB 留言"""
    data = request.json
    seller_id = data.get('seller_id')
    fb_access_token = data.get('fb_access_token', '')

    if not fb_access_token:
        # 從資料庫取
        conn = get_db()
        c = conn.cursor()
        seller = c.execute('SELECT fb_access_token FROM sellers WHERE id = ?', (seller_id,)).fetchone()
        conn.close()
        if not seller or not seller['fb_access_token']:
            return jsonify({'error': '請先設定 Facebook 授權'}), 400
        fb_access_token = seller['fb_access_token']

    conn = get_db()
    c = conn.cursor()
    stream = c.execute('SELECT * FROM streams WHERE id = ?', (stream_id,)).fetchone()
    if not stream:
        conn.close()
        return jsonify({'error': '找不到直播'}), 404

    keywords = stream['keywords'].split(',') if stream['keywords'] else ['+1']
    keywords = [k.strip() for k in keywords]
    conn.close()

    # 調用 Facebook Graph API
    import requests
    fb_post_id = stream['fb_post_id']

    try:
        # 取得留言
        url = f'https://graph.facebook.com/v18.0/{fb_post_id}/comments'
        params = {
            'access_token': fb_access_token,
            'fields': 'id,message,from{id,name},created_time',
            'limit': 100
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        fb_data = resp.json()

        new_orders = 0
        for comment in fb_data.get('data', []):
            msg = comment.get('message', '')
            uid = comment.get('from', {}).get('id', '')
            uname = comment.get('from', {}).get('name', '')

            # 檢查關鍵字
            matched_keyword = None
            for kw in keywords:
                if kw in msg:
                    matched_keyword = kw
                    break

            if not matched_keyword:
                continue

            # 查商品（用關鍵字對應商品code）
            conn = get_db()
            c = conn.cursor()
            product = c.execute(
                'SELECT * FROM products WHERE seller_id = ? AND code = ? LIMIT 1',
                (seller_id, matched_keyword)
            ).fetchone()

            if not product:
                # 用第一個商品
                product = c.execute(
                    'SELECT * FROM products WHERE seller_id = ? LIMIT 1',
                    (seller_id,)
                ).fetchone()

            if not product:
                conn.close()
                continue

            # 檢查是否已存在（防重複）
            existing = c.execute(
                'SELECT id FROM orders WHERE seller_id=? AND fb_comment_id=?',
                (seller_id, comment['id'])
            ).fetchone()
            if existing:
                conn.close()
                continue

            # 數量解析
            qty = 1
            qty_match = re.search(r'[\d]+', msg)
            if qty_match:
                qty = int(qty_match.group())

            # 建立訂單
            order_id = gen_id()
            total = product['price'] * qty
            c.execute('''INSERT INTO orders
                (id, seller_id, stream_id, product_id, buyer_name, quantity, unit_price, total_price, status,
                 fb_user_id, fb_user_name, fb_comment_id, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (order_id, seller_id, stream_id, product['id'], uname, qty,
                 product['price'], total, 'pending', uid, uname, comment['id'],
                 now_str(), now_str()))
            conn.commit()
            conn.close()
            new_orders += 1

        return jsonify({'success': True, 'new_orders': new_orders, 'total_fetched': len(fb_data.get('data', []))})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== 黑名單 ==========
@app.route('/api/blacklist', methods=['GET'])
def list_blacklist():
    seller_id = request.args.get('seller_id')
    conn = get_db()
    c = conn.cursor()
    items = c.execute('SELECT * FROM blacklist WHERE seller_id = ? ORDER BY created_at DESC', (seller_id,)).fetchall()
    conn.close()
    return jsonify({'blacklist': [row_to_dict(b) for b in items]})

@app.route('/api/blacklist', methods=['POST'])
def add_blacklist():
    data = request.json
    seller_id = data.get('seller_id')
    fb_user_id = data.get('fb_user_id')
    reason = data.get('reason', '')

    conn = get_db()
    c = conn.cursor()
    bid = gen_id()
    c.execute('INSERT INTO blacklist (id, seller_id, fb_user_id, reason, created_at) VALUES (?,?,?,?,?)',
              (bid, seller_id, fb_user_id, reason, now_str()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': bid})

@app.route('/api/blacklist/<bid>', methods=['DELETE'])
def remove_blacklist(bid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM blacklist WHERE id = ?', (bid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 數據統計 ==========
@app.route('/api/stats', methods=['GET'])
def get_stats():
    seller_id = request.args.get('seller_id')

    conn = get_db()
    c = conn.cursor()

    total_orders = c.execute('SELECT COUNT(*) FROM orders WHERE seller_id = ?', (seller_id,)).fetchone()[0]
    pending = c.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='pending'", (seller_id,)).fetchone()[0]
    paid = c.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='paid'", (seller_id,)).fetchone()[0]
    shipped = c.execute("SELECT COUNT(*) FROM orders WHERE seller_id=? AND status='shipped'", (seller_id,)).fetchone()[0]
    total_revenue = c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE seller_id=? AND status IN ('paid','shipped','completed')", (seller_id,)).fetchone()[0]

    # 熱銷商品
    top_products = c.execute('''SELECT p.name, SUM(o.quantity) as total_qty, SUM(o.total_price) as total_sales
        FROM orders o JOIN products p ON o.product_id = p.id
        WHERE o.seller_id = ? AND o.status != 'cancelled'
        GROUP BY p.id ORDER BY total_qty DESC LIMIT 5''', (seller_id,)).fetchall()

    # 每日訂單趨勢（近7天）
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    daily = c.execute('''SELECT DATE(created_at) as day, COUNT(*) as cnt, SUM(total_price) as revenue
        FROM orders WHERE seller_id=? AND DATE(created_at) >= ? GROUP BY day ORDER BY day''',
        (seller_id, seven_days_ago)).fetchall()

    conn.close()
    return jsonify({
        'total_orders': total_orders,
        'pending': pending,
        'paid': paid,
        'shipped': shipped,
        'total_revenue': total_revenue,
        'top_products': [row_to_dict(p) for p in top_products],
        'daily': [row_to_dict(d) for d in daily]
    })

# ========== Excel 匯出 ==========
@app.route('/api/orders/export', methods=['GET'])
def export_orders():
    seller_id = request.args.get('seller_id')
    stream_id = request.args.get('stream_id', '')

    import csv, io
    conn = get_db()
    c = conn.cursor()
    query = '''SELECT o.id, o.buyer_name, o.buyer_phone, o.buyer_address, o.quantity,
                      o.unit_price, o.total_price, o.status, o.note, p.name as product_name, o.created_at
               FROM orders o LEFT JOIN products p ON o.product_id = p.id WHERE o.seller_id = ?'''
    params = [seller_id]
    if stream_id:
        query += ' AND o.stream_id = ?'
        params.append(stream_id)
    query += ' ORDER BY o.created_at DESC'
    orders = c.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['訂單編號', '買家姓名', '電話', '收件地址', '商品名', '數量', '單價', '總價', '狀態', '備註', '時間'])
    for o in orders:
        writer.writerow([o['id'], o['buyer_name'], o['buyer_phone'], o['buyer_address'],
                         o['product_name'], o['quantity'], o['unit_price'], o['total_price'],
                         o['status'], o['note'], o['created_at']])

    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv; charset=utf-8-sig',
        'Content-Disposition': f'attachment; filename=orders_{datetime.date.today()}.csv'
    }

# ========== 買家端頁面 ==========
@app.route('/buyer/<order_id>')
def buyer_page(order_id):
    return send_from_directory('../frontend', 'buyer.html')

# ========== 前端靜態頁面 ==========
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    print('🚀 直播加1系統啟動中... http://localhost:5050')
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False)
