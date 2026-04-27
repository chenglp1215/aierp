***

name: 工具生成技能 (Tools Build Skill)
description: 当用户需要生成内置工具，或系统的数据结构、业务逻辑发生变化需要创建/修改工具时，触发本技能。
-----------------------------------------------------------

# 技能描述

当用户需要生成内置工具，或系统的数据结构、业务逻辑发生变化需要创建/修改工具时，触发本技能。

## 触发条件

- 用户明确要求创建新工具
- 系统数据结构变更（新增字段、修改字段、删除字段）
- 业务逻辑变更（新增业务规则、修改业务流程）
- 用户询问工具相关问题

***

## 核心设计原则

### 1. 返回数据详细且含ID标识

- 详情类方法必须返回完整业务数据，包含关联数据的ID
- 返回数据中必须包含 数据业务id 或 数据库`id` 或 `_id` 字段，优先返回业务id，数据库id作为备选，便于后续交互操作
- 避免大模型多次调用获取关联数据

### 2. 业务耦合原则

- 功能联系紧密的操作应合并为一个工具，避免多次调用
- 例如：客户详情应同时包含基本信息+联系人+地址等关联数据
- 工具设计要站在业务流角度，而非单纯CRUD角度

### 3. 入参精简准确

- 参数说明必须包含：含义、类型、是否必填、示例值
- 只保留必要参数，避免参数过多导致大模型调用困惑
- 参数名使用下划线命名，说明使用中文

### 4. 返回值清晰说明

- 必须说明返回数据的结构和每个字段的含义
- 返回内容需简洁，避免返回大量无关数据占用上下文
- 返回格式统一为 `{ success, content, metadata? }`

***

## 第一部分：识别工具需求和设计工具

### 1.1 需求分析

首先需要识别这次创建工具的范围和使用场景，当前项目中的所有工具都是为了让AI大模型调用从而完成ERP系统业务的操作。

### 1.2 影响范围

每次生成工具，应该识别出来这次工具的涉及到的范围，是否有其他业务模块涉及到改工具对应的资源信息？
需要对当前整体项目中的已有工具做个分析，看看待生成的或者待更新的工具在ERP的工作流程上下游是否有其他工具依赖于它。且需要调整的。

### 1.3 工具设计和确定

每个工具的需要有其独特的功能和作用，不要跟其他工具有功能的模糊重叠的部分。如果有的话，要考虑是否重构工具的功能范围。

***

## 第二部分：工具设计

### 2.1 工具定义

| 属性         | 要求               | 示例                         |
| ---------- | ---------------- | -------------------------- |
| **工具名称**   | Python命名规范，下划线分隔 | `customer_search`          |
| **工具中文名**  | 中文简洁清晰           | "搜索客户"                     |
| **工具功能描述** | 准确描述功能和适用场景      | "搜索客户信息，当用户查询客户列表、筛选客户时使用" |
| **权限码**    | "资源.操作"格式        | `customer.view`            |

### 2.2 参数设计

**参数规范要求：**

- 只保留必要参数，控制在5个以内
- 每个参数必须包含：参数名、类型、是否必填、说明、示例

**参数定义模板：**

```json
{
  "参数名": {
    "type": "string",
    "description": "参数说明",
    "required": true/false,
    "example": "示例值"
  }
}
```

**示例 - 客户搜索工具参数：**

```json
{
  "keyword": {
    "type": "string",
    "description": "搜索关键词（客户名称、编码、电话）",
    "required": false,
    "example": "张三"
  },
  "page": {
    "type": "integer",
    "description": "页码，默认1",
    "required": false,
    "example": 1
  }
}
```

### 2.3 返回值设计

**返回值结构：**

```json
{
  "success": true,
  "content": "数据内容描述",
  "metadata": {
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

**返回值要求：**

- `content`: 返回业务数据描述，列表类型返回条数说明
- `metadata`: 包含分页、统计等元数据
- 详情类返回必须包含 数据业务id 或 数据库`id` 或 `_id` 字段，优先返回业务id，数据库id作为备选
- 避免返回完整对象大数据，占用上下文

**示例 - 客户搜索返回：**

```
共找到 3 个客户：
1. [ID:xxx] 客户名称: 张三公司 | 联系人: 张三 | 电话: 13800138000
2. [ID:xxx] 客户名称: 李四公司 | 联系人: 李四 | 电话: 13900139000
3. [ID:xxx] 客户名称: 王五公司 | 联系人: 王五 | 电话: 13700137000
```

### 2.4 错误处理

| 错误情况  | 处理方式                        |
| ----- | --------------------------- |
| 参数缺失  | 返回错误提示，说明缺少哪些必填参数           |
| 数据不存在 | 返回空列表或空数据，success仍为true     |
| 权限不足  | 返回success=false，error说明权限不足 |
| 系统异常  | 返回success=false，error包含错误信息 |

***

## 第三部分：代码实现

### 3.1 工具类实现

**文件路径**：`app/agent/tools/[模块名].py`

**代码框架**：

```python
from typing import Optional
import logging
from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CustomerSearchTool(BaseTool):
    """搜索客户信息"""

    name = "customer_search"
    cn_name = "搜索客户"
    description = "搜索客户信息。当用户查询客户列表、筛选客户、根据名称或电话搜索客户时使用。"
    permission_code = "customer.view"

    parameters = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词（客户名称、编码、电话）",
                "example": "张三"
            },
            "page": {
                "type": "integer",
                "description": "页码，默认1",
                "default": 1
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量，默认20",
                "default": 20
            }
        },
        "required": []
    }

    async def execute(
        self,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"搜索客户: keyword={keyword}, page={page}")

            result = await customer_service.search_customers(
                keyword=keyword,
                page=page,
                page_size=page_size
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(success=True, content="未找到客户记录")

            content_lines = [f"共找到 {result.get('total', 0)} 个客户："]
            for customer in items[:10]:
                content_lines.append(
                    f"[ID:{customer.get('customer_id', customer.get('id', customer.get('_id') or '无'))}] "
                    f"名称: {customer.get('name')} | "
                    f"联系人: {customer.get('contact_person', '无')} | "
                    f"电话: {customer.get('contact_phone', '无')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={
                    "total": result.get("total", 0),
                    "page": page,
                    "page_size": page_size
                }
            )

        except Exception as e:
            logger.error(f"搜索客户失败: {e}")
            return ToolResult(success=False, content="", error=str(e))
