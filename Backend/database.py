from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
import re

# 加载环境变量
load_dotenv()

# 构建数据库URL
def get_database_url():
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    return "{driver}://{user}:{password}@{host}:{port}/{database}".format(
        driver=os.getenv("DB_DRIVER", "mysql+pymysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "3306"),
        database=os.getenv("DB_NAME", "bs_project")
    )

SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # 存储哈希后的密码
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    email_notifications = Column(Boolean, default=True)

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    products = relationship("Product", back_populates="platform")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    item_id = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    sales_count = Column(String(50))
    shop_name = Column(String(200))
    item_url = Column(Text, nullable=False)
    image_url = Column(Text)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    platform = relationship("Platform", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")

class TrackingItem(Base):
    __tablename__ = "tracking_items"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(50), nullable=False)
    platform = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(Text)
    url = Column(Text, nullable=False)
    shop_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    price_history = relationship("TrackingPriceHistory", backref="tracking_item", cascade="all, delete-orphan")

class TrackingPriceHistory(Base):
    __tablename__ = "tracking_price_history"

    id = Column(Integer, primary_key=True, index=True)
    tracking_item_id = Column(Integer, ForeignKey("tracking_items.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

def validate_password(password: str) -> bool:
    """验证密码是否符合要求：长度大于6位"""
    return len(password) >= 6

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> bool:
    """验证用户名是否符合要求：长度大于6位，只包含字母、数字和下划线"""
    pattern = r'^[a-zA-Z0-9_]{6,}$'
    return bool(re.match(pattern, username))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_product(db, platform_name, product_data):
    try:
        # 获取平台ID
        platform = db.query(Platform).filter(Platform.name == platform_name).first()
        if not platform:
            raise ValueError(f"Platform {platform_name} not found")

        # 检查商品是否已存在
        existing_product = db.query(Product).filter(
            Product.platform_id == platform.id,
            Product.item_id == str(product_data['item_id'])
        ).first()

        # 准备商品数据
        product_price = float(str(product_data['price']).replace('¥', '').strip())
        
        if existing_product:
            # 更新现有商品
            existing_product.title = product_data['title']
            existing_product.price = product_price
            existing_product.sales_count = str(product_data.get('sales', '0'))
            existing_product.shop_name = product_data.get('shop_name', '')
            existing_product.item_url = product_data['item_url']
            existing_product.image_url = product_data.get('image_url', '')
            existing_product.location = product_data.get('location', '')
            product = existing_product
        else:
            # 创建新商品
            product = Product(
                platform_id=platform.id,
                item_id=str(product_data['item_id']),
                title=product_data['title'],
                price=product_price,
                sales_count=str(product_data.get('sales', '0')),
                shop_name=product_data.get('shop_name', ''),
                item_url=product_data['item_url'],
                image_url=product_data.get('image_url', ''),
                location=product_data.get('location', '')
            )
            db.add(product)
        
        # 添加价格历史记录
        price_history = PriceHistory(
            product=product,
            price=product_price
        )
        db.add(price_history)
        
        db.commit()
        return product
    except Exception as e:
        db.rollback()
        raise e

# 创建所有表
Base.metadata.create_all(bind=engine)
