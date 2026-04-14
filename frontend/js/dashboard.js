// 直播加1 - 賣家後台 JavaScript
const API = window.location.origin + '/api';

let currentUser = null;
let currentPlan = 'free';

// ========== 認證 ==========
function showAuth(tab) {
  document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
  document.querySelectorAll('.auth-tab').forEach((t, i) => t.classList.toggle('active', (tab === 'login' && i === 0) || (tab === 'register' && i === 1)));
  document.getElementById('authError').textContent = '';
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) return showErr('請填寫信箱和密碼');

  const btn = document.querySelector('#loginForm .btn-primary');
  btn.disabled = true;
  btn.textContent = '登入中...';
  document.getElementById('authError').textContent = '';

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = '登入';
    if (!data.success) return showErr(data.error);

    currentUser = data;
    currentPlan = data.plan;
    localStorage.setItem('liveplus_user', JSON.stringify(data));
    showDashboard();
  } catch(e) {
    btn.disabled = false;
    btn.textContent = '登入';
    showErr('網路錯誤，請稍後再試');
  }
}

async function doRegister() {
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  if (!name || !email || !password) return showErr('請填寫所有欄位');

  const btn = document.getElementById('regBtn');
  btn.disabled = true;
  btn.textContent = '註冊中...';
  document.getElementById('authError').textContent = '';

  try {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, email, password})
    });
    const data = await res.json();
    if (!data.success) {
      btn.disabled = false;
      btn.textContent = '註冊';
      return showErr(data.error);
    }

    // 註冊成功，自動登入
    currentUser = data;
    currentPlan = data.plan;
    localStorage.setItem('liveplus_user', JSON.stringify(data));
    showSuccess('註冊成功！正在進入後台...');
    setTimeout(() => showDashboard(), 500);
  } catch(e) {
    btn.disabled = false;
    btn.textContent = '註冊';
    showErr('網路錯誤，請稍後再試');
  }
}

function showErr(msg) {
  document.getElementById('authError').textContent = msg;
  document.getElementById('authSuccess').style.display = 'none';
}

function showSuccess(msg) {
  document.getElementById('authSuccess').textContent = msg;
  document.getElementById('authSuccess').style.display = 'block';
  document.getElementById('authError').textContent = '';
}

function logout() {
  localStorage.removeItem('liveplus_user');
  currentUser = null;
  location.reload();
}

// ========== 介面切換 ==========
function showTab(tab) {
  document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(tab + 'Section').style.display = 'block';
  event?.target?.classList?.add('active');

  if (tab === 'dashboard' && currentUser) refreshStats();
  if (tab === 'products' && currentUser) loadProducts();
  if (tab === 'streams' && currentUser) loadStreams();
  if (tab === 'orders' && currentUser) loadOrders();
  if (tab === 'blacklist' && currentUser) loadBlacklist();
  if (tab === 'settings' && currentUser) updatePlanUI();
}

function showDashboard() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('dashboardSection').style.display = 'block';
  updatePlanUI();
  refreshStats();
  loadStreams();
}

function updatePlanUI() {
  const badge = document.getElementById('planBadge');
  if (currentPlan === 'premium') {
    badge.textContent = '🏆 進階版';
    badge.style.background = 'rgba(245,158,11,0.2)';
    badge.style.color = '#fbbf24';
  } else {
    badge.textContent = '免費版';
    badge.style.background = '';
    badge.style.color = '';
  }
}

// ========== 數據看板 ==========
async function refreshStats() {
  if (!currentUser) return;
  const res = await fetch(`${API}/stats?seller_id=${currentUser.seller_id}`);
  const data = await res.json();

  document.getElementById('statTotalOrders').textContent = data.total_orders;
  document.getElementById('statPending').textContent = data.pending;
  document.getElementById('statPaid').textContent = data.paid;
  document.getElementById('statRevenue').textContent = '$' + data.total_revenue.toLocaleString();

  // 熱銷商品
  const pt = document.getElementById('topProductsTable');
  pt.innerHTML = '<tr><th>商品名</th><th>數量</th><th>銷售額</th></tr>';
  data.top_products.forEach(p => {
    pt.innerHTML += `<tr><td>${p.name}</td><td>${p.total_qty}</td><td>$${Number(p.total_sales).toLocaleString()}</td></tr>`;
  });

  // 迷你柱狀圖
  const chart = document.getElementById('dailyChart');
  if (data.daily.length > 0) {
    const max = Math.max(...data.daily.map(d => d.cnt));
    chart.innerHTML = data.daily.map(d =>
      `<div class="mini-chart-bar" style="height:${Math.max(4, (d.cnt / max) * 70)}px" title="${d.day}: ${d.cnt}筆"></div>`
    ).join('');
  } else {
    chart.innerHTML = '<div style="color:#94a3b8;font-size:13px;text-align:center;padding-top:20px;">尚無數據</div>';
  }
}

