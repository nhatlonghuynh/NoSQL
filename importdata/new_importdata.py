import random
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from faker import Faker

# Cấu hình kết nối
client = MongoClient("mongodb://localhost:27017")
db = client["ViettelPost_Real_DB"]

# Xóa dữ liệu cũ
db.users.drop()
db.orders.drop()
db.shipments.drop()
db.transactions.drop()
db.post_offices.drop()
db.shippers.drop()

# Khởi tạo Faker
fake = Faker('vi_VN')
Faker.seed(0)

print("⏳ Đang khởi tạo dữ liệu mẫu thực tế...")

# ==========================================
# 1. TẠO BƯU CỤC
# ==========================================
hcm_locations = [
    {"name": "Bưu cục Quận 1", "addr": "Số 1 Công Xã Paris, Bến Nghé, Q1, TP.HCM", "coords": [106.699, 10.779]},
    {"name": "Bưu cục Tân Bình", "addr": "288 Hoàng Văn Thụ, P4, Tân Bình, TP.HCM", "coords": [106.658, 10.796]},
    {"name": "Bưu cục Bình Thạnh", "addr": "270 Bạch Đằng, P24, Bình Thạnh, TP.HCM", "coords": [106.702, 10.801]},
    {"name": "Bưu cục Thủ Đức", "addr": "128 Kha Vạn Cân, Hiệp Bình Chánh, Thủ Đức", "coords": [106.735, 10.835]},
    {"name": "Bưu cục Quận 7", "addr": "15 Nguyễn Lương Bằng, Tân Phú, Q7, TP.HCM", "coords": [106.721, 10.731]}
]

post_offices = []
for i, loc in enumerate(hcm_locations):
    post_offices.append({
        "_id": ObjectId(),
        "office_code": f"VTP-HCM-{str(i+1).zfill(3)}",
        "name": loc["name"],
        "address": loc["addr"],
        "location": { "type": "Point", "coordinates": loc["coords"] },
        "operating_hours": "07:30 - 21:00",
        "hotline": f"1900800{i}",
        "manager_name": fake.name(),
        "status": "ACTIVE"
    })
db.post_offices.insert_many(post_offices)
print(f"✅ Đã tạo {len(post_offices)} bưu cục.")

# ==========================================
# 2. TẠO SHIPPERS
# ==========================================
shippers = []
for i in range(20):
    po = random.choice(post_offices)
    shippers.append({
        "_id": ObjectId(),
        "shipper_code": f"SHP{str(i+1000)}",
        "full_name": fake.name(),
        "phone_number": fake.phone_number(),
        "assigned_post_office_id": po["_id"],
        "current_location": {
            "type": "Point",
            "coordinates": [
                po["location"]["coordinates"][0] + random.uniform(-0.02, 0.02),
                po["location"]["coordinates"][1] + random.uniform(-0.02, 0.02)
            ]
        },
        "vehicle_type": random.choice(["HONDA_WAVE", "YAMAHA_SIRIUS", "WINNER_X"]),
        "status": random.choice(["IDLE", "DELIVERING", "OFFLINE"]),
        "rating": round(random.uniform(3.5, 5.0), 1)
    })
db.shippers.insert_many(shippers)
print(f"✅ Đã tạo {len(shippers)} tài xế.")

# ==========================================
# 3. TẠO USERS
# ==========================================
users = []
for i in range(50):
    users.append({
        "_id": ObjectId(),
        "full_name": fake.name(),
        "phone_number": fake.phone_number(),
        "email": fake.email(),
        "user_type": random.choice(["INDIVIDUAL", "BUSINESS_SME"]),
        "default_address": fake.address(),
        "created_at": datetime.now() - timedelta(days=random.randint(30, 365))
    })
db.users.insert_many(users)
print(f"✅ Đã tạo {len(users)} người dùng.")

# ==========================================
# 4. TẠO ORDERS & SHIPMENTS (Đã sửa lỗi logic ngày giờ)
# ==========================================
orders = []
shipments = []
transactions = []

service_types = [
    {"code": "VCN", "name": "Chuyển phát nhanh", "fee_base": 30000, "days": 2},
    {"code": "VTK", "name": "Chuyển phát tiết kiệm", "fee_base": 15000, "days": 5},
    {"code": "VHT", "name": "Hỏa tốc", "fee_base": 70000, "days": 0.5} 
]

parcel_contents = ["Quần áo thời trang", "Mỹ phẩm", "Linh kiện điện tử", "Sách vở", "Thực phẩm khô"]

