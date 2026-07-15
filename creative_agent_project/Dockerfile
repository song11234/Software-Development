# 智能资料整理助手
# 第08章：轻量级容器化交付

FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY data/ ./data/

# 创建非 root 用户运行（安全最佳实践）
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 暴露端口（通过环境变量 PORT 配置，默认 8000）
EXPOSE 8000

# 启动服务
CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