// ========== 商品管理 ==========
async function loadProducts() {
  if (!currentUser) return;
  const res = await fetch(`${API}/products?seller_id=${currentUser.seller_id}`);
  const data = await res.json();

  const t = document.getElementById('productsTable');
  t.innerHTML = '<tr><th>商品名</th><th>代碼</th><th>價格</th><th>庫存</th><th>操作</th></tr>';

  data.products.forEach(p => {
    t.innerHTML += `<tr>
      <td>${p.name}</td>
      <td><code>${p.code || '-'}</code></td>
      <td>$${p.price.toLocaleString()}</td>
      <td>${p.stock}</td>
      <td>
        <button class="action-btn" onclick="editProduct('${p.id}','${p.name}','${p.code}','${p.price}','${p.stock}','${(p.specs||'').replace(/'/g,"&#39;")}')">編輯</button>
        <button class="action-btn danger" onclick="delProduct('${p.id}')">刪除</button>
      </td>
    </tr>`;
  });

  // 限制提示
  const notice = document.getElementById('productLimitNotice');
  if (currentPlan === 'free' && data.product_count >= data.limits.max_products) {
    notice.style.display = 'block';
  } else {
    notice.style.display = 'none';
  }
}

function showProductModal(id) {
  document.getElementById('editProductId').value = id || '';
  document.getElementById('productModalTitle').textContent = id ? '編輯商品' : '新增商品';
  if (!id) {
    document.getElementById('pName').value = '';
    document.getElementById('pCode').value = '';
    document.getElementById('pPrice').value = '';
    document.getElementById('pStock').value = '';
    document.getElementById('pSpecs').value = '';
  }
  openModal('productModal');
}

function editProduct(id, name, code, price, stock, specs) {
  document.getElementById('editProductId').value = id;
  document.getElementById('productModalTitle').textContent = '編輯商品';
  document.getElementById('pName').value = name;
  document.getElementById('pCode').value = code;
  document.getElementById('pPrice').value = price;
  document.getElementById('pStock').value = stock;
  document.getElementById('pSpecs').value = specs;
  openModal('productModal');
}

