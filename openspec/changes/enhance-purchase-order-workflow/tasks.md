## 1. 数据模型变更

- [x] 1.1 更新 PurchaseStatus 枚举，新增 pending_review、ready_purchase、purchasing、completed 状态
- [x] 1.2 PurchaseOrder 模型新增字段：logistics_company、logistics_no、source_purchase_order_id
- [x] 1.3 编写数据库迁移脚本，将现有数据状态迁移到新状态值
- [ ] 1.4 执行迁移脚本验证数据正确性

## 2. 后端服务层实现

- [x] 2.1 实现 get_available_suppliers 方法 - 根据品牌筛选供应商并标注优先级
- [x] 2.2 实现 update_supplier 方法 - 选择/修改供应商
- [x] 2.3 实现 update_logistics 方法 - 更新物流信息
- [x] 2.4 实现 approve_order 方法 - 审核通过（待审核→准备采购）
- [x] 2.5 实现 start_purchase 方法 - 开始采购（准备采购→采购中）
- [x] 2.6 实现 complete_order 方法 - 采购完成（采购中→采购完成）
- [x] 2.7 实现 rollback_order 方法 - 状态回退
- [x] 2.8 修改 recall_order 方法 - 撤回时正确回退销售单状态

## 3. 后端路由层实现

- [x] 3.1 新增 GET /purchase-orders/{purchase_no}/available-suppliers 端点
- [x] 3.2 新增 PUT /purchase-orders/{purchase_no}/supplier 端点
- [x] 3.3 新增 PUT /purchase-orders/{purchase_no}/logistics 端点
- [x] 3.4 新增 POST /purchase-orders/{purchase_no}/start-purchase 端点
- [x] 3.5 新增 POST /purchase-orders/{purchase_no}/complete 端点
- [x] 3.6 新增 POST /purchase-orders/{purchase_no}/rollback 端点
- [x] 3.7 修改 get_order_by_no 返回关联销售单简要信息

## 4. 前端实现

- [x] 4.1 更新采购单状态类型定义和中文映射
- [x] 4.2 实现采购单详情页面 - 显示基本信息、商品列表、关联销售单信息
- [x] 4.3 实现供应商选择组件 - 显示可选供应商列表，标注优先供应商
- [x] 4.4 实现物流信息录入表单
- [x] 4.5 实现状态操作按钮 - 审核通过、开始采购、采购完成、回退、撤回
- [x] 4.6 更新采购单列表页面状态筛选

## 5. 测试验证

- [x] 5.1 后端单元测试 - 状态流转逻辑
- [x] 5.2 后端单元测试 - 供应商筛选逻辑
- [x] 5.3 后端单元测试 - 销售单状态回退逻辑
- [x] 5.4 API 接口测试 - 所有新增端点
- [ ] 5.5 前端功能测试 - 完整采购流程
