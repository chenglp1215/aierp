## Why

项目需要配置本地开发环境的 MySQL 数据库连接，以便后端服务能够正常启动并连接到远程测试数据库。当前项目已有 MySQL 配置框架，但需要更新为指定的远程测试数据库地址，并确保数据库初始化流程能够正常执行。

## What Changes

- 更新 `backend/config/settings.py` 中的 MySQL 配置默认值
- 创建 `backend/.env` 文件配置本地开发环境的数据库连接参数
- 确保 `init_mysql()` 函数能够正确连接到远程数据库
- 确保服务启动时能够自动执行数据库表初始化（generate_schemas=True）
- 确保 `init_db_mysql.py` 脚本能够正常初始化默认数据

### 配置详情

| 参数 | 值 |
|------|------|
| MYSQL_HOST | 132.232.212.151 |
| MYSQL_PORT | 58901 |
| MYSQL_USER | admin |
| MYSQL_PASSWORD | Chenglp1215!@# |
| MYSQL_DATABASE | erp_test |

## Capabilities

### New Capabilities

- `mysql-local-dev`: 本地开发环境 MySQL 数据库连接配置，包括环境变量配置、数据库连接初始化、表结构自动生成

### Modified Capabilities

无（这是基础设施配置变更，不影响现有业务功能的需求规格）

## Impact

- **配置文件**: `backend/config/settings.py`, `backend/.env`
- **数据库连接**: `backend/app/database.py` 中的 `init_mysql()` 函数
- **初始化脚本**: `backend/scripts/init_db_mysql.py`
- **服务启动**: `backend/app/__init__.py` 中的 lifespan 函数