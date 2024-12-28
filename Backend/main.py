from flask import Blueprint, Flask, request
from flask_cors import CORS
from taobao import taobao_bp
from jd import jd_bp

app = Flask(__name__)

@app.before_request
def log_request_info():
    print('请求头:', dict(request.headers))
    print('请求方法:', request.method)
    print('请求URL:', request.url)

# 配置CORS
CORS(app, 
     origins="http://localhost:8080",
     allow_headers=["Content-Type", "X-Client-ID"],
     supports_credentials=True)

# 注册蓝图
app.register_blueprint(taobao_bp, url_prefix='/api/taobao')
app.register_blueprint(jd_bp, url_prefix='/api/jd')

if __name__ == '__main__':
    print("启动服务器，监听端口5000...")
    app.run(debug=True, port=5000, host='0.0.0.0')