```

### 3.2 业务耦合示例

**不好的设计（过度拆分）：**

- `get_customer_basic` - 获取客户基本信息
- `get_customer_contacts` - 获取客户联系人
- `get_customer_addresses` - 获取客户地址
- `get_customer_orders` - 获取客户订单

**好的设计（业务耦合）：**

```python
class CustomerDetailTool(BaseTool):
    """获取客户详情"""
    # 一个工具返回客户完整信息，包括联系人、地址、最近订单
```

***

## 第四部分：工具权限注册

**权限码规范**：

- 格式：`资源.操作`，如 `customer.view`、`product.edit`
- 工具权限码必须在 `app/__init__.py` 的 `init_default_permissions` 中存在
- 如果权限不存在，需要添加新的权限定义

**权限注册检查清单**：

- [ ] 确认工具的 `permission_code` 在默认权限列表中
- [ ] 如果不存在，在 `init_default_permissions` 中添加
- [ ] 权限类型为 `button`，sort\_order 放在对应模块菜单权限之后

***

## 第五部分：工具注册

### 5.1 注册到工具注册表

**文件路径**：`app/agent/tools/__init__.py`

**注册代码**：

```python
from .customer import CustomerSearchTool

tool_registry.register(CustomerSearchTool())
```

### 5.2 统一注册入口

在 `app/agent/tools/builtin.py` 的 `register_business_tools()` 函数中统一注册所有业务工具。

***

## 第六部分：测试验证

### 6.1 功能测试

- [ ] 工具能正常调用
- [ ] 参数校验生效（必填参数缺失时提示）
- [ ] 返回数据格式正确（包含id标识）
- [ ] 权限控制生效（无权限时正确拒绝）

### 6.2 边界测试

- [ ] 空值处理（无数据时返回空列表）
- [ ] 异常数据处理（非法参数格式）
- [ ] 分页边界测试（page超过总页数）

***

## 第七部分：文档更新

### 7.1 需要更新的文档

- [ ] [PROJECT\_ARCHITECTURE.md](file:///e:/wechat-bot-dev/sale_assistant/vibecoding/ai_mdr_platform/PROJECT_ARCHITECTURE.md) - 更新工具模块说明
- [ ] [AGENT\_PROMPT.md](file:///e:/wechat-bot-dev/sale_assistant/vibecoding/ai_mdr_platform/backend/tests/AGENT_PROMPT.md) - 更新工具使用示例

### 7.2 更新内容描述

新增工具需要记录：

- 工具名称和功能描述
- 权限码
- 关联的权限配置变更

***

## 第八部分：部署注意事项

- 新增工具权限后，需要清空 `permissions` 集合重启服务重新初始化
- 或手动在数据库中插入新的权限记录

***

## 附录：现有工具参考

现有内置工具位于 `app/agent/tools/` 目录：

| 工具名                  | 功能   | 权限码                  | 返回数据说明       |
| -------------------- | ---- | -------------------- | ------------ |
| customer\_search     | 搜索客户 | customer.view        | 返回客户列表，每条含ID |
| customer\_detail     | 客户详情 | customer.view        | 返回完整客户信息含联系人 |
| product\_search      | 搜索商品 | product.view         | 返回商品列表，每条含ID |
| sales\_order\_search | 搜索订单 | order.view           | 返回订单列表，每条含ID |
| inventory\_search    | 搜索库存 | inventory.stock.view | 返回库存数据，含商品ID |

**工具设计检查清单：**

- [ ] 返回数据是否包含 数据业务id 或 数据库`id` 或 `_id` 字段，优先返回业务id，数据库id作为备选
- [ ] 参数说明是否包含 `example`
- [ ] 是否避免了不必要的多次调用
- [ ] 权限码是否已在默认权限中配置

