import datetime
from flask import Flask
from flask_pymongo import PyMongo
import os
from pymongo.errors import ServerSelectionTimeoutError

# --- IMPORT BLUEPRINTS & INIT FUNCTIONS ---
from routes.main_routes import main_bp, init_mongo as main_init
from routes.order_routes import order_bp, init_mongo as order_init
from routes.postoffice_routes import postoffice_bp, init_mongo as postoffice_init
from routes.shipper_routes import shipper_bp, init_mongo as shipper_init
from routes.api_routes import api_bp, init_mongo as api_init


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/ViettelPost_DB')
def safe_strftime(value, fmt="%Y-%m-%d %H:%M"):
    if isinstance(value, datetime.datetime):
        return value.strftime(fmt)
    elif isinstance(value, str):
        try:
            dt = datetime.datetime.fromisoformat(value)
            return dt.strftime(fmt)
        except:
            return value  
    return ""  

app.jinja_env.filters['strftime'] = safe_strftime

# Khởi tạo MongoDB
mongo = PyMongo(app)

# --- INIT DB CHO CÁC MODULE ---
with app.app_context():
    for init_func in [main_init, order_init, postoffice_init, shipper_init, api_init]:
        init_func(mongo)

# --- REGISTER BLUEPRINT ---
app.register_blueprint(main_bp)
app.register_blueprint(order_bp)
app.register_blueprint(postoffice_bp)
app.register_blueprint(shipper_bp)
app.register_blueprint(api_bp)

# Thêm filter Jinja2 cho datetime
# --- KIỂM TRA KẾT NỐI ---
with app.app_context():
    try:
        count = mongo.db.orders.count_documents({})
        print(f"✅ Kết nối MongoDB thành công! Tổng đơn hàng: {count}")
    except ServerSelectionTimeoutError:
        print("⚠️ Không kết nối được MongoDB!")
    except Exception as e:
        print(f"⚠️ Lỗi khởi động: {e}")

if __name__ == '__main__':
    # Chạy app Flask thông thường
    app.run(debug=True, host='0.0.0.0', port=5000)
