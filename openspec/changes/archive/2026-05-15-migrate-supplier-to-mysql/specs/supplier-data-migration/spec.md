## ADDED Requirements

### Requirement: Data Migration Script

系统 SHALL 提供数据迁移脚本，将 MongoDB 供应商数据迁移到 MySQL。

#### Scenario: 迁移供应商主数据
- **WHEN** 执行迁移脚本
- **THEN** 系统 SHALL 从 MongoDB `suppliers` 集合读取数据并插入 MySQL `suppliers` 表

#### Scenario: 映射品牌 ObjectId
- **WHEN** 迁移供应商品牌关联数据
- **THEN** 系统 SHALL 将 MongoDB 品牌 ObjectId 映射到 MySQL 品牌 INT ID

#### Scenario: 迁移银行账户数据
- **WHEN** 迁移银行账户数据
- **THEN** 系统 SHALL 将嵌入式 `bank_account` 对象转换为 `supplier_bank_accounts` 表记录

### Requirement: Migration Transaction

迁移过程 SHALL 使用事务保证数据一致性。

#### Scenario: 迁移失败回滚
- **WHEN** 迁移过程中发生错误
- **THEN** 系统 SHALL 回滚所有已执行的数据库操作

#### Scenario: 迁移成功提交
- **WHEN** 所有数据迁移成功
- **THEN** 系统 SHALL 提交事务并输出迁移统计信息

### Requirement: Migration Validation

迁移完成后 SHALL 验证数据完整性。

#### Scenario: 验证记录数量
- **WHEN** 迁移完成
- **THEN** 系统 SHALL 对比 MongoDB 和 MySQL 记录数量并输出差异

#### Scenario: 验证关联完整性
- **WHEN** 迁移完成
- **THEN** 系统 SHALL 验证所有品牌关联的有效性
