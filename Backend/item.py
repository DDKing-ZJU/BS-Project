from flask import Blueprint, jsonify
from database import get_db, Platform, Product, PriceHistory
from sqlalchemy import desc

item_bp = Blueprint('item', __name__)

@item_bp.route('/price-history/<platform>/<item_id>', methods=['GET'])
def get_price_history(platform, item_id):
    try:
        db = next(get_db())
        
        # 获取平台ID
        platform_obj = db.query(Platform).filter(Platform.name == platform).first()
        if not platform_obj:
            return jsonify({"error": "Platform not found"}), 404
            
        # 先找到对应的商品
        product = db.query(Product).filter(
            Product.platform_id == platform_obj.id,
            Product.item_id == item_id
        ).first()
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        # 然后查询这个商品的价格历史记录
        price_history = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id
        ).order_by(PriceHistory.recorded_at.asc()).all()
        
        if not price_history:
            return jsonify({"error": "No price history found"}), 404
            
        # 格式化数据用于图表显示
        price_history_data = [
            {
                'date': record.recorded_at.strftime('%Y-%m-%d'),
                'price': float(record.price)
            }
            for record in price_history
        ]
        
        # 按日期分组，如果同一天有多条记录，取最新的一条
        price_dict = {}
        for record in price_history_data:
            price_dict[record['date']] = record['price']
        
        dates = list(price_dict.keys())
        prices = list(price_dict.values())
        
        return jsonify({
            "dates": dates,
            "prices": prices
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
