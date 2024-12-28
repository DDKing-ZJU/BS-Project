from calendar import c
from flask import Blueprint, request, jsonify, make_response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import platform
import os
import time
import random
import json
import uuid
import requests
import subprocess
import re
import winreg
from selenium.common.exceptions import TimeoutException
import base64
from PIL import Image
import io

taobao_bp = Blueprint('taobao', __name__)

# 存储客户端会话
client_sessions = {}

# 确保JSON编码时支持中文
json.JSONEncoder.ensure_ascii = False

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

def get_qr_code():
    """获取淘宝登录二维码"""
    try:
        driver = create_chrome_driver(headless=True)  # DEBUG
        driver.get("https://login.taobao.com/member/login.jhtml")
        time.sleep(2)
        
        # 等待二维码Canvas出现
        canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
        )
        
        # 获取canvas的位置和大小
        location = canvas.location
        #size = canvas.size
        #size = 220
        size = {
            'width': 220,
            'height': 220
        }

        print(location)
        print(size)
        
        # 添加位置偏移
        offset_x = 150  # 向右偏移20像素
        offset_y = 80  # 向下偏移20像素
        
        # 截取整个页面
        png = driver.get_screenshot_as_png()
        
        # 使用PIL处理图片
        im = Image.open(io.BytesIO(png))
        
        # 计算二维码区域（添加偏移）
        left = location['x'] + offset_x
        top = location['y'] + offset_y
        right = location['x'] + size['width'] + offset_x
        bottom = location['y'] + size['height'] + offset_y
        
        # 裁剪图片
        im = im.crop((left, top, right, bottom))
        
        # 将图片转换为base64
        buffered = io.BytesIO()
        im.save(buffered, format="PNG")
        qr_base64 = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        
        # 存储driver以便后续检查登录状态
        session_id = str(uuid.uuid4())
        client_sessions[session_id] = {
            'driver': driver,
            'last_active': time.time()
        }
        
        return {
            'session_id': session_id,
            'qr_code': qr_base64
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        print(f"获取二维码失败: {str(e)}")
        raise

def check_login_status(session_id):
    # 处理弹窗
    driver = client_sessions[session_id]['driver']
    current_url = driver.current_url
    print(current_url)
    if "login.taobao.com" in current_url:
        try:
            # 等待取消按钮出现（最多等待10秒）
            cancel_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.dialog-btn.dialog-btn-feedback:not(.primary)"))
            )
            # 点击取消按钮
            cancel_button.click()
            print("成功点击取消按钮")
        except TimeoutException:
            print("没有检测到弹窗或弹窗已自动关闭")
        except Exception as e:
            print(f"处理弹窗时出错: {str(e)}")

    """检查登录状态"""
    if session_id not in client_sessions:
        return {'status': 'error', 'message': '会话不存在'}
        
    try:
        current_url = driver.current_url
        if "login.taobao.com" not in current_url:
            # 获取cookies
            cookies = driver.get_cookies()
            client_sessions[session_id]['cookies'] = cookies
            client_sessions[session_id]['last_active'] = time.time()
            driver.quit()
            del client_sessions[session_id]['driver']
            return {'status': 'success', 'message': '登录成功'}
        return {'status': 'waiting', 'message': '等待扫码'}
    except Exception as e:
        print(f"检查登录状态失败: {str(e)}")
        if driver:
            driver.quit()
        if 'driver' in client_sessions[session_id]:
            del client_sessions[session_id]['driver']
        return {'status': 'error', 'message': str(e)}

def clean_expired_sessions():
    """清理过期的会话"""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, session_data in client_sessions.items():
        # 如果会话超过30分钟没有活动，认为过期
        if current_time - session_data['last_active'] > 1800:  # 30分钟 = 1800秒
            expired_sessions.append(session_id)
    
    # 删除过期会话
    for session_id in expired_sessions:
        if 'driver' in client_sessions[session_id]:
            try:
                client_sessions[session_id]['driver'].quit()
            except:
                pass
        del client_sessions[session_id]

