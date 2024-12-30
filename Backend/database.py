from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import re

# 在生产环境中应使用环境变量
engine_path = 'mysql+pymysql://root:123linhaibin@localhost/bs_project?charset=utf8mb4'

# 创建数据库引擎
engine = create_engine(engine_path)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # 存储哈希后的密码
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

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
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建所有表
Base.metadata.create_all(bind=engine)
