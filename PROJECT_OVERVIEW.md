# ViettelPost Demo Web - Tổng Quan Project

## 📋 Giới Thiệu
**ViettelPost Demo** là một ứng dụng web nâng cao được xây dựng với **Flask** + **MongoDB**, mô phỏng hệ thống quản lý vận đơn của một công ty giao hàng.

---

## 🎯 Các Chức Năng Chính

### 1. **Dashboard (Trang Chủ)**
- 📊 Tổng số đơn hàng
- 💰 Tổng tiền COD đã thu (từ transactions)
- 📈 Biểu đồ thống kê đơn hàng theo trạng thái
- 🔍 Tìm kiếm nhanh (Quick Track)
- 📝 Danh sách 10 đơn hàng gần nhất

**Route:** `GET /` → `main_bp.index()`

---

### 2. **Quản Lý Vận Đơn (Orders Management)**
- ➕ Tạo đơn hàng mới
- 📋 Danh sách toàn bộ đơn hàng (có phân trang)
- 🔎 Tìm kiếm & lọc: theo từ khóa, trạng thái, COD, ngày tạo
- ⚡ Cập nhật trạng thái nhanh (Quick Edit)
- ✏️ Chỉnh sửa đơn hàng
- 🗑️ Xóa đơn hàng

**Routes:**
- `GET /orders` → Danh sách
- `GET /orders/new` → Form tạo mới
- `POST /orders/create` → Lưu vào DB
- `GET /orders/<id>` → Chi tiết
- `POST /orders/<id>/update` → Cập nhật
- `POST /orders/<id>/delete` → Xóa
- `PATCH /api/orders/<id>/status` → API cập nhật trạng thái (AJAX)

**Trạng thái đơn hàng (State Machine):**
```
PENDING_PICKUP (Chờ lấy hàng)
    ↓
PICKED_UP (Đã lấy hàng) 
    ↓
IN_TRANSIT (Đang luân chuyển)
    ↓
DELIVERING (Đang giao hàng)
    ↓
DELIVERED (Giao thành công)

CANCELLED (Đã hủy) - Có thể từ bất kỳ trạng thái nào
```

---

### 3. **Theo Dõi Vận Đơn (Track Order)**
- 🎯 Tìm đơn hàng theo mã vận đơn (order_code)
- 📍 Hiển thị thông tin đơn hàng & lịch sử vận chuyển
- 📦 Lịch sử shipment (các lần giao)

**Route:** `GET /track?code=<order_code>` → `main_bp.track_form()`

---

### 4. **Quản Lý Bưu Cục (Post Offices)**
- 📍 Danh sách bưu cục
- ➕ Thêm bưu cục mới
- ✏️ Sửa thông tin bưu cục
- 🗑️ Xóa bưu cục
- 🗺️ Hiển thị vị trí trên bản đồ (Leaflet)

**Routes:**
- `GET /postoffices` → Danh sách
- `POST /postoffices/create` → Tạo mới
- `POST /postoffices/update` → Cập nhật
- `POST /postoffices/delete/<id>` → Xóa
- `GET /api/postoffices/all` → API JSON cho Map

**MongoDB Structure:**
```json
{
  "_id": ObjectId,
  "office_code": "PO001",
  "name": "Bưu cục Hoàn Kiếm",
  "phone_number": "024...",
  "operating_hours": "7h-19h",
  "address": {
    "street": "Số 1 Phạm Hùng",
    "ward": "Thanh Xuân",
    "district": "Thanh Xuân",
    "province": "Hà Nội"
  },
  "location": {
    "type": "Point",
    "coordinates": [105.8342, 21.0278]  // [Longitude, Latitude]
  }
}
```

---

### 5. **Quản Lý Shipper (Delivery Personnel)**
- 👥 Danh sách shipper
- 🔍 Tìm kiếm shipper
- 🗺️ Hiển thị vị trí shipper trên bản đồ (Leaflet + Marker Cluster)
- 📊 Liên kết với bưu cục (using $lookup)

**Routes:**
- `GET /shippers` → Danh sách với map
- `GET /api/shippers/all` → API JSON

**MongoDB Query (Aggregation):**
```python
db.shippers.aggregate([
    {
        '$lookup': {
            'from': 'post_offices',
            'localField': 'current_post_office_id',
            'foreignField': '_id',
            'as': 'post_office_info'
        }
    },
    {
        '$unwind': {
            'path': '$post_office_info',
            'preserveNullAndEmptyArrays': True
        }
    }
])
```

---

## 🗄️ Cấu Trúc MongoDB Collections

| Collection | Mục đích |
|-----------|---------|
| `orders` | Lưu thông tin vận đơn |
| `shipments` | Lưu chi tiết vận chuyển (tracking history) |
| `post_offices` | Danh sách bưu cục |
| `shippers` | Danh sách nhân viên giao hàng |
| `transactions` | Giao dịch thanh toán (COD, shipping fees) |
| `notifications` | Thông báo cho người dùng |
| `users` | Người dùng hệ thống |
| `counters` | Bộ đếm để tạo order_code độc nhất |

