import datetime
from flask import Blueprint, render_template, request, jsonify
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId

main_bp = Blueprint('main', __name__)
db = None

def init_mongo(mongo):
    global db
    db = mongo.db

# --- Dashboard ---
@main_bp.route('/')
def index():
    total_orders = 0
    orders_by_status = []
    cod_total = 0
    recent_orders = []

    # Tổng đơn hàng
    try:
        total_orders = db.orders.count_documents({})
    except PyMongoError as e:
        print("⚠️ Lỗi đếm tổng đơn:", e)

    # Thống kê trạng thái
    try:
        orders_by_status = list(db.orders.aggregate([
            {'$group': {'_id': '$current_status', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))
    except PyMongoError as e:
        print("⚠️ Lỗi tổng hợp trạng thái:", e)

    # Tổng COD
    try:
        cod_cursor = db.transactions.aggregate([
            {'$match': {'transaction_type': 'COD_COLLECTION', 'status': 'COMPLETED'}},
            {'$group': {'_id': None, 'total_cod': {'$sum': '$amount'}}}
        ])
        cod_total = next(cod_cursor, {}).get('total_cod', 0) or 0
        cod_total = float(cod_total)
    except (PyMongoError, ValueError, TypeError) as e:
        print("⚠️ Lỗi tính tổng COD:", e)
        cod_total = 0

    # 10 đơn gần nhất
    try:
        recent_orders = list(db.orders.find().sort('created_at', -1).limit(10))
        # Convert ObjectId và datetime để template render dễ
        for o in recent_orders:
            o['_id'] = str(o.get('_id'))

            if isinstance(o.get('created_at'), datetime.datetime):
                o['created_at_str'] = o['created_at'].strftime('%Y-%m-%d %H:%M')
            else:
                o['created_at_str'] = ''
    except PyMongoError as e:
        print("⚠️ Lỗi lấy đơn gần nhất:", e)

    return render_template(
        'index.html',
        total_orders=total_orders,
        orders_by_status=orders_by_status,
        cod_total=cod_total,
        recent_orders=recent_orders
    )

# --- Track order ---
@main_bp.route('/track')
def track_form():
    code = request.args.get('code')
    order, shipment = None, None
    if code:
        try:
            order = db.orders.find_one({'order_code': code})
            shipment = db.shipments.find_one({'tracking_code': code})
            # Convert _id và datetime
            if order:
                order['_id'] = str(order['_id'])
                if 'created_at' in order:
                    order['created_at'] = order['created_at'].isoformat()
            if shipment:
                shipment['_id'] = str(shipment['_id'])
        except PyMongoError as e:
            print(f"⚠️ Lỗi truy vấn tracking code {code}:", e)
    return render_template('track.html', order=order, shipment=shipment, code=code)

# --- API cho post offices ---
@main_bp.route('/api/postoffices/all')
def postoffices_api():
    try:
        # Query trực tiếp MongoDB, trả về dữ liệu thuần
        offices = list(db.post_offices.find({}, {"_id":0}))
        return jsonify(offices)
    except PyMongoError as e:
        print("⚠️ Lỗi fetch post offices:", e)
        return jsonify([])

# --- API cho shippers active ---
@main_bp.route('/api/shippers/active')
def shippers_active_api():
    try:
        shps = list(db.shippers.find({'status': {'$in': ['ON_DUTY','ACTIVE']}}))
        result = []
        for s in shps:
            po_name = None
            po_id = s.get('current_post_office_id')
            if po_id:
                po = db.post_offices.find_one({'_id': po_id}, {'name':1})
                if po:
                    po_name = po.get('name')
            result.append({
                'shipper_code': s.get('shipper_code'),
                'full_name': s.get('full_name'),
                'phone_number': s.get('phone_number'),
                'current_post_office_name': po_name,
                'status': s.get('status')
            })
        return jsonify(result)
    except PyMongoError as e:
        print("⚠️ Lỗi fetch shippers:", e)
        return jsonify([])
