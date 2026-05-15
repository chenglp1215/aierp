## ADDED Requirements

### Requirement: 处理空字符串的整数字段

系统 SHALL 在创建销售订单明细时，正确处理前端传递的空字符串整数字段。

**适用字段**：
- `warehouse_id` - 仓库ID
- `product_id` - 商品ID
- `spec_id` - 规格ID
- `brand_id` - 品牌ID

**处理逻辑**：空字符串 `""` 应转换为 `None`，以符合数据库模型的 `null=True` 定义。

#### Scenario: 直运订单无仓库ID
- **WHEN** 前端提交订单明细，`shipping_method` 为 "直运"，`warehouse_id` 为空字符串
- **THEN** 系统将 `warehouse_id` 转换为 `None`，订单创建成功

#### Scenario: 正常仓库发货订单
- **WHEN** 前端提交订单明细，`warehouse_id` 为有效整数值
- **THEN** 系统正常处理，订单创建成功
