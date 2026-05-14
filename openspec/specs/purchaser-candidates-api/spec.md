## ADDED Requirements

### Requirement: 获取采购组用户候选列表

系统 SHALL 提供 `GET /brands/purchaser-candidates` 接口，返回采购组角色（`purchaser_group`）的用户列表。

#### Scenario: 成功获取采购组用户列表
- **WHEN** 用户请求 `GET /brands/purchaser-candidates`
- **THEN** 系统返回状态为 `active` 且角色为 `purchaser_group` 的用户列表
- **AND** 每个用户包含 `id`、`full_name`、`username` 字段

#### Scenario: 使用关键字搜索采购组用户
- **WHEN** 用户请求 `GET /brands/purchaser-candidates?keyword=张`
- **THEN** 系统返回采购组用户中用户名或姓名包含"张"的用户列表

#### Scenario: 采购组角色不存在时返回空列表
- **WHEN** 系统中没有 `purchaser_group` 角色
- **THEN** 系统返回空列表 `[]`

#### Scenario: 无权限用户访问接口
- **WHEN** 未认证用户请求 `GET /brands/purchaser-candidates`
- **THEN** 系统返回 401 错误

### Requirement: 采购人员候选数据格式

系统 SHALL 返回符合前端接口定义的用户数据格式。

#### Scenario: 返回数据字段
- **WHEN** 系统返回采购人员候选列表
- **THEN** 每个用户对象包含以下字段：
  - `id`: 用户ID（字符串）
  - `full_name`: 用户姓名
  - `username`: 用户名