async function saveProduct() {
  const id = document.getElementById('editProductId').value;
  const body = {
    seller_id: currentUser.seller_id,
    name: document.getElementById('pName').value.trim(),
    code: document.getElementById('pCode').value.trim(),
    price: parseInt(document.getElementById('pPrice').value) || 0,
    stock: parseInt(document.getElementById('pStock').value) || 0,
    specs: document.getElementById('pSpecs').value.trim()
  };

  if (!body.name || body.price <= 0) { alert('請填寫商品名稱和價格'); return; }

  const res = await fetch(`${API}/products${id ? '/' + id : ''}`, {
    method: id ? 'PUT' : 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) { alert(data.error); return; }

  closeModal('productModal');
  loadProducts();
}

async function delProduct(id) {
  if (!confirm('確定刪除此商品？')) return;
  await fetch(`${API}/products/${id}`, {method: 'DELETE'});
  loadProducts();
}

// ========== 直播管理 ==========
async function loadStreams() {
  if (!currentUser) return;

  // 載入 FB 設定
  document.getElementById('fbPageId').value = currentUser.fb_page_id || '';
  document.getElementById('fbToken').value = currentUser.fb_access_token || '';

  const res = await fetch(`${API}/streams?seller_id=${currentUser.seller_id}`);
  const data = await res.json();

  const list = document.getElementById('streamsList');
  list.innerHTML = '';

  if (data.streams.length === 0) {
    list.innerHTML = '<p style="color:#94a3b8;text-align:center;padding:30px;">尚無直播，按上方「+ 新增直播」開始</p>';
  }

  data.streams.forEach(s => {
    list.innerHTML += `<div class="stream-card">
      <div class="stream-card-header">
        <span class="stream-title">${s.title}</span>
        <div class="stream-status">
          ${s.status === 'active' ? '<span class="live-dot"></span><span style="color:#ef4444;font-size:13px;font-weight:bold;">直播中</span>' : '<span style="color:#94a3b8;font-size:13px;">已結束</span>'}
        </div>
      </div>
      <div class="stream-info">
        <div>📌 關鍵字：<code>${s.keywords}</code></div>
        <div>🔗 貼文ID：${s.fb_post_id || '未設定'}</div>
        <div>⏰ 開始：${s.start_time}</div>
      </div>
      <div class="stream-actions">
        ${s.status === 'active' ? `<button class="btn-primary" style="padding:8px 16px" onclick="fetchComments('${s.id}')">🔄 抓取留言</button>
        <button class="btn-secondary" onclick="endStream('${s.id}')">🔚 結束直播</button>` : ''}
        <button class="action-btn danger" onclick="delStream('${s.id}')">刪除</button>
      </div>
    </div>`;
  });
}

function showStreamModal() { openModal('streamModal'); }

async function saveStream() {
  const body = {
    seller_id: currentUser.seller_id,
    title: document.getElementById('sTitle').value.trim(),
    fb_post_id: document.getElementById('sPostId').value.trim(),
    keywords: document.getElementById('sKeywords').value.trim() || '+1'
  };

  if (!body.title) { alert('請填寫直播標題'); return; }

  const res = await fetch(`${API}/streams`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) { alert(data.error); return; }

  closeModal('streamModal');
  loadStreams();
}

async function fetchComments(streamId) {
  if (!currentUser.fb_access_token && !document.getElementById('fbToken').value) {
    alert('請先設定 Facebook Access Token');
    return;
  }
  const token = document.getElementById('fbToken').value || currentUser.fb_access_token;
  const res = await fetch(`${API}/streams/${streamId}/fetch-comments`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({seller_id: currentUser.seller_id, fb_access_token: token})
  });
  const data = await res.json();
  if (!res.ok) { alert(data.error); return; }
  alert(`✅ 完成！抓到 ${data.new_orders} 筆新訂單（共掃描 ${data.total_fetched} 則留言）`);
  loadOrders();
}

async function endStream(streamId) {
  await fetch(`${API}/streams/${streamId}/end`, {method: 'POST'});
  loadStreams();
}

async function delStream(streamId) {
  if (!confirm('確定刪除此直播記錄？')) return;
  await fetch(`${API}/streams/${streamId}`, {method: 'DELETE'});
  loadStreams();
}

async function saveFBToken() {
  const pageId = document.getElementById('fbPageId').value.trim();
  const token = document.getElementById('fbToken').value.trim();

  const res = await fetch(`${API}/fb/set-token`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({seller_id: currentUser.seller_id, fb_page_id: pageId, fb_access_token: token})
  });
  const data = await res.json();
  if (data.success) {
    currentUser.fb_page_id = pageId;
    currentUser.fb_access_token = token;
    localStorage.setItem('liveplus_user', JSON.stringify(currentUser));
    alert('✅ FB 設定已儲存');
  }
}

