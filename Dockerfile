# 使用Python官方镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt文件到工作目录
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码到工作目录
COPY . .

# 暴露应用程序使用的端口
EXPOSE 8080

# 设置环境变量（可选）
# ENV FLASK_ENV=production

# 定义启动命令
CMD ["python", "app.py"]