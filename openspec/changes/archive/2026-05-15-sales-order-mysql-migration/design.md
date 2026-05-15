## Context

销售订单管理系统是 ERP 的核心模块，涉及订单创建、审核、下推采购、发货、收款等完整业务流程。当前使用 MongoDB 实现，需要迁移到 MySQL 以保持架构一致性。

**当前状态：**
- 销售订单、采购单使用 MongoDB (Motor) 存储
- 客户、商品、库存、认证已迁移到 MySQL (Tortoise ORM)
- 订单状态流转：draft → audited → partially_pushed_to_purchase → pushed_to_purchase → closed
- 下推采购逻辑已实现基础功能，但缺少库存判断

**约束：**
- 不迁移历史数据，只做代码迁移
- 保持 API 接口兼容性
- 使用 Tortoise ORM 模式，参考已迁移模块

## Goals / Non-Goals

**Goals:**
- 将销售订单和采购单迁移到 MySQL
- 完善订单状态流转，增加待审核状态
- 实现库存判断逻辑，只下推库存不足的商品
- 实现采购单撤销功能
- 保持与现有系统的兼容性

**Non-Goals:**
- 不迁移历史数据
- 不实现采购单审核后的后续流程（入库、财务等）
- 不考虑已占用库存的计算

## Decisions

### 决策 1：使用 Tortoise ORM 进行 MySQL 实现

**理由：**
- 与已迁移模块（客户、商品、库存）保持一致
- Tortoise ORM 支持异步操作，与 FastAPI 契合
- 内置迁移工具支持

**替代方案：**
- SQLAlchemy：同步/异步混用复杂，与现有代码风格不一致

### 决策 2：订单明细使用一对多关系而非 JSON 字段

**理由：**
- 关系型数据库更适合结构化查询
- 便于统计、关联查询
- 符合数据库设计范式

**表结构：**
- sales_orders (主表) ← sales_order_items (明细表) [一对多]
- sales_orders (主表) ← sales_deliver_infos (发货信息) [一对多]
- purchase_orders (主表) ← purchase_order_items (明细表) [一对多]

### 决策 3：订单状态流转设计

```
draft → pending → audited → partially_pushed_to_purchase → pushed_to_purchase → closed
  ↓        ↓        ↓              ↓                            ↓
cancelled  draft   cancelled      cancelled                   cancelled
           (驳回)
```

**特殊入口：** 创建订单时"提交并审核通过"直接跳到 audited 状态

### 决策 4：库存不足判断逻辑

```
需要下推的条件：
1. 直运商品：始终需要下推
2. 仓库发货商品：
   - 库存数量 < 订单数量
   - 或 库存数量 ≤ min_stock（库存不足阈值）
```

### 决策 5：采购单撤销流程

```
撤销步骤：
1. 检查采购单状态（只有 draft 或 audited 可撤销）
2. 获取关联的销售订单和商品行号
3. 更新销售订单商品的 pushed = false
4. 重新计算销售订单状态
5. 删除采购单
6. 记录状态流转
```

## Risks / Trade-offs

**风险 1：API 兼容性**
- 缓解：保持相同的响应格式，只增加新字段

**风险 2：并发操作**
- 缓解：使用数据库事务保证一致性

**风险 3：性能影响**
- 缓解：一对多关系查询使用 prefetch_related 优化

## Migration Plan

1. 创建 MySQL 模型文件
2. 生成数据库迁移
3. 实现新的 Service 层
4. 更新路由层
5. 更新 Agent 工具
6. 测试验证
7. 删除旧的 MongoDB 文件

**回滚策略：** 保留旧的 MongoDB 文件，通过配置切换
