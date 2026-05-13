## Why

当前简化版数据库初始化脚本只创建了超级管理员角色，缺少原有的仓库管理员、采购组、普通用户三个固定角色。同时，用户登录后点击右上角设置按钮没有实际功能，需要实现用户个人信息查看和编辑功能。

## What Changes

### 1. 数据库初始化脚本完善
- 恢复 `warehouse_admin`（仓库管理员）角色及其权限
- 恢复 `purchaser_group`（采购组）角色及其权限
- 恢复 `user`（普通用户）角色及其权限
- 保持幂等性：已存在则跳过

### 2. 用户设置弹窗功能
- 点击右上角用户头像下拉菜单的"设置"按钮，弹出用户信息弹窗
- 弹窗展示：用户名、邮箱、手机、姓名、角色（只读）、新密码（可编辑）
- 只有邮箱和新密码可编辑，其他字段只读展示
- 保存时调用后端 API 更新当前用户信息

## Capabilities

### New Capabilities

- `user-settings-dialog`: 用户设置弹窗功能，允许用户查看和编辑自己的个人信息（邮箱、密码）

### Modified Capabilities

无（数据库初始化脚本是内部实现细节，不涉及 spec 级别的需求变更）

## Impact

- **后端脚本**: `backend/scripts/init_db_sync.py` - 添加三个固定角色的初始化逻辑
- **前端组件**: `web/src/components/DashboardHeader.vue` - 处理设置按钮点击事件
- **前端组件**: 新建 `web/src/components/UserSettingsDialog.vue` - 用户设置弹窗组件
- **后端 API**: 复用现有的 `PUT /api/v1/users/{user_id}` 接口更新用户信息