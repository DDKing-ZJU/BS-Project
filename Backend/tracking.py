from flask import Blueprint, request, jsonify
from database import SessionLocal, User, TrackingItem, PriceHistory
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

@tracking_bp.route('/items', methods=['GET'])
def get_tracking_items():
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

@tracking_bp.route('/items', methods=['POST'])
def add_tracking_item():
    """添加追踪商品"""
    username = request.headers.get('x-client-id')
    if not username:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    db = SessionLocal()
    try:
        # 检查是否已经在追踪
        existing = db.query(TrackingItem).filter_by(
            username=username,
            url=data['url']
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': '该商品已在追踪列表中'
            }), 400

        item = TrackingItem(
            username=username,
            title=data['title'],
            current_price=data['price'],
            target_price=data['target_price'],
            lowest_price=data['price'],
            platform=data['platform'],
            image_url=data['image_url'],
            url=data['url']
        )
        
        # 添加初始价格历史
        history = PriceHistory(
            price=data['price'],
            date=datetime.now()
        )
        item.price_history.append(history)
        
        db.add(item)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '添加成功',
            'item_id': item.id
        })
    finally:
        db.close()

@tracking_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_tracking_item(item_id):
    """删除追踪商品"""
    username = request.headers.get('x-client-id')
    if not username:
        return jsonify({'success': False, 'message': '未登录'}), 401

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

        db.delete(item)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    finally:
        db.close()

@tracking_bp.route('/target-price/<int:item_id>', methods=['PUT'])
def update_target_price(item_id):
    """更新目标价格"""
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

@tracking_bp.route('/email', methods=['POST'])
def update_email():
    """更新用户邮箱"""
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
            # 获取最新价格（这里需要实现具体的价格获取逻辑）
            new_price = get_current_price(item)
            
            # 更新价格历史
            history = PriceHistory(
                item_id=item.id,
                price=new_price,
                date=datetime.now()
            )
            db.add(history)
            
            # 更新商品当前价格和最低价
            item.current_price = new_price
            if new_price < item.lowest_price:
                item.lowest_price = new_price
            
            # 如果价格低于目标价格，发送提醒
            if new_price <= item.target_price:
                user = db.query(User).filter_by(username=item.username).first()
                if user and user.email:
                    send_price_alert(user.email, item)
        
        db.commit()
    finally:
        db.close()

def get_current_price(item):
    """获取商品当前价格"""
    # 这里需要根据不同平台实现具体的价格获取逻辑
    # 可以调用淘宝和京东的相关接口
    pass
