import datetime
from flask import Blueprint, render_template, request, redirect, jsonify, flash
from bson.objectid import ObjectId

order_bp = Blueprint('orders', __name__)
db = None

# --- CẤU HÌNH ---
ALLOWED_TRANSITIONS = {
    "PENDING_PICKUP": ["PICKED_UP", "CANCELLED"],
    "PICKED_UP": ["IN_TRANSIT", "CANCELLED"],
    "IN_TRANSIT": ["DELIVERING", "PICKED_UP"],
    "DELIVERING": ["DELIVERED", "IN_TRANSIT", "CANCELLED"],
    "DELIVERED": [],
    "CANCELLED": []
}

def init_mongo(mongo):
    global db
    db = mongo.db

# --- HÀM HỖ TRỢ ---
def safe_float(value):
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def validate_status_transition(current_status, new_status):
    if current_status == new_status:
        return True
    allowed_next = ALLOWED_TRANSITIONS.get(current_status, [])
    return new_status in allowed_next

# --- SINH ORDER CODE (Thuần MongoDB) ---
def generate_order_code():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    counter = db.counters.find_one_and_update(
        {"_id": date_str},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = counter.get("seq", 1)
    return f"VT{date_str}{seq:04d}"

# --- TẠO ORDER MỚI ---
def build_order(data):
    code = data.get('order_code', '').strip()
    if not code:
        code = generate_order_code()

    return {
        "order_code": code,
        "recipient_info": {
            "name": data.get('recipient_name', ''),
            "phone": data.get('recipient_phone', ''),
            "address": data.get('recipient_address', '')
        },
        "sender_info": {
            "name": data.get('sender_name', ''),
            "phone": data.get('sender_phone', '')
        },
        "parcel": {
            "weight": safe_float(data.get("weight")),
            "dimensions": {
                "l": safe_float(data.get("dim_l")),
                "w": safe_float(data.get("dim_w")),
                "h": safe_float(data.get("dim_h"))
            },
            "contents": data.get("contents", ""),
            "is_fragile": data.get("is_fragile") == "on",
            "declared_value": safe_float(data.get("declared_value")),
            "quantity": safe_float(data.get("quantity", 1))
        },
        "financials": {
            "cod_amount": safe_float(data.get("cod_amount")),
            "shipping_fee": safe_float(data.get("shipping_fee")),
            "insurance_fee": safe_float(data.get("insurance_fee")),
            "total_amount": (
                safe_float(data.get("cod_amount")) +
                safe_float(data.get("shipping_fee")) +
                safe_float(data.get("insurance_fee"))
            )
        },
        "current_status": "PENDING_PICKUP",
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
        "is_deleted": False
    }

# --- TẠO ORDER CHO FORM (GET) ---
def get_empty_order(code=""):
    return {
        "order_code": code,
        "recipient_info": {"name": "", "phone": "", "address": ""},
        "sender_info": {"name": "", "phone": ""},
        "parcel": {
            "weight": 0,
            "dimensions": {"l": 0, "w": 0, "h": 0},
            "contents": "",
            "is_fragile": False,
            "declared_value": 0,
            "quantity": 1
        },
        "financials": {
            "cod_amount": 0,
            "shipping_fee": 0,
            "insurance_fee": 0,
            "total_amount": 0
        },
        "current_status": "PENDING_PICKUP"
    }
# --- API UPDATE STATUS (QUICK EDIT) ---
@order_bp.route('/api/orders/<oid>/status', methods=['PATCH'])
def api_update_status(oid):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Missing status'}), 400

        order = db.orders.find_one({'_id': ObjectId(oid)})
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        current_status = order.get('current_status')

        # Kiểm tra logic chuyển trạng thái
        if not validate_status_transition(current_status, new_status):
            return jsonify({
                'error': f'Không thể chuyển từ {current_status} sang {new_status}'
            }), 400

        # Cập nhật DB
        db.orders.update_one(
            {'_id': ObjectId(oid)},
            {
                '$set': {
                    'current_status': new_status,
                    'updated_at': datetime.datetime.utcnow()
                }
            }
        )

        # Tạo thông báo
        db.notifications.insert_one({
            "order_id": oid,
            "order_code": order.get("order_code"),
            "type": "STATUS_UPDATED",
            "message": f"Quick status update: {current_status} -> {new_status}",
            "timestamp": datetime.datetime.utcnow(),
            "is_read": False
        })

        return jsonify({'success': True, 'new_status': new_status})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- LIST ORDERS API ---
@order_bp.route('/api/orders')
def api_orders():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        q = request.args.get('q', '').strip()
        status = request.args.get('status', '').strip()

        query = {"$or": [{"is_deleted": False}, {"is_deleted": {"$exists": False}}]}

        if q:
            query["$or"] = [
                {"order_code": {"$regex": q, "$options": "i"}},
                {"recipient_info.name": {"$regex": q, "$options": "i"}},
                {"recipient_info.phone": {"$regex": q, "$options": "i"}},
            ]
        if status:
            query["current_status"] = status

        total = db.orders.count_documents(query)
        pages = (total + limit - 1) // limit
        skip = (page - 1) * limit
        orders = list(db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit))

        for o in orders:
            o["_id"] = str(o["_id"])
            created = o.get("created_at")
            o["created_at_str"] = o["created_at"].strftime("%Y-%m-%d %H:%M:%S") if o.get("created_at") else ""

        return jsonify({"data": orders, "page": page, "pages": pages})
    except Exception as e:
        return jsonify({"data": [], "page": 1, "pages": 0, "error": str(e)}), 500


