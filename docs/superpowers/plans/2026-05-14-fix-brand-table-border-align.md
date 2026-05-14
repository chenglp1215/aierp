# 品牌表格边框对齐修复 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复品牌管理页面表格中"描述"列下边框与其他列不对齐的问题

**Architecture:** 移除描述列的 `class-name="col--middle"` 属性，让 vxe-table 使用默认的垂直对齐方式

**Tech Stack:** Vue 3, vxe-table 4, CSS

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `web/src/components/workspace/BrandWorkspace.vue` | 修改 | 移除描述列的 class-name 属性 |

---

### Task 1: 移除描述列的垂直居中类名

**Files:**
- Modify: `web/src/components/workspace/BrandWorkspace.vue:260`

- [ ] **Step 1: 移除 class-name 属性**

将第 260 行的描述列定义从：
```vue
<vxe-column field="description" title="描述" min-width="200" show-overflow="tooltip" class-name="col--middle">
```

修改为：
```vue
<vxe-column field="description" title="描述" min-width="200" show-overflow="tooltip">
```

- [ ] **Step 2: 验证修改**

确认修改后的代码：
```vue
<vxe-column field="description" title="描述" min-width="200" show-overflow="tooltip">
  <template #default="{ row }">
    {{ row.description || '-' }}
  </template>
</vxe-column>
```

- [ ] **Step 3: 提交修改**

```bash
git add web/src/components/workspace/BrandWorkspace.vue
git commit -m "fix: 修复品牌表格描述列边框对齐问题"
```

---

### Task 2: 验证修复效果

**Files:**
- 无文件修改，仅验证

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd web && npm run dev
```

- [ ] **Step 2: 在浏览器中检查品牌管理页面**

访问品牌管理页面，确认：
1. 表格所有列的下边框对齐一致
2. 描述列内容正常显示
3. 其他表格功能正常（筛选、分页、编辑等）

- [ ] **Step 3: 确认修复完成**

截图对比修复前后效果，确认问题已解决。