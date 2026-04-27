---
name: 工具生成技能 (Tools Build Skill)
description: 当用户需要生成内置工具，或系统的数据结构、业务逻辑发生变化需要创建/修改工具时，触发本技能。
trigger_conditions:
  - 用户明确要求创建新工具
  - 系统数据结构变更（新增字段、修改字段、删除字段）
  - 业务逻辑变更（新增业务规则、修改业务流程）
  - 用户询问工具相关问题
---

# 技能描述

当用户需要生成内置工具，或系统的数据结构、业务逻辑发生变化需要创建/修改工具时，触发本技能。

## 触发条件

- 用户明确要求创建新工具
- 系统数据结构变更（新增字段、修改字段、删除字段）
- 业务逻辑变更（新增业务规则、修改业务流程）
- 用户询问工具相关问题

---

## 第一部分：识别工具需求和设计工具

### 1.1 需求分析

首先需要识别这次创建工具的范围和使用场景，当前项目中的所有工具都是为了让AI大模型调用从而完成ERP系统业务的操作。

### 1.2 影响范围

每次生成工具，应该识别出来这次工具的涉及到的范围，是否有其他业务模块涉及到改工具对应的资源信息？
需要对当前整体项目中的已有工具做个分析，看看待生成的或者待更新的工具在ERP的工作流程上下游是否有其他工具依赖于它。且需要调整的。

### 1.3 工具设计和确定

每个工具的需要有其独特的功能和作用，不要跟其他工具有功能的模糊重叠的部分。如果有的话，要考虑是否重构工具的功能范围。

---

## 第二部分：工具设计

### 2.1 工具定义

**工具名称**： 工具名称需要符合Python的命名规范，使用下划线分隔单词。不能跟已有的工具重复

**工具中文名**： 工具的cn_name应该符合中文的命名规范，使用中文的命名规范。中文命名需要简洁且清晰，不能包含复杂的词汇。

**工具功能描述**： 工具的description应该符合中文的规范，功能描述简洁清晰，不能有歧义的词汇，要能准确描述工具的功能和适用场景。

**权限码**： 工具的permission_code应该符合"资源.操作"的设计规范，例如"customer.view"。不能跟已有的工具权限码重复。可以多级，比如"customer.name.edit"。

### 2.3 工具返回值

```json
{
  "success": true,
  "content": "[返回内容描述]"
}
```

工具返回的内容一定需要有数据尽量详细的信息，包括数据ID之类的，便于后续交互带上准确的数据标识，从而业务连续操作。

### 2.4 错误处理

| 错误情况 | 处理方式 |
|----------|----------|
| [填写] | [填写] |

---

## 第三部分：代码实现

### 3.1 工具类实现

**文件路径**：`app/agent/tools/[模块名].py`

**代码框架**：

```python
from typing import Optional
from .base import BaseTool, ToolResult


class [工具名]Tool(BaseTool):
    """工具描述"""

    name = "[工具英文名]"
    cn_name = "[工具中文名]"
    description = "[工具功能描述]"
    permission_code = "[权限码]"

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        # TODO: 实现具体逻辑
        pass

    def _validate_params(self, **kwargs) -> bool:
        """参数校验"""
        # TODO: 实现参数校验
        pass
```

---

## 第四部分：工具权限注册

**工具权限注册**： 工具的权限码permission_code, 因为会跟用户的权限进行匹配，所以需要在默认的权限全集中确认存在，不存在的需要在初始化权限中增加。

---

## 第五部分：工具注册

### 5.1 注册到工具注册表

**文件路径**：`app/agent/tools/__init__.py` 或 `app/agent/tools/registry.py`

**注册代码**：

```python
from .[模块名] import [工具名]Tool

tool_registry.register([工具名]Tool())
```

---

## 第六部分：测试验证

### 6.1 功能测试

- [ ] 工具能正常调用
- [ ] 参数校验生效
- [ ] 返回数据格式正确
- [ ] 权限控制生效

### 6.2 边界测试

- [ ] 空值处理
- [ ] 异常数据处理
- [ ] 并发调用处理

---

## 第七部分：文档更新

### 7.1 需要更新的文档

- [ ] [PROJECT_ARCHITECTURE.md](file:///e:/wechat-bot-dev/sale_assistant/vibecoding/ai_mdr_platform/PROJECT_ARCHITECTURE.md) - 更新模块依赖关系
- [ ] [README.md](file:///e:/wechat-bot-dev/sale_assistant/vibecoding/ai_mdr_platform/README.md) - 更新功能说明
- [ ] AGENT_PROMPT.md - 更新示例（如需要）

### 7.2 更新内容描述

[填写需要更新的具体内容]

---

## 第八部分：部署注意事项

[填写部署时需要注意的事项]

---

## 附录：现有工具参考

现有内置工具位于 `app/agent/tools/` 目录：

| 工具名 | 功能 | 权限码 |
|--------|------|--------|
| customer_tool | 客户管理 | customer.view/edit |
| product_tool | 商品管理 | product.view/edit |
| sales_order_tool | 销售订单 | order.view/confirm |
| inventory_tool | 库存管理 | inventory.view |
| [填写] | [填写] | [填写] |