# --- LIST ORDERS PAGE ---
@order_bp.route('/orders')
def orders_list():
    return render_template('orders.html')


# --- CREATE ORDER ---
@order_bp.route('/orders/new', methods=['GET', 'POST'])
def order_new():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            if not data.get('order_code'):
                data['order_code'] = generate_order_code()
            order = build_order(data)
            result = db.orders.insert_one(order)

            # Notification lưu MongoDB
            db.notifications.insert_one({
                "order_id": str(result.inserted_id),
                "order_code": order["order_code"],
                "type": "ORDER_CREATED",
                "message": "New order created",
                "timestamp": datetime.datetime.utcnow(),
                "is_read": False
            })

            flash(f"Order {order['order_code']} created successfully", "success")
            return redirect('/orders')
        except Exception as e:
            flash(f"Error creating order: {e}", "danger")
            return render_template('order_form.html', order=data)

    empty_order = get_empty_order(generate_order_code())
    return render_template('order_form.html', order=empty_order)

# --- EDIT ORDER ---
@order_bp.route('/orders/edit/<oid>', methods=['GET', 'POST'])
def order_edit(oid):
    try:
        order = db.orders.find_one({'_id': ObjectId(oid)})
    except:
        flash("Invalid order ID", "danger")
        return redirect('/orders')

    if not order:
        flash("Order not found", "danger")
        return redirect('/orders')

    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            new_status = data.get('current_status', order.get('current_status'))

            if not validate_status_transition(order.get('current_status'), new_status):
                flash(f"Cannot change status from {order.get('current_status')} to {new_status}", "warning")
                return render_template('order_form.html', order=order)

            updated_order = build_order(data)
            updated_order['current_status'] = new_status
            updated_order['updated_at'] = datetime.datetime.utcnow()

            db.orders.update_one({'_id': ObjectId(oid)}, {'$set': updated_order})

            db.notifications.insert_one({
                "order_id": oid,
                "order_code": updated_order["order_code"],
                "type": "ORDER_UPDATED",
                "message": f"Status changed to {new_status}",
                "timestamp": datetime.datetime.utcnow(),
                "is_read": False
            })

            flash("Order updated successfully", "success")
            return redirect('/orders')
        except Exception as e:
            flash(f"Error updating order: {e}", "danger")

    return render_template('order_form.html', order=order)

# --- DELETE ORDER ---
@order_bp.route('/api/orders/<oid>', methods=['DELETE'])
def order_delete(oid):
    try:
        db.orders.update_one({'_id': ObjectId(oid)}, {'$set': {"is_deleted": True}})
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500
