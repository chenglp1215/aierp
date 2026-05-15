## 1. 后端修改

- [ ] 1.1 修改 `backend/models_mysql/sales_order.py` 中 `SalesOrderItem.to_dict()` 方法，将 `shipping_method` 返回中文值（"直运"/"仓库发货"）
- [ ] 1.2 验证后端 API 返回的订单详情数据包含中文发货方式

## 2. 前端创建订单修改

- [ ] 2.1 修改 `web/src/components/workspace/SalesOrderCreate.vue` 的 `handleSaveOrder` 函数，提交完整的商品信息（`product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name`）
- [ ] 2.2 验证新建订单后，订单明细包含完整的商品信息

## 3. 前端详情页修改

- [ ] 3.1 修改 `web/src/components/workspace/SalesOrderDetail.vue`，在商品明细表格中添加"仓库"列
- [ ] 3.2 修改 `web/src/components/workspace/SalesOrderDetail.vue`，当发货方式为"直运"时，仓库列显示 "--"
- [ ] 3.3 修改 `web/src/components/workspace/SalesOrderDetail.vue`，移除 `handlePushPurchase` 中冗余的品牌信息查询逻辑
- [ ] 3.4 修改 `web/src/components/workspace/PushPurchaseItemSelectModal.vue`，当发货方式为"直运"时，仓库相关字段显示 "--"

## 4. 验证

- [ ] 4.1 新建销售订单，选择商品并提交，验证订单明细包含完整的商品信息
- [ ] 4.2 查看销售订单详情，验证发货方式显示为中文
- [ ] 4.3 查看销售订单详情，验证直发明细的仓库列显示 "--"
- [ ] 4.4 下推采购，验证弹窗中直发明细的仓库信息显示 "--"
