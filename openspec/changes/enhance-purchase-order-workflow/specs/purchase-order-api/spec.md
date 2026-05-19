## MODIFIED Requirements

### Requirement: 获取采购单详情

系统 SHALL 返回采购单完整详情，包括基本信息、商品明细、关联销售单简要信息。

#### Scenario: 获取采购单详情成功
- **WHEN** 用户请求 GET /purchase-orders/{purchase_no}
- **THEN** 返回采购单基本信息
- **AND** 返回商品明细列表（包含规格、品牌、仓库、数量、单价、金额）
- **AND** 返回关联销售单简要信息（订单号、客户名称、订单日期）

#### Scenario: 采购单不存在
- **WHEN** 用户请求不存在的采购单号
- **THEN** 返回 404 错误

### Requirement: 获取采购单列表

系统 SHALL 支持按状态、品牌、来源销售单号筛选采购单列表。

#### Scenario: 按状态筛选
- **WHEN** 用户请求 GET /purchase-orders?purchase_status=pending_review
- **THEN** 返回所有待审核状态的采购单

#### Scenario: 按品牌筛选
- **WHEN** 用户请求 GET /purchase-orders?brand_id=1
- **THEN** 返回指定品牌的所有采购单

## ADDED Requirements

### Requirement: 获取可选供应商列表

系统 SHALL 提供获取采购单可选供应商列表的 API。

#### Scenario: 获取可选供应商
- **WHEN** 用户请求 GET /purchase-orders/{purchase_no}/available-suppliers
- **THEN** 返回该采购单品牌对应的供应商列表
- **AND** 包含供应商ID、名称、联系人、联系电话、折扣率、是否优先

### Requirement: 选择供应商

系统 SHALL 提供选择/修改采购单供应商的 API。

#### Scenario: 选择供应商
- **WHEN** 用户请求 PUT /purchase-orders/{purchase_no}/supplier
- **AND** 请求体包含 supplier_id
- **THEN** 更新采购单的 supplier_id 和 supplier_name（快照）

#### Scenario: 状态不允许修改供应商
- **WHEN** 采购单状态为采购中或之后的状态
- **THEN** 返回 400 错误"当前状态不可修改供应商"

### Requirement: 更新物流信息

系统 SHALL 提供更新采购单物流信息的 API。

#### Scenario: 更新物流信息
- **WHEN** 用户请求 PUT /purchase-orders/{purchase_no}/logistics
- **AND** 请求体包含 logistics_company、logistics_no、source_purchase_order_id、expect_arrive_date
- **THEN** 更新采购单的物流信息字段

#### Scenario: 状态不允许修改物流信息
- **WHEN** 采购单状态为采购中或之后的状态
- **THEN** 返回 400 错误"当前状态不可修改物流信息"

### Requirement: 审核通过采购单

系统 SHALL 提供审核通过采购单的 API。

#### Scenario: 审核通过
- **WHEN** 用户请求 POST /purchase-orders/{purchase_no}/approve
- **AND** 采购单状态为待审核
- **THEN** 采购单状态变更为准备采购

#### Scenario: 状态不允许审核
- **WHEN** 采购单状态不是待审核
- **THEN** 返回 400 错误"只有待审核状态的采购单可以审核"

### Requirement: 开始采购

系统 SHALL 提供开始采购的 API。

#### Scenario: 开始采购
- **WHEN** 用户请求 POST /purchase-orders/{purchase_no}/start-purchase
- **AND** 采购单状态为准备采购
- **THEN** 采购单状态变更为采购中

#### Scenario: 状态不允许开始采购
- **WHEN** 采购单状态不是准备采购
- **THEN** 返回 400 错误"只有准备采购状态的采购单可以开始采购"

### Requirement: 采购完成

系统 SHALL 提供采购完成的 API。

#### Scenario: 采购完成
- **WHEN** 用户请求 POST /purchase-orders/{purchase_no}/complete
- **AND** 采购单状态为采购中
- **THEN** 采购单状态变更为采购完成

#### Scenario: 状态不允许完成
- **WHEN** 采购单状态不是采购中
- **THEN** 返回 400 错误"只有采购中状态的采购单可以完成"

### Requirement: 状态回退

系统 SHALL 提供采购单状态回退的 API。

#### Scenario: 回退到上一状态
- **WHEN** 用户请求 POST /purchase-orders/{purchase_no}/rollback
- **AND** 采购单状态为准备采购或采购中
- **THEN** 采购单状态回退到上一状态

#### Scenario: 采购完成不可回退
- **WHEN** 采购单状态为采购完成
- **THEN** 返回 400 错误"采购完成状态不可回退"

### Requirement: 撤回采购单

系统 SHALL 提供撤回采购单的 API（仅限待审核状态）。

#### Scenario: 撤回采购单
- **WHEN** 用户请求 POST /purchase-orders/{purchase_no}/recall
- **AND** 采购单状态为待审核
- **THEN** 删除采购单
- **AND** 回退关联销售单状态

#### Scenario: 状态不允许撤回
- **WHEN** 采购单状态不是待审核
- **THEN** 返回 400 错误"只有待审核状态的采购单可以撤回"
