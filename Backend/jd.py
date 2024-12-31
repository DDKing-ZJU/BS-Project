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
from database import SessionLocal, save_product

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
    
    # 如果已经获取到cookies，说明已经登录成功
    if 'cookies' in client_sessions[session_id]:
        return {
            'status': 'success',
            'message': '登录成功'
        }
    
    try:
        # 获取当前session的driver
        if 'driver' not in client_sessions[session_id]:
            return {
                'status': 'error',
                'message': '登录会话已失效'
            }
            
        driver = client_sessions[session_id]['driver']
        
        # 检查driver是否还在运行
        try:
            # 尝试执行一个简单的命令来检查driver是否还活着
            driver.current_window_handle
        except Exception as e:
            print(f"Driver已关闭或无效: {str(e)}")
            if session_id in client_sessions:
                if 'driver' in client_sessions[session_id]:
                    del client_sessions[session_id]['driver']
            return {
                'status': 'error',
                'message': '登录会话已失效'
            }
    
        # 添加重试机制获取URL
        max_retries = 3
        retry_count = 0
        current_url = None
        
        while retry_count < max_retries:
            try:
                current_url = driver.current_url
                break
            except Exception as url_error:
                retry_count += 1
                if retry_count == max_retries:
                    raise url_error
                print(f"获取URL失败，正在重试 ({retry_count}/{max_retries})")
                time.sleep(2)  # 等待2秒后重试
        
        if 'passport.jd.com/new/login.aspx' not in current_url:
            # 获取cookies
            cookies = driver.get_cookies()
            client_sessions[session_id]['cookies'] = cookies
            
            # 更新会话活动时间
            update_session_activity(session_id)

            # 关闭Chrome驱动
            try:
                driver.quit()
            except:
                pass
            if 'driver' in client_sessions[session_id]:
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
        return {
            'status': 'error',
            'message': '检查登录状态时出错'
        }

# 创建一个client_id，转移cookies，更新会话活动时间
def set_account(session_id):

    client_id = str(uuid.uuid4())
    # 将session中的cookies转移到新的client_sessions中
    if 'cookies' in client_sessions[session_id]:
        client_sessions[client_id] = {
            'cookies': client_sessions[session_id]['cookies'],
        }
        # del client_sessions[session_id]
    
        # 更新会话活动时间
        update_session_activity(client_id)
        
        return {
            'status': 'success',
            'message': '登录成功',
            'client_id': client_id
        }
    
    else:
        raise Exception("未找到cookies")

def search(client_id, page, keyword):
    try:
        # 获取cookies
        cookies = client_sessions[client_id]['cookies']
        
        # 计算实际的京东页码
        # 京东的页码逻辑：
        # page = 1,2 显示第1页
        # page = 3,4 显示第2页
        # 所以实际页码 = (page + 1) // 2
        jd_page = (page * 2) - 1
        
        # 创建新的Chrome驱动
        driver = create_chrome_driver(headless=False)
        
        try:
            # 设置cookies
            driver.get("https://www.jd.com")  # 先访问京东主页，然后设置cookies
            for cookie in cookies:
                driver.add_cookie(cookie)
            
            # 构建搜索URL
            search_url = f"https://search.jd.com/Search?keyword={keyword}&page={jd_page}"
            driver.get(search_url)
            
            # 等待搜索结果加载
            wait = WebDriverWait(driver, 10)

            # 在这里添加一个向下缓慢滚动加载的逻辑
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
            
            goods_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gl-warp')))
            
            # 获取搜索结果
            items = goods_list.find_elements(By.CLASS_NAME, 'gl-item')
            results = []
            
            for item in items:
                try:
                    # 获取商品信息
                    sku = item.get_attribute('data-sku')  # 获取商品ID
                    price_element = item.find_element(By.CSS_SELECTOR, '.p-price strong i')
                    title_element = item.find_element(By.CSS_SELECTOR, '.p-name em')
                    shop_element = item.find_element(By.CSS_SELECTOR, '.p-shop')
                    link_element = item.find_element(By.CSS_SELECTOR, '.p-img a')
                    img_element = item.find_element(By.CSS_SELECTOR, '.p-img img')
                    
                    # 处理图片URL，避免双重https://
                    img_url = img_element.get_attribute('src') or img_element.get_attribute('data-lazy-img')
                    # print(img_url)
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif not img_url.startswith('http'):
                        img_url = 'https://' + img_url
                    
                    # 获取商品评价数（销量）
                    try:
                        commit_element = item.find_element(By.CSS_SELECTOR, '.p-commit strong a')
                        # DEBUG
                        # print(commit_element.text)
                        # 直接获取评价数文本并处理
                        sales = commit_element.text.split('条评价')[0].strip()
                    except:
                        sales = "0"
                    
                    # 获取商品产地
                    try:
                        stock_element = item.find_element(By.CSS_SELECTOR, '.p-stock')
                        location = stock_element.get_attribute('data-province')
                    except:
                        location = "未知"
                    
                    # 构建结果
                    result = {
                        'id': 'jd' + str(sku),
                        'title': title_element.text,
                        'price': price_element.text,
                        'sales': sales,
                        'shop_name': shop_element.text,
                        'item_url': 'https:' + link_element.get_attribute('href') if not link_element.get_attribute('href').startswith('http') else link_element.get_attribute('href'),
                        'image_url': img_url,
                        'location': location
                    }
                    results.append(result)
                except Exception as e:
                    print(f"处理商品时出错: {str(e)}")
                    continue
            
            return {
                'status': 'success',
                'results': results,
                'page': page,
                'jd_page': jd_page
            }
            
        finally:
            driver.quit()
        
    except Exception as e:
        print(f"搜索时出错: {str(e)}")
        raise e

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
                'code': 'LOGIN_REQUIRED',
                'message': '请先登录'
            }), 401

        update_session_activity(client_id)

        # 创建数据库会话
        db = SessionLocal()

        try:
            # 调用搜索函数
            result = search(client_id, page, keyword)
            
            # 保存商品信息到数据库
            if result.get('status') == 'success' and 'results' in result:
                for item in result['results']:
                    try:
                        item_data = {
                            'item_id': item['id'],
                            'title': item['title'],
                            'price': float(item['price'].replace('¥', '')),
                            'image_url': item['image_url'],
                            'item_url': item['item_url'],
                            'shop_name': item.get('shop_name', ''),
                            'sales': item.get('sales', 0),
                            'location': item.get('location', '')
                        }
                        save_product(db, 'jd', item_data)
                    except Exception as e:
                        print(f"保存商品信息时出错: {str(e)}")
                        continue

            return jsonify(result)

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
        finally:
            db.close()

    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500