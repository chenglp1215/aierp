# 省份城市数据 API

> 用于获取中国省份、城市、区县数据，无需登录即可访问

## 基础信息

- **基础路径**: `/api/v1/province-city`
- **认证方式**: 无需认证（公开接口）

---

## 接口列表

### 5.3.1 获取省份列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/province-city/provinces` |
| **Method** | GET |
| **认证** | 无需认证 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取省份列表成功",
  "result": [
    {
      "code": "110000",
      "name": "北京市",
      "cities": ["东城区", "西城区", "崇文区", "宣武区", "朝阳区", "丰台区", "石景山区", "海淀区", "门头沟区", "房山区", "通州区", "顺义区", "昌平区", "大兴区", "怀柔区", "平谷区", "密云区", "延庆区"]
    },
    {
      "code": "120000",
      "name": "天津市",
      "cities": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区", "滨海新区", "宁河区", "静海区", "蓟州区"]
    },
    {
      "code": "310000",
      "name": "上海市",
      "cities": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区", "青浦区", "奉贤区", "崇明区"]
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 省份列表 |
| result[].code | string | 省份代码 |
| result[].name | string | 省份名称 |
| result[].cities | array | 该省份下的城市名称列表 |

---

### 5.3.2 获取城市列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/province-city/cities` |
| **Method** | GET |
| **认证** | 无需认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| province | string | 是 | 省份名称（精确匹配） |

### 请求示例

```
GET /api/v1/province-city/cities?province=北京市
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取城市列表成功",
  "result": [
    {
      "code": "11010001",
      "name": "东城区",
      "province_code": "110000"
    },
    {
      "code": "11010002",
      "name": "西城区",
      "province_code": "110000"
    },
    {
      "code": "11010003",
      "name": "崇文区",
      "province_code": "110000"
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 城市列表 |
| result[].code | string | 城市代码 |
| result[].name | string | 城市名称 |
| result[].province_code | string | 所属省份代码 |

---

### 5.3.3 获取区县列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/province-city/districts` |
| **Method** | GET |
| **认证** | 无需认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| province | string | 是 | 省份名称（精确匹配） |
| city | string | 是 | 城市名称（精确匹配） |

### 请求示例

```
GET /api/v1/province-city/districts?province=北京市&city=东城区
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": [
    {
      "code": "110101001",
      "name": "东华门街道",
      "province_code": "110000",
      "city_code": "11010001"
    },
    {
      "code": "110101002",
      "name": "东四街道",
      "province_code": "110000",
      "city_code": "11010001"
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 区县列表 |
| result[].code | string | 区县代码 |
| result[].name | string | 区县名称 |
| result[].province_code | string | 所属省份代码 |
| result[].city_code | string | 所属城市代码 |

---

### 5.3.4 搜索省/市/区

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/province-city/search` |
| **Method** | GET |
| **认证** | 无需认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（支持省份、城市、区县名称模糊匹配） |

### 请求示例

```
GET /api/v1/province-city/search?keyword=北京
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "搜索地址成功",
  "result": [
    {
      "type": "province",
      "name": "北京市",
      "province": null,
      "city": null
    },
    {
      "type": "city",
      "name": "东城区",
      "province": "北京市",
      "city": null
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 搜索结果列表 |
| result[].type | string | 类型：`province`(省份) / `city`(城市) / `district`(区县) |
| result[].name | string | 名称 |
| result[].province | string | 所属省份（区县级返回） |
| result[].city | string | 所属城市（区县级返回） |

---

## 数据代码规则

### 省份代码

省份代码为6位数字，前2位对应行政区划代码：

| 省份 | 代码范围 |
|------|----------|
| 华北地区 | 11xxxxxx - 15xxxxxx |
| 东北地区 | 21xxxxxx - 23xxxxxx |
| 华东地区 | 31xxxxxx - 37xxxxxx |
| 华中地区 | 41xxxxxx - 43xxxxxx |
| 华南地区 | 44xxxxxx - 46xxxxxx |
| 西南地区 | 50xxxxxx - 54xxxxxx |
| 西北地区 | 61xxxxxx - 65xxxxxx |

### 城市代码

城市代码为8位数字，结构为：`PPCCNNNN`
- PP: 省份代码前2位
- CC: 省市标识（01-99）
- NNNN: 城市序号（0001-9999）

### 区县代码

区县代码为9位或12位数字，结构为：`PPCCDDNNN` 或 `PPCCDDNNNN`
- PP: 省份代码前2位
- CC: 城市代码第3-4位
- DD: 区县序号（01-99）
- NNN/NNNN: 街道/乡镇序号
