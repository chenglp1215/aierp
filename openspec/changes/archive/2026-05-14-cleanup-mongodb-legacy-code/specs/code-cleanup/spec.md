## REMOVED Requirements

### Requirement: MongoDB Customer Models
**Reason**: 客户管理模块已迁移到 MySQL，MongoDB 模型不再使用。
**Migration**: 使用 `models_mysql/customer.py` 中的 Customer、InvoiceInfo、ShippingAddress、CustomerDiscount 模型。

### Requirement: MongoDB Inventory Models
**Reason**: 库存管理模块已迁移到 MySQL，MongoDB 模型不再使用。
**Migration**: 使用 `models_mysql/warehouse.py` 中的 Warehouse、Stock、InboundBatch、OutboundBatch 模型。

### Requirement: MongoDB Customer Service
**Reason**: 客户服务已迁移到 MySQL 实现。
**Migration**: 使用 `services/customer_service_mysql.py` 中的 customer_service 和 customer_discount_service。

### Requirement: MongoDB Inventory Service
**Reason**: 库存服务已迁移到 MySQL 实现。
**Migration**: 使用 `services/inventory_service_mysql.py` 中的 warehouse_service、stock_service、inbound_batch_service、outbound_batch_service。

### Requirement: Province City API Endpoint
**Reason**: 省市数据为静态数据，API 接口已移除，数据可硬编码在前端。
**Migration**: 前端可直接内嵌省市数据 JSON，无需 API 调用。

## ADDED Requirements

### Requirement: Code Cleanup Validation
系统 SHALL 在清理后保持所有客户管理和库存管理接口正常工作。

#### Scenario: Customer API endpoints work after cleanup
- **WHEN** 清理完成后调用 `/api/customers/` 相关接口
- **THEN** 所有接口正常返回数据，使用 MySQL 实现

#### Scenario: Inventory API endpoints work after cleanup
- **WHEN** 清理完成后调用 `/api/warehouse/`、`/api/stock/` 相关接口
- **THEN** 所有接口正常返回数据，使用 MySQL 实现

#### Scenario: Agent tools work after cleanup
- **WHEN** 清理完成后使用 AI Agent 的客户和库存工具
- **THEN** 工具正常执行，使用 MySQL 服务实现