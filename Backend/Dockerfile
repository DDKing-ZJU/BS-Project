# 使用 Python 3.13 作为基础镜像
FROM python:3.13.1-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# JWT配置
ARG JWT_SECRET_KEY
ARG JWT_ALGORITHM=HS256
ENV JWT_SECRET_KEY=$JWT_SECRET_KEY
ENV JWT_ALGORITHM=$JWT_ALGORITHM

# 数据库配置
ARG DB_DRIVER=mysql+pymysql
ARG DB_USER=root
ARG DB_PASSWORD
ARG DB_HOST=localhost
ARG DB_PORT=3306
ARG DB_NAME=bs_project

ENV DB_DRIVER=$DB_DRIVER
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV DB_NAME=$DB_NAME

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]
