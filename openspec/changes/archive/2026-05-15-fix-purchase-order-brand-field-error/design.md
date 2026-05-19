## Context

销售订单明细模型 `SalesOrderItem` 已完成外键关联重构，品牌信息通过关联链获取：
```
SalesOrderItem -> spec (ProductSpec) -> product (Product) -> brand (Brand)
```

采购单服务 `purchase_order_service_mysql.py` 的 `create_from_sales_order` 方法仍使用旧的直接字段访问方式，导致运行时错误。

**当前状态**：
- `SalesOrderItem` 有 `spec_id` 外键，无 `brand_id`、`product_id` 冗余字段
- `PurchaseOrderItem` 保留了冗余字段用于兼容（`product_id`, `brand_id`）
- 服务层需要通过关联查询获取品牌信息

## Goals / Non-Goals

**Goals:**
- 修复 `create_from_sales_order` 方法中的字段访问错误
- 通过正确的关联链获取品牌信息用于分组
- 确保下推采购功能正常工作

**Non-Goals:**
- 不修改数据模型结构
- 不改变业务逻辑（按品牌分组创建采购单）
- 不修改 API 接口

## Decisions

### 1. 品牌信息获取方式

**选择**: 在调用 `create_from_sales_order` 前，预先加载关联数据

**理由**:
- 避免在循环中多次查询数据库（N+1 问题）
- `select_related` 可以一次性加载所有需要的关联数据
- 性能更优

**替代方案**:
- 方案 A: 在服务层逐个 await 关联数据 → 性能差，N+1 查询
- 方案 B: 修改模型添加冗余字段 → 违反重构目标，不推荐

### 2. 分组逻辑调整

**选择**: 使用 `spec.product.brand.id` 进行分组，处理 brand 为 None 的情况

**理由**:
- 品牌可能为空，需要用 `or 0` 处理
- 保持现有分组逻辑不变

## Risks / Trade-offs

- **风险**: 部分 `SalesOrderItem` 可能没有关联 `spec` 或 `spec.product`
  - **缓解**: 使用安全访问方式，brand_id 默认为 0
- **风险**: 关联查询可能增加数据库负载
  - **缓解**: 只在下推时执行，频率可控
