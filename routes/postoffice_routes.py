from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId

postoffice_bp = Blueprint('postoffices', __name__)
db = None

def init_mongo(mongo):
    global db
    db = mongo.db

# --- Helper: Xây dựng object Post Office từ Form Data ---
def build_office_data(data):
    try:
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
    except ValueError:
        lat, lng = 0.0, 0.0

    return {
        "office_code": data.get('office_code', '').upper(),
        "name": data.get('name', ''),
        "phone_number": data.get('phone_number', ''),
        "operating_hours": data.get('operating_hours', ''),
        "address": {
            "street": data.get('street', ''),
            "ward": data.get('ward', ''),
            "district": data.get('district', ''),
            "province": data.get('province', '')
        },
        # Cấu trúc GeoJSON chuẩn cho MongoDB
        "location": {
            "type": "Point",
            "coordinates": [lng, lat] # MongoDB lưu [Longitude, Latitude]
        }
    }

# --- 1. Trang danh sách (READ) ---
@postoffice_bp.route('/postoffices')
def postoffices_page():
    try:
        # Lấy tất cả bưu cục
        offices = list(db.post_offices.find())
        # Convert ObjectId sang string để dùng trong template
        for o in offices:
            o['_id'] = str(o['_id'])
    except PyMongoError as e:
        print("⚠️ Lỗi DB:", e)
        offices = []
    return render_template('postoffices.html', offices=offices)

# --- 2. API Trả về JSON (Cho Map) ---
@postoffice_bp.route('/api/postoffices/all')
def postoffices_api():
    try:
        offices = list(db.post_offices.find({}, {"_id": 0}))
    except PyMongoError:
        offices = []
    return jsonify(offices)

# --- 3. Tạo mới (CREATE) ---
@postoffice_bp.route('/postoffices/create', methods=['POST'])
def postoffice_create():
    try:
        data = request.form.to_dict()
        new_office = build_office_data(data)
        
        # Kiểm tra trùng mã (Optional)
        existing = db.post_offices.find_one({"office_code": new_office['office_code']})
        if existing:
            flash(f"Mã bưu cục {new_office['office_code']} đã tồn tại!", "warning")
            return redirect(url_for('postoffices.postoffices_page'))

        db.post_offices.insert_one(new_office)
        flash("Thêm bưu cục thành công!", "success")
    except Exception as e:
        flash(f"Lỗi: {str(e)}", "danger")
    
    return redirect(url_for('postoffices.postoffices_page'))

# --- 4. Cập nhật (UPDATE) ---
@postoffice_bp.route('/postoffices/update', methods=['POST'])
def postoffice_update():
    try:
        data = request.form.to_dict()
        oid = data.get('oid')
        
        if not oid:
            flash("Thiếu ID bưu cục", "danger")
            return redirect(url_for('postoffices.postoffices_page'))

        updated_data = build_office_data(data)
        
        # Update, giữ lại _id
        db.post_offices.update_one(
            {'_id': ObjectId(oid)},
            {'$set': updated_data}
        )
        flash("Cập nhật thành công!", "success")
    except Exception as e:
        flash(f"Lỗi cập nhật: {str(e)}", "danger")

    return redirect(url_for('postoffices.postoffices_page'))

# --- 5. Xóa (DELETE) ---
@postoffice_bp.route('/postoffices/delete/<oid>', methods=['POST'])
def postoffice_delete(oid):
    try:
        db.post_offices.delete_one({'_id': ObjectId(oid)})
        flash("Đã xóa bưu cục", "success")
    except Exception as e:
        flash(f"Lỗi xóa: {str(e)}", "danger")
        
    return redirect(url_for('postoffices.postoffices_page'))