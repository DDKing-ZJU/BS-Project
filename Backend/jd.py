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
from PIL import Image
from io import BytesIO

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

def get_qr_code():
    """获取京东登录二维码"""
    try:
        # 创建新的Chrome驱动
        driver = create_chrome_driver(headless=False)
        
        # 访问京东登录页面
        driver.get('https://passport.jd.com/new/login.aspx')
    
        # 等待二维码图片加载
        wait = WebDriverWait(driver, 10)
        qr_img = wait.until(
            EC.presence_of_element_located((By.ID, 'passport-main-qrcode-img'))
        )
        
        # 获取二维码元素的位置和大小
        location = qr_img.location
        # size = qr_img.size
        size = {
            'width': 240,
            'height': 240
        }

        offset_x = 280  # 向右偏移20像素
        offset_y = 100  # 向下偏移20像素

        # 截取二维码图片
        png = driver.get_screenshot_as_png()
        im = Image.open(BytesIO(png))
        
        # 因为是无头模式，不需要考虑DPI缩放
        left = location['x'] + offset_x
        top = location['y'] + offset_y
        right = location['x'] + size['width'] + offset_x
        bottom = location['y'] + size['height'] + offset_y
        
        # 裁剪图片
        im = im.crop((left, top, right, bottom))
        
        # 将图片转换为base64
        buffered = BytesIO()
        im.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"
    
        # 存储会话信息
        session_id = str(uuid.uuid4())
        client_sessions[session_id] = {
            'driver': driver,
            'last_activity': datetime.now()
        }
    
        return {
            'session_id': session_id,
            'qr_code_url': qr_code_url
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        print(f"获取二维码时出错: {str(e)}")
        raise e

def check_login_status(session_id):
    """检查会话状态"""
    if session_id not in client_sessions:
        return {
            'status': 'error',
            'message': '会话不存在'
        }
    
    try:
        # 获取当前session的driver
        driver = client_sessions[session_id]['driver']
    
        # 检查是否已登录（通过检查URL是否已重定向）
        current_url = driver.current_url
        if 'passport.jd.com/new/login.aspx' not in current_url:
            # 获取cookies
            cookies = driver.get_cookies()
            client_sessions[session_id]['cookies'] = cookies
            
            # 更新会话活动时间
            update_session_activity(session_id)

            # 关闭Chrome驱动
            driver.quit()
            del client_sessions[session_id]['driver']
        
            return {
                'status': 'success',
                'message': '登录成功'
            }

        return {
            'status': 'waiting',
            'message': '等待扫码'
        }
        
    except Exception as e:
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        if session_id in client_sessions and 'driver' in client_sessions[session_id]:
            del client_sessions[session_id]['driver']
        print(f"检查登录状态时出错: {str(e)}")
        raise e

# 创建一个client_id，转移cookies，更新会话活动时间
def set_account(session_id):

    client_id = str(uuid.uuid4())
    # 将session中的cookies转移到新的client_sessions中
    if 'cookies' in client_sessions[session_id]:
        client_sessions[client_id] = {
            'cookies': client_sessions[session_id]['cookies'],
        }
        del client_sessions[session_id]
    
        # 更新会话活动时间
        update_session_activity(client_id)
        
        return {
            'status': 'success',
            'message': '登录成功',
            'client_id': client_id
        }
    
    else:
        raise Exception("未找到cookies")

@jd_bp.route('/get_qr_code', methods=['GET'])
def get_qr_code_route():
    try:
        result = get_qr_code()
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@jd_bp.route('/check_login', methods=['POST'])
def check_login_route():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({
                'status': 'error',
                'message': '缺少session_id'
            }), 400
            
        result = check_login_status(session_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@jd_bp.route('/SetAccount', methods=['POST'])
def set_account_route():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'message': '缺少session_id'
            }), 400
            
        # 此处我们要根据会话创建一个client_id，转移cookies，更新会话活动时间
        result = set_account(session_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@jd_bp.route('/search', methods=['POST'])
def search_route():
    try:

        clean_expired_sessions()

        data = request.get_json()
        keyword = data.get('keyword')
        page = data.get('page', 1)
        client_id = request.headers.get('X-Client-ID')
        
        if not client_id or client_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'code' : 'LOGIN_REQUIRED',
                'message': '缺少client_id'
            }), 401
        
        if 'cookies' not in client_sessions[client_id]:
            return jsonify({
                'status': 'error',
                'code' : 'LOGIN_REQUIRED',
                'message': '缺少cookies'
            }), 401

        update_session_activity(client_id)
            
        result = search(client_id, page, keyword)
        return jsonify(result)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)    
        }), 500