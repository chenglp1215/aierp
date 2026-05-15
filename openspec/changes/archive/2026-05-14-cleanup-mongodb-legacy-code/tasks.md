## 1. 更新依赖模块导入

- [x] 1.1 更新 `backend/models/__init__.py`，移除 MongoDB 模型导出（CustomerBase、CustomerType、CustomerStatus、CustomerDiscount、Warehouse、Stock 等）
- [x] 1.2 更新 `backend/app/agent/tools/customer.py`，将导入从 `services.customer_service` 改为 `services.customer_service_mysql`（简化处理，后续重新对接）
- [x] 1.3 更新 `backend/app/agent/tools/inventory.py`，将导入从 `services.inventory_service` 改为 `services.inventory_service_mysql`（简化处理，后续重新对接）

## 2. 删除 MongoDB 服务文件

- [x] 2.1 删除 `backend/services/customer_service.py`
- [x] 2.2 删除 `backend/services/inventory_service.py`
- [x] 2.3 保留 `backend/services/province_city_service.py`（前端仍在使用省市接口）

## 3. 删除 MongoDB 模型文件

- [x] 3.1 删除 `backend/models/customer.py`
- [x] 3.2 删除 `backend/models/inventory.py`
- [x] 3.3 删除 `backend/models/province_city.py`（数据已硬编码在 service 中）

## 4. 保留省市路由（前端使用）

- [x] 4.1 保留 `backend/app/routers/province_city.py`（前端调用 `/api/province-city/`）
- [x] 4.2 保留 `backend/app/routers/prompts/province_city.py`（被 customer.py 使用）

## 5. 验证清理结果

- [x] 5.1 使用 grep 确认无遗漏的 MongoDB 模型/服务引用
- [x] 5.2 启动后端服务验证无导入错误
- [x] 5.3 测试客户管理 API 接口正常工作
- [x] 5.4 测试库存管理 API 接口正常工作
- [x] 5.5 测试省市 API 接口正常工作（确认保留）