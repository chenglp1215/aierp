## ADDED Requirements

### Requirement: MySQL 数据库连接配置
系统 SHALL 支持通过环境变量配置 MySQL 数据库连接参数，包括主机、端口、用户名、密码和数据库名。

#### Scenario: 使用环境变量配置数据库连接
- **WHEN** 存在有效的 `.env` 文件包含 MySQL 配置
- **THEN** 系统在启动时 SHALL 读取并使用这些配置连接数据库

#### Scenario: 数据库连接成功
- **WHEN** 配置的数据库连接参数正确且数据库服务可用
- **THEN** 系统 SHALL 成功建立数据库连接并输出成功日志

### Requirement: 数据库表自动初始化
系统 SHALL 在服务启动时自动创建不存在的数据库表。

#### Scenario: 首次启动创建表结构
- **WHEN** 数据库中不存在所需的表
- **THEN** 系统 SHALL 根据 Tortoise ORM 模型定义自动创建表结构

#### Scenario: 后续启动不重复创建
- **WHEN** 数据库表已存在
- **THEN** 系统 SHALL 跳过表创建步骤，不修改现有表结构

### Requirement: 初始化数据脚本
系统 SHALL 提供独立脚本用于初始化默认数据（权限、角色、管理员账号）。

#### Scenario: 执行初始化脚本
- **WHEN** 运行 `python scripts/init_db_mysql.py`
- **THEN** 系统 SHALL 创建默认权限、角色和管理员账号（如不存在）

#### Scenario: 幂等性保证
- **WHEN** 初始化数据已存在
- **THEN** 系统 SHALL 跳过已存在的数据，不产生重复或错误

### Requirement: Tortoise ORM 模型注册
系统 SHALL 在初始化 MySQL 连接时注册所有需要使用的模型模块。

#### Scenario: 添加新的 MySQL 模型模块
- **WHEN** 在 `models_mysql/` 目录下新增模型文件（如 `product.py`）
- **THEN** 开发者 SHALL 在 `app/database.py` 的 `init_mysql()` 函数中添加对应模块到 `modules["models"]` 列表
- **AND** 格式为 `"models_mysql.{模块名}"`

#### Scenario: 模型未注册时的错误
- **WHEN** 使用未注册的 Tortoise ORM 模型进行数据库操作
- **THEN** 系统 SHALL 抛出 `ConfigurationError: default_connection for the model cannot be None`
- **AND** 需检查 `init_mysql()` 中的 `modules["models"]` 是否包含该模型所在模块

#### Scenario: 模型注册示例
- **GIVEN** 项目有 `models_mysql/auth.py` 和 `models_mysql/product.py` 两个模型文件
- **WHEN** 初始化数据库连接时
- **THEN** `Tortoise.init()` 的配置 SHALL 为：
  ```python
  modules={"models": ["models_mysql.auth", "models_mysql.product"]}
  ```
