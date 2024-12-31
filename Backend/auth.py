from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from database import get_db, User, validate_password, validate_email, validate_username

# 加载环境变量
load_dotenv()

bp = Blueprint('auth', __name__)

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

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

@bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 验证输入
    if not validate_username(username):
        return jsonify({
            "status": "error",
            "detail": "用户名必须至少6位，只能包含字母、数字和下划线"
        }), 400
    
    if not validate_email(email):
        return jsonify({
            "status": "error",
            "detail": "邮箱格式不正确"
        }), 400
    
    if not validate_password(password):
        return jsonify({
            "status": "error",
            "detail": "密码必须至少6位"
        }), 400
    
    try:
        db = next(get_db())
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
        
        return jsonify({
            "status": "success",
            "message": "注册成功",
            "token": token
        })
    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "error",
            "detail": "用户名或邮箱已存在"
        }), 400

@bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        db = next(get_db())
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password):
            return jsonify({
                "status": "error",
                "detail": "用户名或密码错误"
            }), 401
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        # 创建JWT令牌
        token = create_jwt_token(user.id)
        
        return jsonify({
            "status": "success",
            "message": "登录成功",
            "token": token
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "detail": "登录失败，请重试"
        }), 500

@bp.route("/verify", methods=["GET"])
def verify_token():
    """验证令牌"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({
            "status": "error",
            "detail": "未提供令牌"
        }), 401
    
    try:
        # 从 Bearer token 中提取令牌
        token = auth_header.split(" ")[1]
        # 验证令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({
                "status": "error",
                "detail": "用户不存在"
            }), 401
            
        return jsonify({
            "status": "success",
            "user": user.username
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            "status": "error",
            "detail": "令牌已过期"
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            "status": "error",
            "detail": "无效的令牌"
        }), 401

@bp.route("/check_username/<username>", methods=["GET"])
def check_username(username):
    """检查用户名是否已存在"""
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    return jsonify({
        "exists": user is not None
    })

@bp.route("/check_email/<email>", methods=["GET"])
def check_email(email):
    """检查邮箱是否已存在"""
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    return jsonify({
        "exists": user is not None
    })
