from flask import Blueprint, request, jsonify
from database import SessionLocal, User, TrackingItem, TrackingPriceHistory, PriceHistory
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

tracking_bp = Blueprint('tracking', __name__)

# 邮件配置
# 生产环境时进行更改
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.zju.edu.cn')
SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '3220103645@zju.edu.cn') 
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '123linhaibin')

def send_price_alert(user_email, item):
    """发送价格提醒邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = user_email
        msg['Subject'] = f'商品降价提醒 - {item.title}'

        body = f"""
        您关注的商品已降价！

        商品名称：{item.title}
        当前价格：¥{item.current_price}
        目标价格：¥{item.target_price}
        商品链接：{item.url}

        请及时查看！
        """

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

@tracking_bp.route('/items', methods=['GET', 'OPTIONS'])
def get_tracking_items():
    if request.method == 'OPTIONS':
        return '', 204
        
    """获取用户追踪的所有商品"""
    username = request.headers.get('x-client-id')
    if not username:
        return jsonify({'success': False, 'message': '未登录'}), 401

    db = SessionLocal()
    try:
        items = db.query(TrackingItem).filter_by(username=username).all()
        return jsonify({
            'success': True,
            'items': [{
                'id': item.id,
                'title': item.title,
                'current_price': item.current_price,
                'target_price': item.target_price,
                'lowest_price': item.lowest_price,
                'platform': item.platform,
                'image_url': item.image_url,
                'url': item.url,
                'price_history': [
                    {'date': h.date.strftime('%Y-%m-%d'), 'price': h.price}
                    for h in item.price_history
                ]
            } for item in items]
        })
    finally:
        db.close()

@tracking_bp.route('/add', methods=['POST', 'OPTIONS'])
def add_tracking():
    """添加追踪商品"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        print("Received data:", data)  # 打印接收到的数据
        
        db = SessionLocal()
        
        # 检查是否已经存在相同的商品
        existing_item = db.query(TrackingItem).filter_by(
            item_id=data['item_id'],
            platform=data['platform']
        ).first()
        
        if existing_item:
            return jsonify({'message': '该商品已在追踪列表中'}), 400
            
        # 创建新的追踪项
        new_item = TrackingItem(
            item_id=str(data['item_id']),  # 确保转换为字符串
            platform=data['platform'],
            title=data['title'],
            current_price=float(data['current_price']),  # 确保转换为浮点数
            image_url=data['image_url'],
            url=data['item_url'],
            shop_name=data.get('shop_name', '')  # 使用 get 方法，提供默认值
        )
        
        db.add(new_item)
        db.commit()
        
        return jsonify({'message': '添加成功', 'item': {
            'id': new_item.id,
            'item_id': new_item.item_id,
            'platform': new_item.platform,
            'title': new_item.title,
            'current_price': float(new_item.current_price)
        }}), 200
    except KeyError as e:
        print(f"Missing required field: {str(e)}")  # 打印缺失的字段
        return jsonify({'error': f'缺少必要字段: {str(e)}'}), 400
    except ValueError as e:
        print(f"Value error: {str(e)}")  # 打印值错误
        return jsonify({'error': f'数据格式错误: {str(e)}'}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # 打印意外错误
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@tracking_bp.route('/<platform>/<item_id>', methods=['DELETE', 'OPTIONS'])
def delete_tracking(platform, item_id):
    """删除追踪商品"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        db = SessionLocal()
        # 查找匹配的商品
        item = db.query(TrackingItem).filter_by(
            platform=platform,
            item_id=item_id
        ).first()
        
        if not item:
            return jsonify({'error': '未找到该商品'}), 404
            
        db.delete(item)
        db.commit()
        
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@tracking_bp.route('/list', methods=['GET', 'OPTIONS'])
def get_tracking_list():
    """获取用户的追踪列表"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        db = SessionLocal()
        tracking_items = db.query(TrackingItem).all()
        
        items_list = []
        for item in tracking_items:
            items_list.append({
                'item_id': item.item_id,
                'platform': item.platform,
                'title': item.title,
                'current_price': float(item.current_price),
                'image_url': item.image_url,
                'item_url': item.url,
                'shop_name': item.shop_name
            })
        
        return jsonify(items_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@tracking_bp.route('/target-price/<int:item_id>', methods=['PUT', 'OPTIONS'])
def update_target_price(item_id):
    """更新目标价格"""
    if request.method == 'OPTIONS':
        return '', 204
        
    username = request.headers.get('x-client-id')
    if not username:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    db = SessionLocal()
    try:
        item = db.query(TrackingItem).filter_by(
            id=item_id,
            username=username
        ).first()
        
        if not item:
            return jsonify({
                'success': False,
                'message': '商品不存在'
            }), 404

        item.target_price = data['target_price']
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
    finally:
        db.close()

@tracking_bp.route('/email', methods=['POST', 'OPTIONS'])
def update_email():
    """更新用户邮箱"""
    if request.method == 'OPTIONS':
        return '', 204
        
    username = request.headers.get('x-client-id')
    if not username:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        user.email = data['email']
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
    finally:
        db.close()

def check_prices():
    """检查所有追踪商品的价格并发送提醒"""
    db = SessionLocal()
    try:
        items = db.query(TrackingItem).all()
        for item in items:
            # 获取当前价格
            new_price = get_current_price(item)
            if new_price is None:
                continue
                
            # 更新商品价格
            item.current_price = new_price
            
            # 添加价格历史记录
            history = TrackingPriceHistory(
                tracking_item_id=item.id,
                price=new_price,
                date=datetime.now()
            )
            db.add(history)
            
        db.commit()
    except Exception as e:
        print(f"Error in check_prices: {str(e)}")
        db.rollback()
    finally:
        db.close()

def get_current_price(item):
    """获取商品当前价格"""
    # 这里需要根据不同平台实现具体的价格获取逻辑
    # 可以调用淘宝和京东的相关接口
    pass
