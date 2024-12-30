from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import bcrypt
import jwt
from typing import Optional

from database import get_db, User, validate_password, validate_email, validate_username

router = APIRouter()

# JWT配置
SECRET_KEY = "your-secret-key"  # 在生产环境中应该使用环境变量
ALGORITHM = "HS256"

def create_jwt_token(user_id: int) -> str:
    """创建JWT令牌"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)  # 令牌1天后过期
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/register")
async def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    """用户注册"""
    # 验证输入
    if not validate_username(username):
        raise HTTPException(
            status_code=400,
            detail="用户名必须至少6位，只能包含字母、数字和下划线"
        )
    
    if not validate_email(email):
        raise HTTPException(
            status_code=400,
            detail="邮箱格式不正确"
        )
    
    if not validate_password(password):
        raise HTTPException(
            status_code=400,
            detail="密码必须至少6位"
        )
    
    try:
        # 创建新用户
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 创建JWT令牌
        token = create_jwt_token(new_user.id)
        
        return {
            "status": "success",
            "message": "注册成功",
            "token": token
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="用户名或邮箱已存在"
        )

@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 创建JWT令牌
    token = create_jwt_token(user.id)
    
    return {
        "status": "success",
        "message": "登录成功",
        "token": token
    }

@router.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """验证令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="无效的认证凭据"
            )
        return {"status": "success", "user": user.username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="认证凭据已过期"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="无效的认证凭据"
        )
