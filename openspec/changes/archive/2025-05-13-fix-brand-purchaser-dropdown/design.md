## Context

品牌管理功能需要为品牌指定采购人员。采购人员是系统中具有 `purchaser_group` 角色的用户。当前前端已实现采购人员选择下拉框，但后端缺少对应的 API 接口。

**当前状态**:
- 前端 `BrandWorkspace.vue` 在 `onMounted` 时调用 `brandApi.getPurchaserCandidates()`
- 前端 API 定义了 `GET /brands/purchaser-candidates` 接口调用
- 后端 `brand_router` 中缺少该路由定义
- 用户服务 `MySQLUserService` 已支持按角色过滤用户列表

## Goals / Non-Goals

**Goals:**
- 新增 `GET /brands/purchaser-candidates` 接口
- 返回采购组角色（`purchaser_group`）的用户列表
- 支持可选的 `keyword` 参数搜索用户

**Non-Goals:**
- 不修改前端代码（前端已正确实现）
- 不修改数据库结构
- 不修改采购组角色的定义或权限

## Decisions

### 1. 接口位置

**决定**: 在 `brand_router` 中添加 `/purchaser-candidates` 路由

**理由**:
- 该接口专门服务于品牌管理功能
- 前端已预期接口路径为 `/brands/purchaser-candidates`
- 保持与现有代码组织一致

**备选方案**:
- 在 `auth_router` 中添加 `/users/by-role` 通用接口
  - 优点：更通用，可复用
  - 缺点：需要修改前端 API 调用路径
  - 决定：不采用，保持前端不变

### 2. 数据查询方式

**决定**: 复用 `MySQLUserService.list_users()` 方法，使用 `role='purchaser_group'` 参数

**理由**:
- 现有方法已支持按角色过滤
- 已实现分页、关键字搜索等功能
- 代码复用，减少重复实现

### 3. 返回数据格式

**决定**: 返回简化的用户信息列表，仅包含 `id`、`full_name`、`username`

**理由**:
- 前端下拉框只需要这些字段
- 减少数据传输量
- 与前端 `PurchaserCandidate` 接口定义一致

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 采购组角色不存在 | 接口返回空列表，不抛出错误 |
| 用户量大时性能问题 | 接口仅返回活跃状态用户，后续可加分页 |
| 角色编码硬编码 | 使用常量定义角色编码，便于维护 |
