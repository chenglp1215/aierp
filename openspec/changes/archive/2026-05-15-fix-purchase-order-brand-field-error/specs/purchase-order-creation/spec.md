## MODIFIED Requirements

### Requirement: 从销售订单创建采购单
系统 SHALL 支持从销售订单选中商品下推生成采购单，按品牌分组创建多个采购单。

#### Scenario: 正常下推采购单
- **WHEN** 用户选择销售订单中的商品并点击下推采购
- **THEN** 系统通过 `spec -> product -> brand` 关联链获取品牌信息
- **AND** 按品牌分组创建采购单
- **AND** 返回创建的采购单列表

#### Scenario: 商品无品牌信息
- **WHEN** 选中的商品没有关联品牌（brand 为 None）
- **THEN** 系统将品牌 ID 视为 0 进行分组
- **AND** 正常创建采购单

#### Scenario: 预加载关联数据
- **WHEN** 调用下推采购接口
- **THEN** 系统使用 `select_related` 预加载 `spec__product__brand` 和 `warehouse` 关联数据
- **AND** 避免在循环中产生 N+1 查询问题