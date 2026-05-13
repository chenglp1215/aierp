# MySQL 本地开发配置实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 配置本地开发环境连接到远程 MySQL 测试数据库，确保服务启动时自动创建表结构，并初始化默认数据。

**Architecture:** 使用 Pydantic Settings 从 `.env` 文件读取 MySQL 连接参数，Tortoise ORM 在服务启动时自动生成表结构，独立脚本初始化默认数据。

**Tech Stack:** Python, FastAPI, Pydantic Settings, Tortoise ORM, MySQL

---

## 文件结构

| 文件 | 操作 | 负责内容 |
|------|------|----------|
| `backend/.env` | 创建 | 本地开发环境变量配置 |
| `backend/config/settings.py` | 修改 | 更新 MySQL 默认配置值 |

---

### Task 1: 创建环境配置文件

**Files:**
- Create: `backend/.env`

- [ ] **Step 1: 创建 .env 文件**

创建 `backend/.env` 文件，内容如下：

```env
# 应用配置
APP_NAME=AI MDR Platform API
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# MongoDB 配置
MONGODB_URL=mongodb://132.232.212.151:58902
MONGODB_DB_NAME=oai_erp_test

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=["http://localhost:5174", "http://localhost:3000"]

# 日志配置
LOG_LEVEL=INFO

# MySQL 配置（本地开发测试环境）
MYSQL_HOST=132.232.212.151
MYSQL_PORT=58901
MYSQL_USER=admin
MYSQL_PASSWORD=Chenglp1215!@#
MYSQL_DATABASE=erp_test
```

- [ ] **Step 2: 验证 .env 文件已创建**

Run: `cat backend/.env`
Expected: 文件内容显示正确

---

### Task 2: 更新配置默认值

**Files:**
- Modify: `backend/config/settings.py:21-25`

- [ ] **Step 1: 更新 MySQL 默认配置**

修改 `backend/config/settings.py` 中的 MySQL 配置默认值（第 21-25 行）：

```python
    # MySQL 配置
    MYSQL_HOST: str = "132.232.212.151"
    MYSQL_PORT: int = 58901
    MYSQL_USER: str = "admin"
    MYSQL_PASSWORD: str = "Chenglp1215!@#"
    MYSQL_DATABASE: str = "erp_test"
```

- [ ] **Step 2: 验证配置文件更新**

Run: `grep -A5 "MySQL 配置" backend/config/settings.py`
Expected: 显示更新后的配置值

---

### Task 3: 测试数据库连接

**Files:**
- 无文件修改，仅验证

- [ ] **Step 1: 测试 MySQL 连接**

Run: `cd backend && python -c "
import pymysql
try:
    conn = pymysql.connect(
        host='132.232.212.151',
        port=58901,
        user='admin',
        password='Chenglp1215!@#',
        database='erp_test',
        connect_timeout=10
    )
    print('数据库连接成功!')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {e}')
"`
Expected: 输出 "数据库连接成功!"

---

### Task 4: 初始化数据库数据

**Files:**
- 无文件修改，执行初始化脚本

- [ ] **Step 1: 运行数据库初始化脚本**

Run: `cd backend && python scripts/init_db_mysql.py`
Expected: 输出包含 "MySQL 数据库初始化完成"

- [ ] **Step 2: 验证数据初始化结果**

Run: `cd backend && python -c "
import pymysql
conn = pymysql.connect(
    host='132.232.212.151',
    port=58901,
    user='admin',
    password='Chenglp1215!@#',
    database='erp_test'
)
cursor = conn.cursor()

# 检查表是否创建
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
print(f'已创建表: {[t[0] for t in tables]}')

# 检查用户数据
cursor.execute('SELECT username FROM users')
users = cursor.fetchall()
print(f'用户: {[u[0] for u in users]}')

# 检查角色数据
cursor.execute('SELECT code, name FROM roles')
roles = cursor.fetchall()
print(f'角色: {[(r[0], r[1]) for r in roles]}')

conn.close()
"`
Expected: 显示已创建的表、用户和角色列表

---

### Task 5: 启动服务验证

**Files:**
- 无文件修改，启动服务验证

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && timeout 10 python main.py || true`
Expected: 输出包含 "MySQL (Tortoise ORM) 连接成功"

- [ ] **Step 2: 验证 API 响应**

Run: `cd backend && python -c "
import asyncio
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/api/v1/docs')
print(f'API 状态: {response.status_code}')
"`
Expected: API 返回正常状态码

---

### Task 6: 提交变更

- [ ] **Step 1: 检查变更状态**

Run: `cd e:/ai_erp/aierp && git status`
Expected: 显示 `backend/.env` 和 `backend/config/settings.py` 变更

- [ ] **Step 2: 提交变更**

Run: `cd e:/ai_erp/aierp && git add backend/.env backend/config/settings.py && git commit -m "feat: 配置本地开发 MySQL 数据库连接

- 创建 backend/.env 配置远程测试数据库
- 更新 settings.py MySQL 默认配置值
- 数据库地址: 132.232.212.151:58901
- 数据库名: erp_test

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"`
Expected: 提交成功

---

## 自检清单

**1. Spec 覆盖率:**
- [x] MySQL 数据库连接配置 → Task 1, 2, 3
- [x] 数据库表自动初始化 → Task 4 (init_mysql 中的 generate_schemas=True)
- [x] 初始化数据脚本 → Task 4

**2. 占位符扫描:** 无 TBD、TODO、"implement later" 等占位符

**3. 类型一致性:** 配置参数名称与现有代码一致 (MYSQL_HOST, MYSQL_PORT 等)