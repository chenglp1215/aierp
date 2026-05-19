## ADDED Requirements

### Requirement: 根据品牌筛选供应商

系统 SHALL 根据采购单的品牌筛选有该品牌供应资格的供应商列表。

#### Scenario: 筛选品牌供应商
- **WHEN** 用户获取采购单可选供应商列表
- **THEN** 系统返回 SupplierBrand 表中 brand_id 与采购单 brand_id 匹配的供应商
- **AND** 供应商信息包含：供应商ID、供应商名称、联系人、联系电话、折扣率、是否优先

#### Scenario: 无匹配供应商
- **WHEN** 采购单品牌在 SupplierBrand 表中无匹配记录
- **THEN** 系统返回空列表
- **AND** 提示"该品牌暂无供应商"

### Requirement: 优先供应商标注

系统 SHALL 在供应商列表中标注优先供应商（is_priority=true）。

#### Scenario: 显示优先供应商标识
- **WHEN** 供应商列表包含 is_priority=true 的供应商
- **THEN** 该供应商在列表中显示"优先"标识
- **AND** 优先供应商排在列表前面

#### Scenario: 多个优先供应商排序
- **WHEN** 存在多个优先供应商
- **THEN** 按折扣率从低到高排序（折扣率越低，价格越优惠）

### Requirement: 供应商折扣率显示

系统 SHALL 显示供应商对该品牌的折扣率信息。

#### Scenario: 显示折扣率
- **WHEN** 用户查看可选供应商列表
- **THEN** 每个供应商显示对应的折扣率（来自 SupplierBrand.discount 字段）

#### Scenario: 折扣率含义
- **WHEN** 折扣率为 0.95
- **THEN** 表示该供应商对该品牌的采购价格为标准价格的 95%