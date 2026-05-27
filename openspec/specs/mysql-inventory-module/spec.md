## ADDED Requirements

### Requirement: 库存数据模型使用 MySQL 存储

系统 SHALL 使用 Tortoise ORM 定义库存数据模型，存储在 MySQL 数据库的 `stocks` 表中。

#### Scenario: 创建库存记录
- **WHEN** 调用 Stock.create() 创建库存
- **THEN** 系统在 MySQL 的 stocks 表中插入一条记录，自动生成整数 ID

#### Scenario: 查询库存列表
- **WHEN** 调用 Stock.filter().all() 查询库存列表
- **THEN** 系统从 MySQL 数据库返回库存记录列表

### Requirement: 库存关联仓库和商品

系统 SHALL 在库存记录中关联仓库、商品和规格，使用整数外键 ID。

#### Scenario: 库存记录关联仓库
- **WHEN** 创建库存记录时指定 warehouse_id
- **THEN** 系统保存仓库关联，warehouse_id 为整数类型

#### Scenario: 库存记录关联商品和规格
- **WHEN** 创建库存记录时指定 product_id 和 spec_id
- **THEN** 系统保存商品和规格关联，product_id 和 spec_id 为整数类型

### Requirement: 库存数量管理

系统 SHALL 支持库存数量的增减操作，通过入库和出库批次记录实现。

#### Scenario: 入库增加库存
- **WHEN** 创建入库批次记录
- **THEN** 系统自动增加对应库存记录的 quantity 字段值

#### Scenario: 出库减少库存
- **WHEN** 创建出库批次记录
- **THEN** 系统自动减少对应库存记录的 quantity 字段值

#### Scenario: 出库数量超过库存
- **WHEN** 出库数量大于当前库存数量
- **THEN** 系统拒绝出库操作，返回错误信息"库存不足"

### Requirement: 库存状态自动计算

系统 SHALL 根据库存数量与阈值的关系自动计算库存状态。

#### Scenario: 正常库存状态
- **WHEN** 库存数量大于 min_stock 且小于 max_stock
- **THEN** 系统设置库存状态为 normal

#### Scenario: 低库存警告状态
- **WHEN** 库存数量小于或等于 min_stock 且大于 0
- **THEN** 系统设置库存状态为 low_stock

#### Scenario: 缺货状态
- **WHEN** 库存数量等于 0
- **THEN** 系统设置库存状态为 out_of_stock

#### Scenario: 超额库存状态
- **WHEN** 库存数量大于 max_stock 且 max_stock > 0
- **THEN** 系统设置库存状态为 overstock

### Requirement: 入库批次管理

系统 SHALL 使用 Tortoise ORM 定义入库批次数据模型，存储在 MySQL 数据库的 `inbound_batches` 表中。

#### Scenario: 创建入库批次
- **WHEN** 调用 InboundBatch.create() 创建入库批次
- **THEN** 系统在 MySQL 的 inbound_batches 表中插入记录，同时更新对应库存数量

#### Scenario: 查询入库批次列表
- **WHEN** 调用 InboundBatch.filter(stock_id=X).all() 查询入库批次
- **THEN** 系统返回指定库存的所有入库批次记录

### Requirement: 出库批次管理

系统 SHALL 使用 Tortoise ORM 定义出库批次数据模型，存储在 MySQL 数据库的 `outbound_batches` 表中。

#### Scenario: 创建出库批次
- **WHEN** 调用 OutboundBatch.create() 创建出库批次
- **THEN** 系统在 MySQL 的 outbound_batches 表中插入记录，同时减少对应库存数量

#### Scenario: 查询出库批次列表
- **WHEN** 调用 OutboundBatch.filter(stock_id=X).all() 查询出库批次
- **THEN** 系统返回指定库存的所有出库批次记录

### Requirement: 库存详情查询

系统 SHALL 支持查询库存详情，包括关联的商品、规格、仓库信息以及入库出库记录。

#### Scenario: 获取库存详情
- **WHEN** 调用 GET /api/v1/stocks/{id}
- **THEN** 系统返回库存信息，包含 product_info、spec_info、warehouse_info 关联信息

#### Scenario: 获取库存入库出库记录
- **WHEN** 查询库存详情时请求入库出库记录
- **THEN** 系统返回该库存的所有入库批次和出库批次记录

### Requirement: API 接口保持兼容

系统 SHALL 保持现有 API 接口签名和响应格式不变，前端无需修改。

#### Scenario: 获取库存列表
- **WHEN** 调用 GET /api/v1/stocks/
- **THEN** 系统返回包含 total、page、page_size、items 的 JSON 对象，items 中每条记录包含 product_info、spec_info、warehouse_info

#### Scenario: 创建入库批次
- **WHEN** 调用 POST /api/v1/inbound-batches/
- **THEN** 系统返回创建成功的入库批次信息，响应格式与 MongoDB 版本一致

#### Scenario: 创建出库批次
- **WHEN** 调用 POST /api/v1/outbound-batches/
- **THEN** 系统返回创建成功的出库批次信息，响应格式与 MongoDB 版本一致

### Requirement: 数据迁移完整性

系统 SHALL 在数据迁移过程中保持数据完整性，确保所有 MongoDB 数据正确迁移到 MySQL。

#### Scenario: 迁移仓库数据
- **WHEN** 执行数据迁移脚本
- **THEN** 系统将 MongoDB inventory_warehouses 集合的所有记录迁移到 MySQL warehouses 表

#### Scenario: 迁移库存数据
- **WHEN** 执行数据迁移脚本
- **THEN** 系统将 MongoDB inventory_stocks 集合的所有记录迁移到 MySQL stocks 表，正确映射关联 ID

#### Scenario: 迁移批次数据
- **WHEN** 执行数据迁移脚本
- **THEN** 系统将 MongoDB inventory_inbound_batches 和 inventory_outbound_batches 集合的所有记录迁移到 MySQL 对应表