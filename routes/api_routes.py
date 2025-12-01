from flask import Blueprint, jsonify, request, abort
from bson.objectid import ObjectId
from datetime import datetime
from math import ceil

api_bp = Blueprint('api', __name__, url_prefix='/api')
db = None

def init_mongo(mongo):
    global db
    db = mongo.db

def safe_datetime(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt or None

def safe_get(d, keys, default=None):
    """Lấy giá trị nested dict an toàn"""
    for k in keys:
        if d and isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default

# --------- Update Order Status & Notifications ----------
@api_bp.route('/order/update_status', methods=['POST'])
def update_order_status():
    data = request.json
    order_id = data.get('order_id')
    new_status = data.get('status')

    if not order_id or not new_status:
        abort(400, 'order_id and status required')

    try:
        order_oid = ObjectId(order_id)
    except Exception:
        abort(400, 'Invalid order_id')

    # Cập nhật trạng thái đơn
    order = db.orders.find_one_and_update(
        {"_id": order_oid},
        {"$set": {"current_status": new_status, "updated_at": datetime.utcnow()}},
        return_document=True
    )
    if not order:
        abort(404, 'Order not found')

    # Tạo notification
    notif = {
        "user_ids": [],
        "type": f"ORDER_{new_status}",
        "order_code": order.get('order_code'),
        "message": "",
        "timestamp": datetime.utcnow(),
        "is_read": False
    }

    recipients = []
    if new_status == "PICKED_UP":
        notif['message'] = "Đơn hàng đã được shipper lấy"
        if 'sender' in order:
            recipients.append(order['sender'].get('full_name'))
        if 'assigned_shipper_code' in order:
            recipients.append(order['assigned_shipper_code'])
    elif new_status == "IN_TRANSIT":
        notif['message'] = "Đơn hàng sắp được giao trong 30 phút"
        if 'recipient_info' in order:
            recipients.append(order['recipient_info'].get('name'))

    # Lưu notification vào MongoDB
    for r in recipients:
        n = notif.copy()
        n['user_id'] = r
        db.notifications.insert_one(n)

    return jsonify({"status": "ok"})

# --------- Send Notification ----------
@api_bp.route('/send_notification', methods=['POST'])
def send_notification():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    if not user_id or not message:
        abort(400, 'user_id and message required')

    notif = {
        "user_id": user_id,
        "type": data.get('type', 'ORDER_UPDATE'),
        "order_code": data.get('order_code'),
        "message": message,
        "timestamp": datetime.utcnow(),
        "is_read": False
    }
    db.notifications.insert_one(notif)
    return jsonify({"status": "ok"})

# --------- Orders Summary ----------
@api_bp.route('/orders/summary')
def api_orders_summary():
    pipeline = [{'$group': {'_id': '$current_status', 'count': {'$sum': 1}}}]
    data = list(db.orders.aggregate(pipeline))
    return jsonify(data)

# --------- COD Transactions ----------
@api_bp.route('/transactions/cod')
def api_transactions_cod():
    pipeline = [
        {'$match': {'transaction_type': 'COD_COLLECTION', 'status': 'COMPLETED'}},
        {'$group': {'_id': None, 'total_cod': {'$sum': '$amount'}}}
    ]
    data = list(db.transactions.aggregate(pipeline))
    total = float(data[0]['total_cod']) if data else 0
    return jsonify({'total_cod': total})

# --------- PostOffices ----------
@api_bp.route('/postoffices/all')
def api_postoffices_all():
    offices = list(db.postoffices.find({}, {'name':1,'office_code':1,'location':1,'address':1,'operating_hours':1}))
    for o in offices:
        o['_id'] = str(o['_id'])
    return jsonify(offices)

# --------- Shippers ----------
@api_bp.route('/shippers/active')
def api_shippers_active():
    shps = list(db.shippers.find({'status': {'$in': ['ON_DUTY','ACTIVE']}}))
    for s in shps:
        s['_id'] = str(s.get('_id'))
        po_id = s.get('current_post_office_id')
        s['current_post_office_name'] = None
        if po_id:
            po = db.postoffices.find_one({'_id': po_id}, {'name':1})
            if po:
                s['current_post_office_name'] = po.get('name')
    return jsonify(shps)

# --------- Track Order ----------
@api_bp.route('/track/<code>')
def api_track(code):
    order = db.orders.find_one({'order_code': code})
    shipment = db.shipments.find_one({'tracking_code': code})
    if order: order['_id'] = str(order.get('_id'))
    if shipment: shipment['_id'] = str(shipment.get('_id'))
    return jsonify({'order': order, 'shipment': shipment})

# --------- Orders for Frontend Table ----------
@api_bp.route('/orders/all')
def api_orders_all():
    cursor = db.orders.find({}, {'order_code':1, 'recipient_info':1, 'current_status':1, 'created_at':1}).sort('created_at', -1).limit(200)
    orders = []
    for o in cursor:
        o['_id'] = str(o.get('_id'))
        ri = o.get('recipient_info') or {}
        orders.append({
            '_id': o['_id'],
            'order_code': o.get('order_code'),
            'recipient_name': ri.get('name'),
            'recipient_phone': ri.get('phone'),
            'current_status': o.get('current_status'),
            'created_at': safe_datetime(o.get('created_at'))
        })
    return jsonify(orders)

# --------- Orders with Pagination ----------
@api_bp.route('/orders')
def api_orders():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 25))
        if page < 1: page = 1
        if limit < 1 or limit > 500: limit = 25
    except Exception:
        page, limit = 1, 25

    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()

    query = {}
    if q:
        query['$or'] = [
            {'order_code': {'$regex': q, '$options':'i'}},
            {'recipient_info.name': {'$regex': q, '$options':'i'}},
            {'recipient_info.phone': {'$regex': q, '$options':'i'}}
        ]
    if status:
        query['current_status'] = status

    total = db.orders.count_documents(query)
    cursor = db.orders.find(query, {'order_code':1,'recipient_info':1,'current_status':1,'created_at':1}) \
                     .sort('created_at', -1) \
                     .skip((page-1)*limit).limit(limit)
    orders = []
    for o in cursor:
        o['_id'] = str(o.get('_id'))
        ri = o.get('recipient_info') or {}
        orders.append({
            '_id': o['_id'],
            'order_code': o.get('order_code'),
            'recipient_name': ri.get('name'),
            'recipient_phone': ri.get('phone'),
            'current_status': o.get('current_status'),
            'created_at': safe_datetime(o.get('created_at'))
        })

    pages = ceil(total/limit) if limit else 1
    return jsonify({'page': page, 'limit': limit, 'total': total, 'pages': pages, 'data': orders})

# --------- Delete Order ----------
@api_bp.route('/orders/<oid>', methods=['DELETE'])
def api_orders_delete(oid):
    try:
        res = db.orders.delete_one({'_id': ObjectId(oid)})
    except Exception:
        abort(400,'Invalid id')
    if res.deleted_count == 0:
        return jsonify({'deleted': False}), 404
    return jsonify({'deleted': True})
