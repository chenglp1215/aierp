## 1. 数据库初始化脚本完善

- [ ] 1.1 在 `init_db_sync.py` 中添加 `init_warehouse_admin_role` 函数
- [ ] 1.2 在 `init_db_sync.py` 中添加 `init_purchaser_group_role` 函数
- [ ] 1.3 在 `init_db_sync.py` 中添加 `init_default_user_role` 函数
- [ ] 1.4 在 `main` 函数中调用新增的三个角色初始化函数
- [ ] 1.5 运行初始化脚本验证角色创建

## 2. 用户设置弹窗组件开发

- [ ] 2.1 创建 `web/src/components/UserSettingsDialog.vue` 组件
- [ ] 2.2 实现弹窗 UI 布局（用户名、邮箱、手机、姓名、角色、新密码）
- [ ] 2.3 实现字段只读/可编辑状态控制
- [ ] 2.4 实现表单验证逻辑（邮箱格式、密码长度）
- [ ] 2.5 实现保存功能，调用 `authApi.updateUser` 接口

## 3. 集成到 DashboardHeader

- [ ] 3.1 在 `DashboardHeader.vue` 中引入 `UserSettingsDialog` 组件
- [ ] 3.2 处理设置按钮点击事件，打开弹窗
- [ ] 3.3 处理弹窗保存成功后的回调

## 4. 测试验证

- [ ] 4.1 验证数据库初始化脚本创建 4 个固定角色
- [ ] 4.2 验证用户设置弹窗正确展示当前用户信息
- [ ] 4.3 验证邮箱和密码编辑保存功能