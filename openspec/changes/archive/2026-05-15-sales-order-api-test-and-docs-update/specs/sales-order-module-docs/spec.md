## MODIFIED Requirements

### Requirement: 销售订单模块 API 文档

系统 SHALL 提供销售订单模块的完整 API 文档，包含所有接口的定义和数据结构说明。

#### Scenario: API 接口列表展示
- **WHEN** 用户查看销售订单模块文档
- **THEN** 显示所有 11 个 API 接口的路径、方法、说明和权限要求

#### Scenario: 数据模型结构展示
- **WHEN** 用户查看销售订单数据结构
- **THEN** 显示 SalesOrder、SalesOrderItem、SalesDeliverInfo 的完整字段定义

#### Scenario: 状态枚举值展示
- **WHEN** 用户查看订单状态枚举
- **THEN** 显示 OrderStatus 的所有枚举值（draft、pending、audited、partially_pushed_to_purchase、pushed_to_purchase、closed、cancelled）

#### Scenario: 状态流转图展示
- **WHEN** 用户查看订单状态流转
- **THEN** 显示状态流转图和允许的转换路径

#### Scenario: 响应格式示例展示
- **WHEN** 用户查看接口响应格式
- **THEN** 显示成功和错误响应的 JSON 示例