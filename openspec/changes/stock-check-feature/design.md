## Context

库存管理模块已完成 MySQL 迁移，使用 Tortoise ORM 管理数据。现有入库（InboundBatch）和出库（OutboundBatch）记录库存变动，但缺少盘库功能。

盘库业务场景：
- 仓库人员定期盘点，记录实际数量
- 系统自动计算差异（盘盈/盘亏）
- 批量盘点时上传 Excel 提高效率
- Excel 中不存在的规格自动创建库存记录（盘盈入库）

技术约束：
- 后端使用 Tortoise ORM + MySQL
- 前端使用 Vue 3 + vxe-table
- 复用现有 `stock.edit` 权限

## Goals / Non-Goals

**Goals:**
- 实现单个盘库功能，支持录入实际盘点数量并自动计算差异
- 实现批量盘库功能，支持 Excel 上传和解析
- 盘库记录与入库/出库记录并列展示
- 批量盘库生成批次号便于追溯
- Excel 中不存在的库存自动创建

**Non-Goals:**
- 不做盘库审批流程
- 不做盘库报表统计
- 不做移动端盘点功能

## Decisions

### 1. 盘库数量语义：录入实际数量

**决定**：用户录入实际盘点数量，系统计算差异。

**理由**：
- 符合实际业务场景，仓库人员记录"数了多少"
- 避免用户计算差异时出错
- 系统自动计算更准确

**备选方案**：录入差异数量（盘盈+5，盘亏-5）
- 缺点：用户需要心算，容易出错

### 2. 批量盘库使用批次号

**决定**：每次批量盘库生成唯一批次号（如 SC20260514001）。

**理由**：
- 便于追溯"某次盘库改了哪些库存"
- 支持批次维度统计（共盘点多少、盘盈多少、盘亏多少）
- 单个盘库也生成批次，保持数据一致性

### 3. Excel 模板简化为两列

**决定**：模板只需规格编码 + 盘点数量。

**理由**：
- `spec_code` 在系统中唯一（`unique=True`）
- 可通过规格编码反查商品信息
- 简化用户填写，减少错误

### 4. 不存在的库存自动创建

**决定**：Excel 中有但库存中没有的规格，自动创建库存记录。

**理由**：
- 盘点时可能发现未入库的商品
- 避免用户先手动入库再盘点
- 盘库记录标记 `is_new_stock=true` 便于识别

### 5. 数据模型设计

**StockCheckBatch（盘库批次）**：
```
id              - 批次ID
batch_code      - 批次编号 SC20260514001
warehouse_id    - 仓库ID
check_type      - 类型: single/batch
total_count     - 总数
success_count   - 成功数
fail_count      - 失败数
user_id/user_name - 操作人
created_at/updated_at
```

**StockCheckRecord（盘库记录）**：
```
id              - 记录ID
batch_id        - 关联批次
stock_id        - 库存ID（可能为空，新建的）
warehouse_id    - 仓库ID
product_id/code/name - 商品信息
spec_id/code    - 规格信息
before_quantity - 盘点前数量
check_quantity  - 盘点数量
difference      - 差异
is_new_stock    - 是否新建库存
user_id/user_name - 操作人
remarks         - 备注
created_at/updated_at
```

### 6. API 设计

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stock-checks/single` | POST | 单个盘库 |
| `/api/stock-checks/batch` | POST | 批量盘库（multipart） |
| `/api/stock-checks/template` | GET | 下载模板 |
| `/api/stock-checks/records` | GET | 盘库记录列表 |
| `/api/stock-checks/batches` | GET | 批次列表 |
| `/api/stock-checks/batches/{id}` | GET | 批次详情 |

### 7. 前端交互

**单个盘库入口**：
- 库存列表操作列 → "盘库"按钮
- 库存详情弹窗 → "盘库"按钮

**批量盘库入口**：
- 库存管理页面右上角 → "批量盘库"按钮

**详情展示**：
- 库存详情弹窗新增"盘库记录" Tab
- 与入库记录、出库记录并列

## Risks / Trade-offs

### 风险1：Excel 解析失败
- **风险**：用户上传格式错误的 Excel
- **缓解**：后端严格校验，返回详细错误信息（行号 + 原因）

### 风险2：并发盘库冲突
- **风险**：多人同时盘点同一库存
- **缓解**：使用数据库事务，记录盘点前数量，冲突时提示用户

### 风险3：规格编码不存在
- **风险**：Excel 中的规格编码在系统中不存在
- **缓解**：返回错误信息，不自动创建规格（只创建库存）

### 权衡：批次号增加复杂度
- **权衡**：批次号增加了数据模型复杂度
- **收益**：可追溯、可统计，值得投入
