# 品牌管理列表视图重构 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将品牌管理从卡片网格布局改为 vxe-table 表格列表，保持与商品管理风格一致。

**Architecture:** 重构 BrandWorkspace.vue 组件，将卡片网格布局替换为 vxe-table 表格组件。保留现有的筛选、搜索、分页和弹窗功能，仅修改列表展示部分。

**Tech Stack:** Vue 3, TypeScript, vxe-table 4, Composition API + `<script setup lang="ts">`

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `web/src/components/workspace/BrandWorkspace.vue` | 修改 | 重构模板和样式，将卡片网格改为表格 |

---

### Task 1: 重构模板 - 将卡片网格替换为 vxe-table

**Files:**
- Modify: `web/src/components/workspace/BrandWorkspace.vue` (template 部分)

- [ ] **Step 1: 替换品牌内容区域为表格结构**

将原有的 `.brand-grid` 卡片网格区域替换为 vxe-table 表格。找到模板中的 `<div class="brand-content">` 部分，替换为：

```vue
<div class="brand-content">
  <div v-if="loading" class="loading-state">
    <div class="loading-spinner"></div>
    <span>加载中...</span>
  </div>
  <div v-else-if="brands.length === 0" class="empty-state">
    <div class="empty-icon">🏷️</div>
    <p>暂无品牌数据</p>
    <button class="primary-btn" @click="openCreate">新建第一个品牌</button>
  </div>
  <div v-else class="table-section">
    <vxe-table
      :data="brands"
      :column-config="{ resizable: true }"
    >
      <vxe-column title="Logo" width="80" class-name="col--center">
        <template #default="{ row }">
          <div class="brand-logo-cell">
            <img v-if="row.logo_url" :src="row.logo_url" :alt="row.name" />
            <div v-else class="logo-placeholder">{{ row.name.charAt(0).toUpperCase() }}</div>
          </div>
        </template>
      </vxe-column>
      <vxe-column field="name" title="品牌名称" min-width="150" />
      <vxe-column field="description" title="描述" min-width="200" show-overflow="tooltip">
        <template #default="{ row }">
          {{ row.description || '-' }}
        </template>
      </vxe-column>
      <vxe-column field="purchaser_name" title="采购人员" min-width="100">
        <template #default="{ row }">
          {{ row.purchaser_name || '-' }}
        </template>
      </vxe-column>
      <vxe-column field="is_active" title="状态" width="80" class-name="col--center">
        <template #default="{ row }">
          <span :class="['status-tag', row.is_active ? 'active' : 'inactive']">
            {{ row.is_active ? '启用' : '停用' }}
          </span>
        </template>
      </vxe-column>
      <vxe-column field="product_count" title="商品数量" width="80" class-name="col--center">
        <template #default="{ row }">
          {{ row.product_count || 0 }}
        </template>
      </vxe-column>
      <vxe-column field="updated_at" title="更新时间" width="140">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </vxe-column>
      <vxe-column title="操作" width="180" fixed="right" class-name="col--center">
        <template #default="{ row }">
          <span class="action-btns">
            <button class="btn-link" @click="openEdit(row)">编辑</button>
            <button class="btn-link" @click="handleToggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </button>
            <button class="btn-link danger" @click="confirmDelete(row)">删除</button>
          </span>
        </template>
      </vxe-column>
    </vxe-table>

    <vxe-pager
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :layouts="['PrevPage', 'JumpNumber', 'NextPage', 'FullJump', 'Sizes', 'Total']"
      @page-change="handlePageChange"
    />
  </div>
</div>
```

---

### Task 2: 重构样式 - 移除卡片样式，添加表格样式

**Files:**
- Modify: `web/src/components/workspace/BrandWorkspace.vue` (style 部分)

- [ ] **Step 1: 移除卡片网格相关样式**

删除 `<style scoped>` 中以下样式块：
- `.brand-grid`
- `.brand-card`
- `.brand-card-header`
- `.brand-card-body`
- `.brand-card-footer`
- `.brand-logo`（保留但移到表格单元格样式中）
- `.brand-name`
- `.brand-description`
- `.brand-purchaser`
- `.brand-stats`
- `.stat-item`
- `.stat-label`
- `.stat-value`
- `.update-time`
- `.card-actions`
- `.action-btn`（改用 `.btn-link`）

- [ ] **Step 2: 添加表格相关样式**

在 `<style scoped>` 中添加：

```css
.table-section {
  flex: 1;
  min-height: 0;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brand-logo-cell {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.brand-logo-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.brand-logo-cell .logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent-blue);
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.action-btns {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.btn-link:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}
```

- [ ] **Step 3: 调整加载和空状态样式**

修改 `.loading-state` 和 `.empty-state` 样式：

```css
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  min-height: 300px;
}
```

---

### Task 3: 验证功能

**Files:**
- Verify: `web/src/components/workspace/BrandWorkspace.vue`

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd web && npm run dev
```

- [ ] **Step 2: 验证表格展示**

在浏览器中访问品牌管理页面，检查：
- 表格正确展示所有列：Logo、品牌名称、描述、采购人员、状态、商品数量、更新时间、操作
- Logo 列：有图显示缩略图，无图显示首字母占位
- 状态列：启用显示绿色标签，停用显示红色标签
- 操作列：编辑、启用/停用、删除按钮正常显示

- [ ] **Step 3: 验证交互功能**

- 搜索功能：输入关键词，点击搜索，表格刷新
- 状态筛选：选择启用/停用，表格刷新
- 重置筛选：点击重置，清空筛选条件
- 分页：翻页、调整每页数量正常工作
- 编辑：点击编辑按钮，弹窗打开，数据正确填充
- 启用/停用：点击切换按钮，状态正确切换
- 删除：点击删除按钮，确认弹窗打开，删除成功

- [ ] **Step 4: 验证风格一致性**

对比商品管理页面，确认：
- 表格样式一致
- 筛选区域样式一致
- 分页器样式一致
- 操作按钮样式一致

---

### Task 4: 提交代码

- [ ] **Step 1: 提交变更**

```bash
git add web/src/components/workspace/BrandWorkspace.vue
git commit -m "refactor: 将品牌管理从卡片布局改为表格列表布局

- 使用 vxe-table 替代卡片网格展示品牌数据
- 表格列包含：Logo、品牌名称、描述、采购人员、状态、商品数量、更新时间、操作
- 保持与商品管理一致的交互风格
- 保留现有筛选、搜索、分页、弹窗功能

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```