for i in range(120):
    sender = random.choice(users)
    svc = random.choice(service_types)
    created_at = datetime.now() - timedelta(days=random.randint(0, 30))
    
    # Logic Trạng thái
    rand_status = random.random()
    if rand_status < 0.6: current_status = "DELIVERED_SUCCESS"
    elif rand_status < 0.8: current_status = "IN_TRANSIT"
    elif rand_status < 0.9: current_status = "PICKED_UP"
    elif rand_status < 0.95: current_status = "CREATED"
    else: current_status = "CANCELLED"

    weight = round(random.uniform(0.1, 5.0), 2)
    shipping_fee = svc["fee_base"] + (weight * 2000)
    cod_amount = random.choice([0, 0, random.randint(100, 2000) * 1000])
    total_amount = shipping_fee + cod_amount

    order_id = ObjectId()
    tracking_code = f"VTP{datetime.now().year}{str(i+10000)}"
    
    orders.append({
        "_id": order_id,
        "order_code": f"OD{random.randint(100000,999999)}",
        "tracking_code": tracking_code,
        "sender_id": sender["_id"],
        "sender_info": { "name": sender["full_name"], "phone": sender["phone_number"], "address": sender["default_address"] },
        "recipient_info": { "name": fake.name(), "phone": fake.phone_number(), "address": fake.address() },
        "service_info": svc,
        "financials": { "cod_amount": cod_amount, "shipping_fee": shipping_fee, "total_payment": total_amount },
        "current_status": current_status,
        "created_at": created_at,
        "updated_at": datetime.now()
    })

    # --- LOGIC LỊCH SỬ SHIPMENT (ĐÃ FIX LỖI) ---
    history = [{
        "status": "CREATED",
        "desc": "Đơn hàng đã được tạo",
        "time": created_at,
        "location": "Online"
    }]

    assigned_shipper = None
    if current_status not in ["CREATED", "CANCELLED"]:
        pickup_time = created_at + timedelta(hours=random.randint(1, 6))
        assigned_shipper = random.choice(shippers)
        
        if pickup_time < datetime.now():
            history.append({
                "status": "PICKED_UP",
                "desc": f"Shipper {assigned_shipper['full_name']} đã lấy hàng",
                "time": pickup_time,
                "location": sender["default_address"]
            })
            
            wh_time = pickup_time + timedelta(hours=random.randint(1, 3))
            history.append({
                "status": "WAREHOUSE_IN",
                "desc": "Nhập kho bưu cục gửi",
                "time": wh_time,
                "location": "Bưu cục trung chuyển"
            })

            if current_status in ["IN_TRANSIT", "DELIVERED_SUCCESS"]:
                transit_time = wh_time + timedelta(hours=random.randint(5, 12))
                history.append({
                    "status": "IN_TRANSIT",
                    "desc": "Đang luân chuyển",
                    "time": transit_time,
                    "location": "Trung tâm khai thác HCM"
                })

            if current_status == "DELIVERED_SUCCESS":
                # --- FIX LỖI TẠI ĐÂY ---
                # Xử lý riêng cho trường hợp Hỏa tốc (0.5 ngày) hoặc thường
                if svc["days"] < 1:
                    # Nếu hỏa tốc, giao sau 4-12 tiếng
                    hours_to_add = random.randint(4, 12)
                    delivery_time = wh_time + timedelta(hours=hours_to_add)
                else:
                    # Nếu thường, giao sau 1 -> svc["days"] ngày
                    # Dùng int() để đảm bảo tham số là số nguyên
                    days_add = random.randint(1, int(svc["days"]))
                    delivery_time = wh_time + timedelta(days=days_add)

                history.append({
                    "status": "DELIVERED_SUCCESS",
                    "desc": "Giao hàng thành công",
                    "time": delivery_time,
                    "location": "Địa chỉ người nhận"
                })

    shipments.append({
        "_id": ObjectId(),
        "order_id": order_id,
        "tracking_code": tracking_code,
        "status_history": history,
        "shipper_id": assigned_shipper["_id"] if assigned_shipper else None
    })

    if total_amount > 0:
        transactions.append({
            "_id": ObjectId(),
            "order_id": order_id,
            "amount": total_amount,
            "status": "COMPLETED" if current_status == "DELIVERED_SUCCESS" else "PENDING",
            "created_at": created_at
        })

db.orders.insert_many(orders)
db.shipments.insert_many(shipments)
db.transactions.insert_many(transactions)

print(f"✅ Đã tạo {len(orders)} đơn hàng.")
print(f"✅ Đã tạo {len(shipments)} thông tin vận chuyển.")
print(f"✅ Đã tạo {len(transactions)} giao dịch.")
print("\n🎉 HOÀN TẤT! Không còn lỗi nữa nhé!")