"""部署配置工具 - 用于生成生产环境配置"""
import os
import sys

def create_production_config():
    """创建生产环境配置"""
    
    # Streamlit 生产配置
    config_content = '''[server]
port = 8501
address = 0.0.0.0
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 200
maxMessageSize = 200

[client]
showErrorDetails = false
maxCachedMessageAge = 3600

[browser]
gatherUsageStats = false
serverAddress = 0.0.0.0
serverPort = 8501
'''
    
    config_dir = '.streamlit'
    os.makedirs(config_dir, exist_ok=True)
    
    with open(os.path.join(config_dir, 'config.toml'), 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✓ 已创建 Streamlit 生产配置")

def create_requirements_prod():
    """创建生产环境依赖文件"""
    requirements = '''streamlit>=1.28.0
requests>=2.28.0
brotli>=1.0.9
gunicorn>=21.0.0
'''
    
    with open('requirements-prod.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("✓ 已创建生产环境依赖文件")

def create_dockerfile():
    """创建 Dockerfile 用于容器化部署"""
    dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# 复制应用代码
COPY . .

# 创建 Streamlit 配置目录
RUN mkdir -p /app/.streamlit

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
'''
    
    with open('Dockerfile', 'w', encoding='utf-8') as f:
        f.write(dockerfile)
    
    print("✓ 已创建 Dockerfile")

def create_docker_compose():
    """创建 Docker Compose 配置"""
    compose = '''version: '3.8'

services:
  todaytitle:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
    
    with open('docker-compose.yml', 'w', encoding='utf-8') as f:
        f.write(compose)
    
    print("✓ 已创建 Docker Compose 配置")

def create_env_example():
    """创建环境变量示例文件"""
    env_example = '''# DeepSeek API Key
DEEPSEEK_API_KEY=your_api_key_here

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8501
'''
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example)
    
    print("✓ 已创建环境变量示例文件")

if __name__ == '__main__':
    print("正在创建部署配置文件...")
    create_production_config()
    create_requirements_prod()
    create_dockerfile()
    create_docker_compose()
    create_env_example()
    print("\n✅ 所有部署配置文件已创建完成！")
    print("\n下一步操作：")
    print("1. 复制 .env.example 为 .env 并填入你的 API Key")
    print("2. 使用 Docker Compose 部署：docker-compose up -d")
    print("3. 或直接运行：streamlit run app.py")
