## Why

品牌管理编辑功能中，采购人员下拉框无法加载采购组用户信息。原因是后端缺少 `/brands/purchaser-candidates` 接口，前端调用该接口时返回 404 错误。

## What Changes

- 后端新增 `GET /brands/purchaser-candidates` 接口，返回采购组角色（`purchaser_group`）的用户列表
- 接口支持可选的 `keyword` 参数用于搜索用户

## Capabilities

### New Capabilities

- `purchaser-candidates-api`: 获取采购组用户候选列表的 API 接口

### Modified Capabilities

- 无（这是新增接口，不修改现有功能）

## Impact

- **后端**: `backend/app/routers/product.py` - 新增 `purchaser-candidates` 路由
- **后端**: `backend/services/auth_service.py` - 可能需要在 `MySQLUserService` 中添加按角色编码查询用户的方法
- **前端**: 无需修改（前端已正确调用该接口）
