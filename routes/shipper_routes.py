from flask import Blueprint, render_template, jsonify
from pymongo.errors import PyMongoError

db = None
shipper_bp = Blueprint('shippers', __name__)

def init_mongo(mongo):
    global db
    db = mongo.db

# Trang quản lý Shippers
@shipper_bp.route('/shippers')
def shippers_page():
    try:
        shps = list(db.shippers.aggregate([
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
        ]))
    except PyMongoError as e:
        print("⚠️ Lỗi khi lấy shippers:", e)
        shps = []
    return render_template('shippers.html', shippers=shps)

# API JSON để dùng AJAX/map
@shipper_bp.route('/api/shippers/all')
def shippers_api():
    try:
        shps = list(db.shippers.aggregate([
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
        ]))
    except PyMongoError as e:
        print("⚠️ Lỗi API shippers:", e)
        shps = []
    return jsonify(shps)