---

## 📡 API Routes Chi Tiết

### Dashboard & Tracking
```
GET  /                              → Dashboard (Hiển thị index.html)
GET  /track?code=<code>             → Trang tracking đơn hàng
GET  /api/postoffices/all           → JSON danh sách bưu cục
GET  /api/shippers/active           → JSON danh sách shipper active
```

### Order Management
```
GET  /orders                         → Danh sách đơn (orders.html)
GET  /orders/new                     → Form tạo mới
POST /orders/create                  → Lưu đơn mới
GET  /orders/<id>                    → Chi tiết 1 đơn
POST /orders/<id>/update             → Cập nhật đơn
POST /orders/<id>/delete             → Xóa đơn
PATCH /api/orders/<id>/status        → API cập nhật trạng thái (AJAX)
GET  /api/orders/list                → JSON danh sách (pagination)
```

### Post Office Management
```
GET  /postoffices                    → Danh sách bưu cục
POST /postoffices/create             → Thêm mới
POST /postoffices/update             → Cập nhật
POST /postoffices/delete/<id>        → Xóa
GET  /api/postoffices/all            → JSON (cho map)
```

### Shipper Management
```
GET  /shippers                       → Danh sách shipper + map
GET  /api/shippers/all               → JSON shipper (+ post office info)
GET  /api/shippers/active            → JSON shipper active
```

### Notifications
```
POST /api/order/update_status        → Cập nhật status + tạo notification
POST /api/send_notification          → Gửi notification thủ công
```

---

## 🔌 Cách Gọi API từ View (Frontend)

### 1️⃣ **Cập Nhật Trạng Thái Đơn Hàng (Quick Edit)**

**HTML Template (orders.html):**
```html
<select 
    class="form-select form-select-sm" 
    onchange="updateStatus('{{ order._id }}', this, '{{ order.current_status }}')"
>
    <option value="PENDING_PICKUP">Chờ lấy hàng</option>
    <option value="PICKED_UP">Đã lấy hàng</option>
    <option value="IN_TRANSIT">Đang luân chuyển</option>
    <option value="DELIVERING">Đang giao hàng</option>
    <option value="DELIVERED">Giao thành công</option>
    <option value="CANCELLED">Đã hủy</option>
</select>
```

**JavaScript:**
```javascript
async function updateStatus(orderId, selectElem, oldStatus) {
    const newStatus = selectElem.value;
    selectElem.disabled = true;

    try {
        const res = await fetch(`/api/orders/${orderId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Không thể cập nhật");
        }

        // Reload page hoặc update UI
        location.reload();
    } catch (error) {
        alert("Lỗi: " + error.message);
        selectElem.value = oldStatus; // Revert
    } finally {
        selectElem.disabled = false;
    }
}
```

---

### 2️⃣ **Tải Danh Sách Đơn Hàng (Pagination + Filter)**

**JavaScript (orders.html):**
```javascript
async function loadOrders() {
    const search = document.getElementById('search-input').value;
    const status = document.getElementById('status-filter').value;
    const codMin = document.getElementById('cod-min').value;
    const codMax = document.getElementById('cod-max').value;
    const dateFrom = document.getElementById('date-from').value;
    const dateTo = document.getElementById('date-to').value;

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (codMin) params.append('cod_min', codMin);
    if (codMax) params.append('cod_max', codMax);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    params.append('page', currentPage);
    params.append('limit', currentLimit);

    const res = await fetch(`/api/orders/list?${params.toString()}`);
    const data = await res.json();

    renderTable(data.orders);
    renderPagination(data.total_pages, data.current_page);
}