// ========== 訂單管理 ==========
async function loadOrders() {
  if (!currentUser) return;
  const status = document.getElementById('orderStatusFilter').value;
  const streamId = document.getElementById('orderStreamFilter').value;

  let url = `${API}/orders?seller_id=${currentUser.seller_id}`;
  if (status) url += `&status=${status}`;
  if (streamId) url += `&stream_id=${streamId}`;

  const res = await fetch(url);
  const data = await res.json();

  const t = document.getElementById('ordersTable');
  t.innerHTML = '<tr><th>訂單編號</th><th>買家</th><th>商品</th><th>數量</th><th>金額</th><th>狀態</th><th>時間</th><th>操作</th></tr>';

  data.orders.forEach(o => {
    const statusClass = `status-${o.status}`;
    const statusText = {'pending':'待處理','paid':'已付款','shipped':'已出貨','completed':'已完成','cancelled':'已取消'}[o.status] || o.status;
    const buyerInfo = o.buyer_name || o.fb_user_name || '-';
    const orderData = encodeURIComponent(JSON.stringify(o));
    t.innerHTML += `<tr>
      <td><code style="font-size:12px">${o.id}</code></td>
      <td>${buyerInfo}</td>
      <td>${o.product_name || '-'}</td>
      <td>${o.quantity}</td>
      <td>$${o.total_price?.toLocaleString() || 0}</td>
      <td><span class="status-tag ${statusClass}">${statusText}</span></td>
      <td style="font-size:12px;color:#64748b">${o.created_at?.substring(0,16) || '-'}</td>
      <td>
        <button class="action-btn" onclick="printOrderFromData('${orderData}')" title="列印出貨單">🖨️</button>
        <button class="action-btn" onclick="editOrder('${o.id}','${(o.buyer_name||'').replace(/'/g,"&#39;")}','${(o.buyer_phone||'').replace(/'/g,"&#39;")}','${(o.buyer_address||'').replace(/'/g,"&#39;")}','${o.status}','${(o.note||'').replace(/'/g,"&#39;")}')">編輯</button>
        <button class="action-btn danger" onclick="delOrder('${o.id}')">刪除</button>
      </td>
    </tr>`;
  });

  // 更新直播篩選
  const streamFilter = document.getElementById('orderStreamFilter');
  const streamsRes = await fetch(`${API}/streams?seller_id=${currentUser.seller_id}`);
  const streamsData = await streamsRes.json();
  streamFilter.innerHTML = '<option value="">全部直播</option>';
  streamsData.streams.forEach(s => {
    streamFilter.innerHTML += `<option value="${s.id}">${s.title}</option>`;
  });
}

function editOrder(id, buyerName, buyerPhone, buyerAddress, status, note) {
  document.getElementById('editOrderId').value = id;
  document.getElementById('oBuyerName').value = buyerName;
  document.getElementById('oBuyerPhone').value = buyerPhone;
  document.getElementById('oBuyerAddress').value = buyerAddress;
  document.getElementById('oStatus').value = status;
  document.getElementById('oNote').value = note;
  openModal('orderModal');
}

