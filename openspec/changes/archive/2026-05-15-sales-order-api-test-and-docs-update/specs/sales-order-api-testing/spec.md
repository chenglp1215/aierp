## ADDED Requirements

### Requirement: API 测试脚本生成

系统 SHALL 生成销售订单模块的 API 测试脚本，覆盖所有 11 个接口。

#### Scenario: 创建订单测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/` 携带有效订单数据
- **THEN** 返回状态码 200，包含订单号和订单 ID

#### Scenario: 创建并提交订单测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/create-and-submit` 携带有效订单数据
- **THEN** 返回状态码 200，订单状态为 `audited`

#### Scenario: 获取订单列表测试
- **WHEN** 发送 GET 请求到 `/api/v1/sales-orders/`
- **THEN** 返回状态码 200，包含分页数据和订单列表

#### Scenario: 获取订单详情测试
- **WHEN** 发送 GET 请求到 `/api/v1/sales-orders/{order_no}`
- **THEN** 返回状态码 200，包含订单详情和明细列表

#### Scenario: 更新订单测试
- **WHEN** 发送 PUT 请求到 `/api/v1/sales-orders/{order_no}` 携带更新数据
- **THEN** 返回状态码 200，订单更新成功

#### Scenario: 删除订单测试
- **WHEN** 发送 DELETE 请求到 `/api/v1/sales-orders/{order_no}`
- **THEN** 返回状态码 200，订单删除成功

#### Scenario: 提交审核测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/{order_no}/submit`
- **THEN** 返回状态码 200，订单状态变为 `pending`

#### Scenario: 审核通过测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/{order_no}/approve`
- **THEN** 返回状态码 200，订单状态变为 `audited`

#### Scenario: 驳回订单测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/{order_no}/reject`
- **THEN** 返回状态码 200，订单状态变为 `draft`

#### Scenario: 取消订单测试
- **WHEN** 发送 POST 请求到 `/api/v1/sales-orders/{order_no}/cancel`
- **THEN** 返回状态码 200，订单状态变为 `cancelled`

#### Scenario: 获取状态流转记录测试
- **WHEN** 发送 GET 请求到 `/api/v1/sales-orders/{order_no}/status-flows`
- **THEN** 返回状态码 200，包含状态流转历史记录

### Requirement: 测试数据清理

测试脚本 SHALL 在测试完成后清理创建的测试数据，避免污染数据库。

#### Scenario: 测试后数据清理
- **WHEN** 所有测试用例执行完成
- **THEN** 删除测试过程中创建的所有订单数据

### Requirement: 测试报告输出

测试脚本 SHALL 输出详细的测试报告，包含每个用例的执行结果。

#### Scenario: 测试成功报告
- **WHEN** 测试用例执行成功
- **THEN** 输出绿色成功标识和用例名称

#### Scenario: 测试失败报告
- **WHEN** 测试用例执行失败
- **THEN** 输出红色失败标识、用例名称和错误详情
