# AI MDR Platform Backend

基于 FastAPI 的后端服务，使用 MongoDB 和 Redis。

## 技术栈

- **FastAPI**: 高性能 Python Web 框架
- **MongoDB**: 文档型数据库
- **Redis**: 缓存和会话存储
- **Pydantic**: 数据验证和序列化
- **Motor**: MongoDB 异步驱动

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── database.py          # 数据库连接管理
│   ├── middleware.py        # 中间件
│   └── routers/             # 路由模块
│       ├── __init__.py
│       └── health.py        # 健康检查
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置管理
├── models/                  # 数据模型
├── services/                # 业务逻辑
├── utils/                   # 工具函数
├── tests/                   # 测试
├── main.py                  # 应用入口
├── requirements.txt         # 依赖
└── .env.example             # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接等
```

### 3. 启动服务

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 健康检查

- `GET /api/v1/health/` - 健康状态检查
- `GET /api/v1/health/ping` - Ping 测试

## 开发规范

### 代码风格

- 使用 Black 格式化代码
- 使用 isort 管理导入
- 使用 flake8 检查代码质量

### 测试

```bash
# 运行测试
pytest

# 运行测试并显示覆盖率
pytest --cov=app --cov-report=html
```

### 部署

#### Docker 部署

```bash
# 构建镜像
docker build -t ai-mdr-platform .

# 运行容器
docker run -p 8000:8000 --env-file .env ai-mdr-platform
```

#### 生产环境

```bash
# 使用 Gunicorn + Uvicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| APP_NAME | 应用名称 | AI MDR Platform API |
| APP_VERSION | 应用版本 | 1.0.0 |
| APP_ENV | 运行环境 | development |
| DEBUG | 调试模式 | true |
| HOST | 服务器地址 | 0.0.0.0 |
| PORT | 服务器端口 | 8000 |
| MONGODB_URL | MongoDB 连接地址 | mongodb://localhost:27017 |
| MONGODB_DB_NAME | MongoDB 数据库名 | ai_mdr_platform |
| REDIS_URL | Redis 连接地址 | redis://localhost:6379/0 |
| SECRET_KEY | JWT 密钥 | your-secret-key |
| ALGORITHM | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 过期时间 | 30 |
| CORS_ORIGINS | CORS 允许的源 | ["http://localhost:5174"] |

## 开发注意事项

1. **数据库连接**: 确保 MongoDB 和 Redis 服务已启动
2. **环境变量**: 生产环境必须修改 SECRET_KEY
3. **CORS 配置**: 根据前端地址调整 CORS_ORIGINS
4. **日志级别**: 开发环境使用 DEBUG，生产环境使用 INFO 或 WARNING

## 许可证

MIT License
