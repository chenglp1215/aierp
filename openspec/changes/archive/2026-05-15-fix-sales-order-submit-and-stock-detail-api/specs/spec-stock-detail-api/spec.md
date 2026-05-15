## ADDED Requirements

### Requirement: 查询规格库存详情

系统 SHALL 提供根据规格 ID 查询库存详情的 API 接口。

**接口定义**：
- 路径：`GET /api/v1/products/specs/{spec_id}/stock-detail`
- 权限：需要 `product.view` 权限

**返回格式**：
```json
{
  "status": "success",
  "message": "",
  "result": {
    "spec_id": 4,
    "items": [
      {
        "warehouse_id": 1,
        "warehouse_name": "主仓库",
        "quantity": 100
      }
    ],
    "total_quantity": 100
  }
}
```

#### Scenario: 查询存在的规格库存
- **WHEN** 用户请求 `GET /api/v1/products/specs/4/stock-detail`
- **THEN** 系统返回该规格在各仓库的库存信息

#### Scenario: 查询不存在的规格
- **WHEN** 用户请求 `GET /api/v1/products/specs/99999/stock-detail`
- **THEN** 系统返回空列表，`items` 为空数组，`total_quantity` 为 0

#### Scenario: 未授权访问
- **WHEN** 用户未登录或无 `product.view` 权限
- **THEN** 系统返回 401 或 403 错误