async function saveOrder() {
  const id = document.getElementById('editOrderId').value;
  const body = {
    buyer_name: document.getElementById('oBuyerName').value.trim(),
    buyer_phone: document.getElementById('oBuyerPhone').value.trim(),
    buyer_address: document.getElementById('oBuyerAddress').value.trim(),
    status: document.getElementById('oStatus').value,
    note: document.getElementById('oNote').value.trim()
  };

  const res = await fetch(`${API}/orders/${id}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!data.success) { alert(data.error); return; }

  closeModal('orderModal');
  loadOrders();
}

async function delOrder(id) {
  if (!confirm('確定刪除此訂單？')) return;
  await fetch(`${API}/orders/${id}`, {method: 'DELETE'});
  loadOrders();
}

function exportOrders() {
  const streamId = document.getElementById('orderStreamFilter').value;
  let url = `${API}/orders/export?seller_id=${currentUser.seller_id}`;
  if (streamId) url += `&stream_id=${streamId}`;
  window.open(url, '_blank');
}

// 從資料列印訂單（用於訂單表格中的列印按鈕）
function printOrderFromData(dataStr) {
  try {
    const order = JSON.parse(decodeURIComponent(dataStr));
    // 呼叫全域的 printOrder 函數
    if (typeof window.printOrder === 'function') {
      window.printOrder(order);
    } else {
      // 如果全域函數還沒載入，直接執行
      printOrderDirect(order);
    }
  } catch(e) {
    alert('無法列印此訂單');
    console.error(e);
  }
}

// 直接列印（不依賴 DOM）
function printOrderDirect(order) {
  const printContent = `
    <div style="width:280px;padding:15px;font-family:'Courier New',monospace;font-size:14px;border:2px solid #000;">
      <h2 style="text-align:center;margin:0 0 10px;padding-bottom:10px;border-bottom:2px dashed #000;">📦 直播加1 出貨單</h2>
      <div style="margin:8px 0;"><strong>訂單編號：</strong>${order.id}</div>
      <div style="margin:8px 0;"><strong>日　　期：</strong>${order.created_at ? order.created_at.substring(0, 10) : new Date().toISOString().substring(0, 10)}</div>
      <div style="margin:8px 0;"><strong>直播名稱：</strong>${order.stream_title || '-'}</div>
      <hr style="border-top:1px dashed #000;margin:10px 0;">
      <div style="margin:8px 0;"><strong>商品名稱：</strong>${order.product_name || '-'}</div>
      <div style="margin:8px 0;"><strong>規　　格：</strong>${order.specs || '-'}</div>
      <div style="margin:8px 0;"><strong>數　　量：</strong>${order.quantity || 1}</div>
      <div style="margin:8px 0;"><strong>單　　價：</strong>$${(order.unit_price || 0).toLocaleString()}</div>
      <hr style="border-top:1px dashed #000;margin:10px 0;">
      <div style="margin:8px 0;"><strong>收件人：</strong>${order.buyer_name || '-'}</div>
      <div style="margin:8px 0;"><strong>電　話：</strong>${order.buyer_phone || '-'}</div>
      <div style="margin:8px 0;"><strong>地　址：</strong>${order.buyer_address || '-'}</div>
      <div style="margin:8px 0;"><strong>備　註：</strong>${order.note || '-'}</div>
      <hr style="border-top:1px dashed #000;margin:10px 0;">
      <div style="font-size:18px;font-weight:bold;text-align:right;">合計：$${(order.total_price || 0).toLocaleString()}</div>
      <div style="text-align:center;margin-top:15px;padding-top:10px;border-top:2px dashed #000;">
        <p>━━━━━━━━━━━━━━━</p>
        <p>直播加1 自動收單系統</p>
        <p>請妥善保管此單據</p>
      </div>
    </div>
  `;
  
  const printWindow = window.open('', '_blank', 'width=350,height=600');
  printWindow.document.write(`
    <html>
    <head>
      <title>出貨單 - ${order.id}</title>
      <style>body{margin:0;padding:20px;}</style>
    </head>
    <body>${printContent}
    <script>window.onload=function(){window.print();}<\/script>
    </body>
    </html>
  `);
  printWindow.document.close();
}

// ========== 黑名單 ==========
async function loadBlacklist() {
  if (!currentUser) return;

  const notice = document.getElementById('blacklistUpgrade');
  notice.style.display = currentPlan === 'free' ? 'block' : 'none';

  const res = await fetch(`${API}/blacklist?seller_id=${currentUser.seller_id}`);
  const data = await res.json();

  const t = document.getElementById('blacklistTable');
  t.innerHTML = '<tr><th>FB用戶ID</th><th>原因</th><th>加入時間</th><th>操作</th></tr>';

  if (currentPlan === 'free') {
    t.innerHTML += '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:30px;">請升級進階版使用黑名單功能</td></tr>';
    return;
  }

  data.blacklist.forEach(b => {
    t.innerHTML += `<tr>
      <td><code>${b.fb_user_id}</code></td>
      <td>${b.reason || '-'}</td>
      <td style="font-size:12px;color:#64748b">${b.created_at?.substring(0,16) || '-'}</td>
      <td><button class="action-btn danger" onclick="removeBlacklist('${b.id}')">移除</button></td>
    </tr>`;
  });
}

async function removeBlacklist(id) {
  await fetch(`${API}/blacklist/${id}`, {method: 'DELETE'});
  loadBlacklist();
}

// ========== 升級 ==========
function showUpgrade() { openModal('upgradeModal'); }

async function activatePremium() {
  if (!confirm('確認已付款？')) return;
  const res = await fetch(`${API}/subscription/upgrade`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({seller_id: currentUser.seller_id})
  });
  const data = await res.json();
  if (data.success) {
    currentPlan = 'premium';
    currentUser.plan = 'premium';
    localStorage.setItem('liveplus_user', JSON.stringify(currentUser));
    updatePlanUI();
    closeModal('upgradeModal');
    alert('🎉 升級成功！歡迎使用進階版');
  }
}

// ========== Modal 輔助 ==========
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// 點擊背景關閉
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal')) e.target.style.display = 'none';
});

// ========== 啟動 ==========
(function init() {
  const saved = localStorage.getItem('liveplus_user');
  if (saved) {
    currentUser = JSON.parse(saved);
    currentPlan = currentUser.plan;
    showDashboard();
  } else {
    document.getElementById('loginSection').style.display = 'block';
  }
})();
