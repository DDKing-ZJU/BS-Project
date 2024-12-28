from flask import Blueprint, request, jsonify, make_response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import base64
import time
import json
import os
import platform
from datetime import datetime, timedelta
import uuid

# 创建蓝图
jd_bp = Blueprint('jd', __name__)

# 存储用户会话信息
client_sessions = {}

# 会话过期时间（分钟）
SESSION_EXPIRY_MINUTES = 30

def create_chrome_driver(headless=False):
    """创建Chrome驱动"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        # 首先尝试自动安装并使用ChromeDriver
        manager = ChromeDriverManager()
        driver_path = manager.install()
        service = ChromeService(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("成功使用自动安装的ChromeDriver")
        return driver
    except Exception as e:
        print(f"自动安装ChromeDriver失败: {str(e)}")
        
        # 尝试使用本地ChromeDriver
        try:
            print("尝试使用本地ChromeDriver...")
            if platform.system() == 'Windows':
                driver_path = "./chromedriver.exe"
            else:
                driver_path = "./chromedriver"
            
            if not os.path.exists(driver_path):
                print(f"本地ChromeDriver不存在于路径: {driver_path}")
                # 尝试在当前文件所在目录查找
                current_dir = os.path.dirname(os.path.abspath(__file__))
                driver_path = os.path.join(current_dir, "chromedriver.exe" if platform.system() == 'Windows' else "chromedriver")
                
                if not os.path.exists(driver_path):
                    raise Exception(f"未找到ChromeDriver: {driver_path}")
            
            print(f"使用本地ChromeDriver: {driver_path}")
            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("成功使用本地ChromeDriver")
            return driver
            
        except Exception as local_error:
            print(f"使用本地ChromeDriver失败: {str(local_error)}")
            error_message = (
                "无法初始化Chrome浏览器。请确保：\n"
                "1. 已安装Chrome浏览器\n"
                "2. ChromeDriver存在且版本匹配\n"
                "3. ChromeDriver有执行权限\n"
                "4. 在Linux上已安装必要的依赖"
            )
            raise Exception(error_message) from local_error

def clean_expired_sessions():
    """清理过期的会话"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in client_sessions.items():
        last_activity = session_data.get('last_activity')
        if last_activity and (current_time - last_activity) > timedelta(minutes=SESSION_EXPIRY_MINUTES):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del client_sessions[session_id]

def update_session_activity(session_id):
    """更新会话活动时间"""
    if session_id in client_sessions:
        client_sessions[session_id]['last_activity'] = datetime.now()

@jd_bp.route('/get_qr_code', methods=['POST', 'OPTIONS'])
def get_qr_code():
    """获取京东登录二维码"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Client-ID')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        # 清理过期会话
        clean_expired_sessions()
        
        data = request.get_json()
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({
                'status': 'error',
                'message': '缺少客户端ID'
            }), 400
        
        # 创建新的Chrome驱动
        driver = create_chrome_driver(headless=False)
        
        try:
            # 访问京东登录页面
            driver.get('https://passport.jd.com/new/login.aspx')
            
            # 等待二维码图片加载
            wait = WebDriverWait(driver, 10)
            qr_img = wait.until(
                EC.presence_of_element_located((By.ID, 'passport-main-qrcode-img'))
            )
            
            # 获取二维码图片的src属性并处理
            qr_code_url = qr_img.get_attribute('src')
            if qr_code_url.startswith('//'):
                qr_code_url = 'https:' + qr_code_url
            
            # 存储会话信息
            client_sessions[client_id] = {
                'driver': driver,
                'last_activity': datetime.now()
            }
            
            return jsonify({
                'status': 'success',
                'qr_code_url': qr_code_url
            })
            
        except Exception as e:
            driver.quit()
            raise e
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@jd_bp.route('/check_login', methods=['POST', 'OPTIONS'])
def check_login():
    """检查京东登录状态"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Client-ID')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        data = request.get_json()
        client_id = data.get('client_id')
        
        if not client_id or client_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'message': '无效的会话'
            }), 401
        
        session = client_sessions[client_id]
        driver = session['driver']
        
        try:
            # 检查是否已登录（通过检查URL是否已重定向）
            current_url = driver.current_url
            if 'passport.jd.com/new/login.aspx' not in current_url:
                # 获取cookies
                cookies = driver.get_cookies()
                client_sessions[client_id]['cookies'] = cookies
                
                # 更新会话活动时间
                update_session_activity(client_id)
                
                return jsonify({
                    'status': 'success',
                    'logged_in': True
                })
            
            # 更新会话活动时间
            update_session_activity(client_id)
            
            return jsonify({
                'status': 'success',
                'logged_in': False
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@jd_bp.route('/SetAccount', methods=['POST', 'OPTIONS'])
def SetAccount():
    """设置用户账号，转移session到新的client_id"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Client-ID')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = data.get('session_id')
        
        if not session_id or session_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'message': '无效的会话ID'
            }), 400
            
        # 创建新的客户端ID
        client_id = str(uuid.uuid4())
        
        # 获取当前session的driver
        driver = client_sessions[session_id]['driver']
        
        # 获取所有cookies
        cookies = driver.get_cookies()
        
        # 将cookies和其他信息转移到新的client_sessions中
        client_sessions[client_id] = {
            'cookies': cookies,
            'last_activity': datetime.now()
        }
        
        # 关闭并清理旧的session的driver
        try:
            driver.quit()
        except:
            pass
        del client_sessions[session_id]
        
        return jsonify({
            'status': 'success',
            'message': '登录成功',
            'client_id': client_id
        })
            
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
