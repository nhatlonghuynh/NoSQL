from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import random

client = MongoClient("mongodb://localhost:27017")
db = client["ViettelPost_DB"]

# -------------------------
# Tạo 10 users
users = []
for i in range(10):
    users.append({
        "_id": ObjectId(),
        "full_name": f"Nguyen Van {chr(65+i)}",
        "phone_number": f"+84901{str(234567+i).zfill(5)}",
        "email": f"user{i}@example.com",
        "hashed_password": "hashedpassword123",
        "user_type": "INDIVIDUAL",
        "address_book": [
            {
                "alias": "Nhà",
                "contact_name": f"Nguyen Van {chr(65+i)}",
                "contact_phone": f"+84901{str(234567+i).zfill(5)}",
                "street": f"{100+i} Le Loi",
                "ward": "Ben Nghe",
                "district": "1",
                "province": "Ho Chi Minh",
                "is_default": True
            }
        ],
        "payment_info": { "bank_name":"Vietcombank", "account_number":f"01234{i}" },
        "status":"ACTIVE",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

db.users.insert_many(users)
db.users.create_index("phone_number", unique=True)
db.users.create_index("email", unique=True)

# -------------------------
# Tạo 20 orders
orders = []
shipments = []
transactions = []

for i in range(20):
    user = random.choice(users)
    order_id = ObjectId()
    tracking_code = f"TRKVT202500{str(100+i).zfill(2)}"
    
    order = {
        "_id": order_id,
        "order_code": f"VT202500{str(100+i).zfill(2)}",
        "sender_id": user["_id"],
        "sender_info": { "name": user["full_name"], "phone": user["phone_number"], "address": user["address_book"][0]["street"] },
        "recipient_info": { "name": f"Nguyen Recipient {i}", "phone": f"+84907{str(654321+i).zfill(5)}", "address": f"{200+i} Nguyen Trai, Q5, HCM" },
        "parcel": {
            "weight": round(random.uniform(0.5,5.0),1),
            "dimensions": {"l":random.randint(10,50),"w":random.randint(10,50),"h":random.randint(5,30)},
            "contents": random.choice(["Quần áo","Giày dép","Sách","Điện tử"]),
            "quantity": random.randint(1,3),
            "declared_value": random.randint(100000,1000000),
            "is_fragile": random.choice([True, False])
        },
        "service": { "code":"ECONOMY", "name":"Economy","estimated_delivery_time":"3-5 days" },
        "financials": { "cod_amount": 0, "shipping_fee": 30000, "insurance_fee":0, "total_amount":30000 },
        "payment_method":"SENDER_PAYS",
        "notes": { "for_shipper":"Gọi trước 30 phút", "allowed_to_view": True },
        "current_status": random.choice(["PICKED_UP","CREATED","IN_TRANSIT"]),
        "tracking_code": tracking_code,
        "assigned_shipper_code": "SHP001",
        "created_at": datetime.utcnow() - timedelta(days=random.randint(0,10)),
        "created_by": "MOBILE_APP",
        "updated_at": datetime.utcnow()
    }
    orders.append(order)

    # Shipment cho order
    shipment = {
        "_id": ObjectId(),
        "order_id": order_id,
        "tracking_code": tracking_code,
        "status_history": [
            {"status_code": "CREATED", "description":"Order created", "timestamp": datetime.utcnow() - timedelta(days=random.randint(0,10)), "shipper_code": None, "location": None},
            {"status_code": "PICKED_UP", "description":"Picked up by shipper", "timestamp": datetime.utcnow(), "shipper_code":"SHP001", "location": {"type":"Point","coordinates":[106.7+random.random()*0.01,10.8+random.random()*0.01]}}
        ],
        "estimated_delivery_date": datetime.utcnow() + timedelta(days=3),
        "actual_delivery_date": None,
        "last_updated_at": datetime.utcnow()
    }
    shipments.append(shipment)

    # Transaction cho order
    transaction = {
        "_id": ObjectId(),
        "order_id": order_id,
        "transaction_code": f"TXN202500{str(100+i).zfill(2)}",
        "transaction_type": "COD_COLLECTION",
        "amount": random.randint(100000,500000),
        "currency": "VND",
        "status": "COMPLETED",
        "executed_by_id": user["_id"],
        "created_at": datetime.utcnow()
    }
    transactions.append(transaction)

db.orders.insert_many(orders)
db.orders.create_index("order_code", unique=True)
db.orders.create_index("tracking_code", unique=True)
db.orders.create_index("sender_id")
db.orders.create_index("recipient_info.phone")
db.orders.create_index("current_status")

db.shipments.insert_many(shipments)
db.shipments.create_index("tracking_code")
db.shipments.create_index("order_id")
db.shipments.create_index("status_history.timestamp")

db.transactions.insert_many(transactions)
db.transactions.create_index("order_id")
db.transactions.create_index("transaction_code", unique=True)

# -------------------------
# Post offices (3 offices)
post_offices = []
for i in range(3):
    post_offices.append({
        "_id": ObjectId(),
        "office_code": f"POHCM0{i+1}",
        "name": f"Bưu cục HCM 0{i+1}",
        "address": { "street": f"{100+i} Le Loi","ward":"Ben Nghe","district":"1","province":"Ho Chi Minh" },
        "location": { "type":"Point", "coordinates": [106.7+0.01*i, 10.8+0.01*i] },
        "operating_hours":"7:00-19:00",
        "phone_number": f"+849011100{i+1}"
    })

db.post_offices.insert_many(post_offices)
db.post_offices.create_index("office_code", unique=True)
db.post_offices.create_index([("location","2dsphere")])
# -------------------------
# Shippers (5 shippers)
shippers = []
for i in range(5):
    post_office = random.choice(post_offices)
    shippers.append({
        "_id": ObjectId(),
        "shipper_code": f"SHP00{i+1}",
        "full_name": f"Tran Van Shipper{i+1}",
        "phone_number": f"+84908{str(888000+i).zfill(3)}",
        "current_post_office_id": ObjectId(),
        "current_location": {
            "type":"Point",
            "coordinates":[
                post_office["location"]["coordinates"][0] + random.uniform(-0.01,0.01),
                post_office["location"]["coordinates"][1] + random.uniform(-0.01,0.01)
                            ]
                    },
        "status":"ON_DUTY",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

db.shippers.insert_many(shippers)
db.shippers.create_index("shipper_code", unique=True)
db.shippers.create_index("phone_number", unique=True)


print("✅ Import dữ liệu mẫu (~40 dòng) hoàn tất!")
