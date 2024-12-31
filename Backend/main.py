from flask import Blueprint, Flask, request
from flask_cors import CORS
from taobao import taobao_bp
from jd import jd_bp
from item import item_bp
from tracking import tracking_bp
import auth
from scheduler import start_scheduler
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取端口配置
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '0.0.0.0')

app = Flask(__name__)

@app.before_request
def log_request_info():
    print('请求头:', dict(request.headers))
    print('请求方法:', request.method)
    print('请求URL:', request.url)

# 配置CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "x-client-id"],
        "supports_credentials": True
    }
})

# 注册蓝图
app.register_blueprint(taobao_bp, url_prefix='/api/taobao')
app.register_blueprint(jd_bp, url_prefix='/api/jd')
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(item_bp, url_prefix='/api/item')
app.register_blueprint(tracking_bp, url_prefix='/api/tracking')

if __name__ == '__main__':
    print("启动服务器，监听端口{}...".format(PORT))
    start_scheduler()  # 启动价格检查调度器
    app.run(debug=True, port=PORT, host=HOST)