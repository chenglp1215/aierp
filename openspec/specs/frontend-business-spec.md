# 前端项目业务说明

<!-- 变更日期: 2026-05-05 -->

> 本文档说明前端业务流转规则、业务注意事项和业务约束。随业务调整实时更新。

---

## 1. 页面导航结构

### 侧边栏菜单

```
首页 (Dashboard)
AI 助手 (Chat)
销售管理
├── 销售订单
├── 客户管理
└── 客户折扣
采购管理
├── 采购单
└── 供应商
库存管理
├── 库存总览
└── 仓库管理
财务管理
├── 应收款
└── ...
系统管理
├── 用户管理
├── 角色管理
└── 权限管理
AI 设置
├── Agent 配置
├── LLM 设置
├── 技能设置
├── 知识库
└── MCP 设置
```

### 菜单权限控制

- 菜单显示受 `menu` 类型权限控制
- 权限代码映射定义在 `hooks/usePermission.ts` 的 `MENU_PERMISSION_MAP` 中
- admin/super_admin 角色显示所有菜单
- 无权限的菜单项自动隐藏

---

## 2. 业务流转说明

### 销售订单流程

```
创建订单 → 填写客户/商品信息 → 保存草稿(DRAFT)
    ↓
确认订单 → 状态变为 CONFIRMED
    ↓
发货 → 状态变为 DELIVERED → 触发出库操作
    ↓
结算 → 状态变为 SETTLED → 生成应收款记录
    ↓
完成 → 状态变为 COMPLETED
```

**前端操作**：
- 创建：`SalesOrderCreate.vue` 组件
- 列表：`SalesOrderList.vue` 支持状态筛选
- 状态变更：通过 API 调用 `updateOrderStatus`

### 采购单流程

```
从销售订单推送 → 选择商品项 → 预览采购单 → 确认创建
    ↓
确认采购单 → 状态变为 CONFIRMED
    ↓
到货入库 → 触发库存入库操作
    ↓
结算/完成
```

**前端操作**：
- 推送创建：`PushPurchaseItemSelectModal.vue` + `PushPurchasePreviewModal.vue`
- 列表管理：`PurchaseOrderWorkspace.vue`

### 库存管理流程

```
查看库存 → 库存总览页面
    ↓
入库操作 → 选择仓库 → 输入商品/数量 → 确认入库
    ↓
出库操作 → 选择仓库 → 输入商品/数量 → 确认出库
    ↓
库存调整 → 手动调整库存数量
```

**前端操作**：
- 库存查看：`InventoryWorkspace.vue`
- 仓库管理：`WarehouseWorkspace.vue`

---

## 3. 业务注意事项

### 认证与权限

- Token 存储在 `localStorage`，包含 `token`、`user`、`token_expires_at`
- 退出登录需清除所有认证数据（包括 `remembered_username`、`remembered_password`）
- 侧边栏菜单根据用户权限动态显示/隐藏
- 操作按钮根据 `button` 类型权限控制显示

### 数据展示

- 商品列表使用 vxe-table 垂直展开模式（一个商品多规格）
- 序号按商品显示，非按行显示
- 状态标签使用颜色区分（在售/停用）

### 表单交互

- 编辑成功后直接更新列表对应项，不重新加载整个列表
- 删除成功后从列表 filter 移除
- 新建操作需刷新列表获取后端生成的 id
- 使用 Toast 替代 alert()

### 主题适配

- 支持 `light` 和 `dark` 两种主题
- 组件样式需同时适配两种主题
- vxe-table 分页器、加载覆盖层等需主题适配

---

## 4. 已知注意事项

### 历史代码清理

- `SalesOrderList.vue` 已被 `SalesOrderWorkspace.vue` 可能取代，需确认是否可删除
- `customer.py`（v1）与 `customer_v2.py` 共存，前端使用 v2

### 全局样式冲突

- vxe-table 的 hover 效果来自全局样式 `global.css`
- 需要覆盖时使用 `!important` + 更具体的选择器
- 示例：覆盖 hover 高亮需在组件 `<style>` 中添加

```css
.vxe-table .vxe-table--body tr:hover,
.vxe-table .vxe-table--body tr:hover > td {
  background-color: transparent !important;
}
```

### WebSocket 连接

- AI 聊天使用 WebSocket 实时通信
- 消息类型：`text`（文本）、`tool_call_start`（工具开始）、`tool_call_end`（工具结束）、`error`（错误）