def update_session_activity(session_id):
    """更新会话活动时间"""
    if session_id in client_sessions:
        client_sessions[session_id]['last_active'] = time.time()

@taobao_bp.route('/get_qr_code', methods=['GET'])
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

@taobao_bp.route('/check_login', methods=['POST'])
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

@taobao_bp.route('/SetAccount', methods=['POST','OPTIONS'])
def SetAccount():
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
        
        # 将session中的cookies转移到新的client_sessions中
        if 'cookies' in client_sessions[session_id]:
            client_sessions[client_id] = {
                'cookies': client_sessions[session_id]['cookies'],
                'last_active': time.time()
            }
            # 清理旧的session
            del client_sessions[session_id]
            
            return jsonify({
                'status': 'success',
                'message': '登录成功',
                'client_id': client_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '未找到登录信息'
            }), 400
            
    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@taobao_bp.route('/search_taobao', methods=['POST', 'OPTIONS'])
def search_taobao():
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
        keyword = data.get('keyword')
        page = data.get('page', 1)
        client_id = request.headers.get('X-Client-ID')
        
        if not client_id or client_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'code': 'LOGIN_REQUIRED',
                'message': '请先登录'
            }), 401
            
        if 'cookies' not in client_sessions[client_id]:
            return jsonify({
                'status': 'error',
                'code': 'LOGIN_REQUIRED',
                'message': '请先登录'
            }), 401
            
        # 更新会话活动时间
        update_session_activity(client_id)

        # 创建Chrome驱动
        driver = create_chrome_driver(headless=False)
        try:
            # 先访问淘宝主页
            driver.get("https://www.taobao.com")
            
            # 设置cookies
            for cookie in client_sessions[client_id]['cookies']:
                driver.add_cookie(cookie)
            
            # 构建搜索URL并访问
            search_url = f"https://s.taobao.com/search?page={page}&q={keyword}&tab=all"
            driver.get(search_url)
            
            # 检查是否需要登录
            if "login.taobao.com" in driver.current_url:
                driver.quit()
                return jsonify({
                    'status': 'error',
                    'code': 'LOGIN_EXPIRED',
                    'message': '登录已过期，请重新登录'
                }), 401
            
            # 等待商品卡片加载
            wait = WebDriverWait(driver, 20)
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "doubleCardWrapperAdapt--mEcC7olq"))
            )
            
            # 缓慢滚动页面以加载图片
            last_height = driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            step = 300  # 每次滚动300像素
            
            while True:
                # 分段滚动
                current_position += step
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.3)  # 每次滚动后等待1秒
                
                # 检查是否到达底部
                if current_position >= last_height:
                    # 计算新的页面高度
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    # 如果页面变长了，继续滚动
            
            # 回到顶部，同样缓慢滚动
            while current_position > 0:
                current_position -= step
                if current_position < 0:
                    current_position = 0
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.1)
            
            # 等待图片加载完成
            wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".doubleCardWrapperAdapt--mEcC7olq img[class*='mainPic']"))
            )
            
            # 获取所有商品卡片
            cards = driver.find_elements(By.CLASS_NAME, "doubleCardWrapperAdapt--mEcC7olq")

            print(len(cards))
            items = []
            for card in cards:
                try:
                    # 打印卡片的HTML内容
                    # print("\n=== 商品卡片HTML开始 ===")
                    # print(card.get_attribute('outerHTML'))
                    # print("=== 商品卡片HTML结束 ===\n")

                    # 获取商品链接和ID
                    try:
                        link = card.get_attribute("href")
                        # 从链接中提取ID
                        if "id=" in link:
                            item_id = link.split("id=")[1].split("&")[0]
                        else:
                            # 尝试从卡片的id属性获取
                            card_id = card.get_attribute("id")
                            if card_id and "item_id_" in card_id:
                                item_id = card_id.replace("item_id_", "")
                            else:
                                item_id = None
                    except Exception as e:
                        print(f"获取商品ID出错: {str(e)}")
                        item_id = None
                        link = ""
                    
                    # 获取商品标题
                    try:
                        title_element = card.find_element(By.CSS_SELECTOR, "div[class*='title']")
                        title = title_element.text.strip()
                    except Exception as e:
                        print(f"获取标题出错: {str(e)}")
                        title = "标题未知"
                    
                    # 获取价格
                    try:
                        price_wrapper = card.find_element(By.CSS_SELECTOR, "div[class*='priceWrapper']")
                        price_text = price_wrapper.text
                        # 提取价格数字（格式可能是 "¥40.00" 或类似）
                        price = price_text.split("¥")[1].split()[0]
                    except Exception as e:
                        print(f"获取价格出错: {str(e)}")
                        price = "价格未知"
                    
                    # 获取销量
                    try:
                        sales_element = card.find_element(By.CSS_SELECTOR, "span[class*='realSales']")
                        sales = sales_element.text.replace("+人付款", "").replace("人付款", "")
                    except Exception as e:
                        print(f"获取销量出错: {str(e)}")
                        sales = "销量未知"
                    
                    # 获取店铺名称
                    try:
                        shop_name = card.find_element(By.CSS_SELECTOR, "span[class*='shopNameText']").text
                    except Exception as e:
                        print(f"获取店铺名称出错: {str(e)}")
                        shop_name = "店铺未知"
                    
                    # 获取商品图片
                    try:
                        img = card.find_element(By.CSS_SELECTOR, "img[class*='mainPic']")
                        img_url = img.get_attribute("src") or ""
                    except Exception as e:
                        print(f"获取图片出错: {str(e)}")
                        # 打印卡片的HTML内容
                        print("\n=== 商品卡片HTML开始 ===")
                        print(card.get_attribute('outerHTML'))
                        print("=== 商品卡片HTML结束 ===\n")
                        img_url = ""
                    
                    # 获取商品位置
                    try:
                        location_elements = card.find_elements(By.CSS_SELECTOR, "div[class*='procity']")
                        if location_elements:
                            location = " ".join([el.text for el in location_elements])
                        else:
                            # 尝试其他可能的位置元素
                            location_spans = card.find_elements(By.CSS_SELECTOR, "span[class*='procity']")
                            location = " ".join([el.text for el in location_spans])
                    except Exception as e:
                        print(f"获取位置出错: {str(e)}")
                        location = "位置未知"
                    
                    items.append({
                        'id': item_id,  # 添加商品ID作为主键
                        'title': title,
                        'price': price,
                        'sales': sales,
                        'shop_name': shop_name,
                        'image_url': img_url,
                        'item_url': link,
                        'location': location
                    })
                except Exception as e:
                    print(f"解析商品卡片错误: {str(e)}")
                    continue
            
            driver.quit()
            return jsonify({
                'status': 'success',
                'data': items
            })
            
        except Exception as e:
            if driver:
                driver.quit()
            raise e

    except Exception as e:
        print(f"搜索错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 保存cookies的路由
@taobao_bp.route('/save_cookies', methods=['POST', 'OPTIONS'])
def save_cookies():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Client-ID')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        data = request.get_json()
        cookies = data.get('cookies')
        client_id = request.headers.get('X-Client-ID')
        
        if not client_id or not cookies:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
            
        if client_id not in client_sessions:
            return jsonify({
                'status': 'error',
                'message': '会话不存在'
            }), 404
            
        # 保存cookies到会话
        client_sessions[client_id]['cookies'] = cookies
        client_sessions[client_id]['last_active'] = time.time()
        
        return jsonify({
            'status': 'success',
            'message': 'Cookies已保存'
        })
        
    except Exception as e:
        print(f"保存Cookies错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
