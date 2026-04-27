---
name: form-submission-workflow
description: |
  当你需要做任何工具调用之前，先调用此技能。
---

# 数据提交类操作工作流

当需要执行提交、更新、删除等数据提交类操作时，按照以下步骤进行：

## 工作流程

1. **查找工具** - 从用户提供的工具中查找完成操作需要用到的工具
2. **提取数据** - 从用户提供的信息中提取提交的数据信息，可选步骤，如果没有需要提取的数据，直接跳转到第3步
3. **校验参数** - 根据需要调用的工具的参数说明，判断参数数据是否满足要求
4. **构建表单** - 构建表单JSON格式，包含参数字段、字段类型、描述、提交值
  构建表单字段的原则：
  - 字段要方便用户填写，要避免让用户填写ID, 英文编号等不方便的字段。
  - 尽量提供options选择项，选择项也应该是便于用户读取的。
  - 可以将多个相关字段组合在一起，形成一个字段项，例如联系人信息（包含了姓名、手机号、邮箱等）。
5. **生成提示** - 构建给用户的提示语句（text）和下一步动作（next_step）
6. **返回结果** - 将整个表单JSON做json_dumps后前面拼接"form_result:"后返回给用户

## 表单JSON结构

```json
{
  "text": "给用户的提示语句，说明当前状态和需要补充的信息",
  "form_data": {
    "字段名": {
      "type": "字段类型（string/number/boolean等）",
      "description": "字段描述",
      "value": "用户提供的值，如果没有则为空字符串",
      "options": ["选项列表（可选，用于下拉选择）"],
      "default": "默认值（可选）"
    }
  },
  "next_step": "下一步动作描述"
}
```

## 示例

### 示例1：客户不存在，需要先创建

**用户输入：**
> 给上海科技大学下个单，买戴尔电脑3台。

**助手响应：**
```json
form_result:{
  "text": "我将帮你创建一个客户，并提交订单，因为系统没有对应的客户信息，我需要创建客户信息，请先确认一下客户创建的信息是否正确，并填写缺失的属性，确认无误后，我会自动帮你执行创建客户",
  "form_data": {
    "name": {
      "type": "string",
      "description": "客户名称（必填）",
      "value": "上海科技大学"
    },
    "customer_type": {
      "type": "string",
      "description": "客户类型：enterprise(企业)、individual(个人)",
      "default": "enterprise",
      "value": "enterprise"
    },
    "level": {
      "type": "string",
      "description": "客户级别：vip(VIP)、potential(潜在)、normal(普通)",
      "default": "normal",
      "value": "normal"
    },
    "contact_person": {
      "type": "string",
      "description": "联系人",
      "value": ""
    }
  },
  "next_step": "创建客户，然后提交订单"
}
```

### 示例2：客户已存在，直接创建订单

**用户输入：**
> 给上海科技大学下个单，买戴尔电脑3台。

**助手响应：**
```json
form_result:{
  "text": "我查到了系统对应的客户信息-》上海科技大学，我将提交销售订单，另外还需要具体的以下信息，请补充一下",
  "form_data": {
    "customer_name": {
      "type": "string",
      "description": "客户名称（必填）",
      "value": "上海科技大学"
    },
    "delivery_type": {
      "type": "string",
      "description": "发货方式",
      "value": "",
      "options": ["西安仓", "北京仓", "采购直发"]
    },
    "items": [
      {
        "product_name": {
          "type": "string",
          "description": "产品名称",
          "value": "戴尔电脑"
        },
        "quantity": {
          "type": "number",
          "description": "规格数量",
          "value": 3
        }
      }
    ],
    "contact": {
      "type": "string",
      "description": "联系信息",
      "value": ""
    }
  },
  "next_step": "提交订单"
}
```

## 关键原则

- **text字段**：清晰说明当前状态、需要用户确认或补充什么信息
- **form_data字段**：只包含与当前操作相关的必填和可选字段
- **value字段**：从用户输入中提取已有值，未提供的字段留空
- **next_step字段**：简明扼要地说明下一步将执行什么操作
- 复杂对象（如items数组）可以嵌套在form_data中