// Gọi khi click Filter button
document.getElementById('search-btn').addEventListener('click', loadOrders);
```

---

### 3️⃣ **Tải Bản Đồ Bưu Cục (Leaflet)**

**JavaScript (postoffices.html):**
```javascript
// Khởi tạo bản đồ
const map = L.map('map').setView([21.0278, 105.8342], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

// Fetch danh sách bưu cục từ API
fetch('/api/postoffices/all')
    .then(res => res.json())
    .then(offices => {
        offices.forEach(office => {
            if (office.location && office.location.coordinates) {
                const [lng, lat] = office.location.coordinates;
                L.marker([lat, lng])
                    .bindPopup(`<b>${office.name}</b><br>${office.address}`)
                    .addTo(map);
            }
        });
    });
```

---

### 4️⃣ **Tải Danh Sách Shipper với Marker Cluster**

**JavaScript (shippers.html):**
```javascript
const map = L.map('map').setView([21.0278, 105.8342], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const markers = L.markerClusterGroup();

// Fetch shipper data
fetch('/api/shippers/all')
    .then(res => res.json())
    .then(shippers => {
        shippers.forEach(s => {
            if (s.current_location && s.current_location.coordinates) {
                const [lng, lat] = s.current_location.coordinates;
                const marker = L.marker([lat, lng])
                    .bindPopup(`<b>${s.full_name}</b><br>${s.phone_number}`);
                markers.addLayer(marker);
            }
        });
        
        map.addLayer(markers);
        if (markers.getLayers().length) {
            map.fitBounds(markers.getBounds());
        }
    });

// Search filter
document.getElementById('search-input').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('#shipper-list li').forEach(li => {
        li.style.display = li.innerText.toLowerCase().includes(query) ? '' : 'none';
    });
});
```

---

### 5️⃣ **Gửi Thông Báo**

**JavaScript:**
```javascript
async function sendNotification(userId, message, orderCode) {
    const res = await fetch('/api/send_notification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            message: message,
            type: 'ORDER_UPDATE',
            order_code: orderCode
        })
    });

    if (res.ok) {
        console.log('Notification sent!');
    }
}
```

---

## 💾 MongoDB Queries Chính

### 1. **Thống Kê Đơn Hàng Theo Trạng Thái**
```javascript
db.orders.aggregate([
    { '$group': { '_id': '$current_status', 'count': { '$sum': 1 } } },
    { '$sort': { 'count': -1 } }
])
```

### 2. **Tính Tổng COD Đã Thu**
```javascript
db.transactions.aggregate([
    { '$match': { 'transaction_type': 'COD_COLLECTION', 'status': 'COMPLETED' } },
    { '$group': { '_id': null, 'total_cod': { '$sum': '$amount' } } }
])
```

### 3. **Tìm Đơn Hàng Theo Mã**
```javascript
db.orders.find_one({ 'order_code': 'VT20251201001' })
```

### 4. **Lấy Shipper + Thông Tin Bưu Cục**
```javascript
db.shippers.aggregate([
    {
        '$lookup': {
            'from': 'post_offices',
            'localField': 'current_post_office_id',
            'foreignField': '_id',
            'as': 'post_office_info'
        }
    },
    { '$unwind': { 'path': '$post_office_info', 'preserveNullAndEmptyArrays': True } }
])
```

### 5. **Lọc Đơn Hàng Với Nhiều Điều Kiện**
```javascript
db.orders.find({
    'current_status': 'DELIVERED',
    'financials.cod_amount': { '$gte': 100000, '$lte': 500000 },
    'created_at': {
        '$gte': datetime(2025, 1, 1),
        '$lte': datetime(2025, 12, 31)
    }
}).skip(0).limit(10)
```

### 6. **Tạo/Cập Nhật Counter**
```javascript
db.counters.find_one_and_update(
    { '_id': '20251202' },
    { '$inc': { 'seq': 1 } },
    { 'upsert': True, 'return_document': True }
)
```

### 7. **Xóa Mềm (Soft Delete)**
```javascript
db.orders.update_one(
    { '_id': ObjectId('...') },
    { '$set': { 'is_deleted': True, 'updated_at': datetime.utcnow() } }
)
```

---

## 🔐 Kết Nối MongoDB

**Config (app.py):**
```python
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/ViettelPost_DB')
mongo = PyMongo(app)
```

**Sử dụng trong Blueprint:**
```python
def init_mongo(mongo):
    global db
    db = mongo.db

# Trong route:
result = db.orders.find_one({'order_code': code})
```

---

## 📦 Dependencies

```
Flask==3.0.3
Flask-PyMongo==3.0.1
dnspython
bcrypt
redis
```

---

## 🚀 Cách Chạy Project

1. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Đảm bảo MongoDB chạy:**
   ```bash
   mongod
   ```

3. **Chạy Flask app:**
   ```bash
   python app.py
   ```

4. **Truy cập:** http://127.0.0.1:5000

---

## 🎨 Frontend Stack

- **Template Engine:** Jinja2
- **CSS Framework:** Bootstrap 5 (CDN)
- **Map Library:** Leaflet + Marker Cluster
- **Chart Library:** Chart.js
- **AJAX:** Fetch API (native)

---

## 📝 Ghi Chú

- ✅ Mô phỏng hệ thống quản lý vận đơn thực tế
- ✅ Sử dụng MongoDB aggregation pipeline
- ✅ Có logic chuyển trạng thái (State Machine)
- ✅ Tích hợp Map cho bưu cục & shipper
- ✅ Hỗ trợ filter & search advanced
- ⚠️ Chưa có authentication (có comment về bcrypt)
- ⚠️ Chưa sử dụng Redis (khai báo nhưng chưa dùng)

---

**Project được xây dựng cho mục đích học tập NoSQL + Flask.**
