## 1. 数据模型创建

- [x] 1.1 创建 `backend/models_mysql/product.py` 文件
- [x] 1.2 实现 Brand 模型（brands 表）
- [x] 1.3 实现 Category 模型（categories 表，支持 parent_id 自关联）
- [x] 1.4 实现 Product 模型（products 表，外键关联 Brand 和 Category）
- [x] 1.5 实现 ProductSpec 模型（product_specs 表，外键关联 Product）
- [x] 1.6 在 `backend/models_mysql/__init__.py` 中导出模型

## 2. 服务层重构

- [x] 2.1 创建 `backend/services/product_service_mysql.py` 文件
- [x] 2.2 实现 BrandService 类（MySQL 版本）
- [x] 2.3 实现 CategoryService 类（MySQL 版本，支持树形查询）
- [x] 2.4 实现 ProductService 类（MySQL 版本）
- [x] 2.5 实现 ProductSpecService 类（MySQL 版本）

## 3. 路由层适配

- [x] 3.1 修改 `backend/app/routers/product.py` 使用 MySQL 服务层
- [x] 3.2 添加 ID 类型转换（string -> int）
- [x] 3.3 验证 API 接口兼容性

## 4. 数据库初始化

- [x] 4.1 在 `backend/scripts/init_db_sync.py` 中添加商品模块表初始化
- [x] 4.2 运行初始化脚本创建表结构
- [x] 4.3 验证表结构和外键约束

## 5. 测试验证

- [x] 5.1 启动后端服务验证模型加载
- [x] 5.2 测试品牌 CRUD 接口
- [x] 5.3 测试分类 CRUD 和树形查询接口
- [x] 5.4 测试商品 CRUD 接口
- [x] 5.5 测试商品规格 CRUD 接口