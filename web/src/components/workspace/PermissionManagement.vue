<script setup lang="ts">
defineOptions({ name: 'PermissionManagement' })

import { ref } from 'vue'
import { permissionApi } from '../../services/api'

interface Permission {
  id: number
  code: string
  name: string
  type: string
  path?: string
  sort_order?: number
  parent_id?: number
  children?: Permission[]
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const permissions = ref<Permission[]>([])
const expandedKeys = ref<Set<number>>(new Set())
const checkedKeys = ref<Set<number>>(new Set())

const typeMap: Record<string, { label: string; color: string }> = {
  menu: { label: '菜单', color: 'menu' },
  button: { label: '按钮', color: 'button' },
  'button,tools': { label: '按钮/Tools', color: 'button,tools' },
  tools: { label: 'Tools', color: 'tools' },
  api: { label: 'API', color: 'api' }
}

const loadPermissions = async () => {
  loading.value = true
  try {
    const res = await permissionApi.getTree()
    permissions.value = Array.isArray(res) ? res : (res.items || [])
    autoExpandFirstLevel()
  } catch (error) {
    console.error('加载权限列表失败:', error)
  } finally {
    loading.value = false
  }
}

const autoExpandFirstLevel = () => {
  expandedKeys.value = new Set(
    permissions.value
      .filter(p => p.children && p.children.length > 0)
      .map(p => p.id)
  )
}

const toggleExpand = (key: number) => {
  const newSet = new Set(expandedKeys.value)
  if (newSet.has(key)) {
    newSet.delete(key)
  } else {
    newSet.add(key)
  }
  expandedKeys.value = newSet
}

const isExpanded = (key: number) => expandedKeys.value.has(key)

const flattenTree = (items: Permission[]): { item: Permission; level: number; hasChildren: boolean }[] => {
  const result: { item: Permission; level: number; hasChildren: boolean }[] = []
  for (const item of items) {
    const hasChildren = !!(item.children && item.children.length > 0)
    result.push({ item, level: 0, hasChildren })
    if (hasChildren && expandedKeys.value.has(item.id)) {
      const children = flattenTree(item.children!)
      children.forEach(child => {
        result.push({ ...child, level: child.level + 1 })
      })
    }
  }
  return result
}

const flatPermissions = () => flattenTree(permissions.value)

const isChecked = (key: number) => checkedKeys.value.has(key)

const getAllDescendantKeys = (item: Permission): number[] => {
  const keys: number[] = []
  if (item.children) {
    for (const child of item.children) {
      keys.push(child.id)
      keys.push(...getAllDescendantKeys(child))
    }
  }
  return keys
}

const toggleCheckWithChildren = (item: Permission) => {
  const newSet = new Set(checkedKeys.value)
  const descendantKeys = getAllDescendantKeys(item)

  if (newSet.has(item.id)) {
    newSet.delete(item.id)
    descendantKeys.forEach(k => newSet.delete(k))
  } else {
    newSet.add(item.id)
    descendantKeys.forEach(k => newSet.add(k))
  }
  checkedKeys.value = newSet
}

const checkAll = () => {
  const allKeys = new Set<number>()
  const collectKeys = (items: Permission[]) => {
    for (const item of items) {
      allKeys.add(item.id)
      if (item.children) {
        collectKeys(item.children)
      }
    }
  }
  collectKeys(permissions.value)
  checkedKeys.value = allKeys
}

const uncheckAll = () => {
  checkedKeys.value = new Set()
}

const getCheckedCount = () => checkedKeys.value.size

loadPermissions()
</script>

<template>
  <div class="permission-management">
    <div class="tree-section">
      <div class="section-header">
        <h3 class="section-title">权限树</h3>
        <div class="header-actions">
          <span class="checked-count" v-if="getCheckedCount() > 0">
            已选择 {{ getCheckedCount() }} 项
          </span>
          <button class="btn-text" @click="checkAll">全选</button>
          <button class="btn-text" @click="uncheckAll">取消全选</button>
        </div>
      </div>

      <div class="tree-container">
        <div v-if="loading" class="loading-state">加载中...</div>
        <div v-else-if="permissions.length === 0" class="empty-state">暂无权限数据</div>
        <div v-else class="tree-content">
          <div
            v-for="{ item, level, hasChildren } in flatPermissions()"
            :key="item.id"
            class="tree-node"
            :class="{ 'has-children': hasChildren }"
          >
            <div class="node-row" :style="{ paddingLeft: (level * 24 + 12) + 'px' }">
              <button
                v-if="hasChildren"
                class="expand-btn"
                @click="toggleExpand(item.id)"
              >
                <span class="expand-icon" :class="{ expanded: isExpanded(item.id) }">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <path d="M4.5 2L9 6L4.5 10" stroke="currentColor" stroke-width="1.5" fill="none"/>
                  </svg>
                </span>
              </button>
              <span v-else class="expand-placeholder"></span>

              <label class="checkbox-wrapper" v-if="hasChildren || item.type === 'api'">
                <input
                  type="checkbox"
                  :checked="isChecked(item.id)"
                  @change="toggleCheckWithChildren(item)"
                />
                <span class="checkmark"></span>
              </label>
              <span v-else class="checkbox-placeholder"></span>

              <div class="node-type-icon" :class="item.type">
                <svg v-if="item.type === 'menu'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M1 3h14v2H1V3zm0 4h14v2H1V7zm0 4h14v2H1v-2z"/>
                </svg>
                <svg v-else-if="item.type === 'api'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M6.5 3H3.5V13H6.5V3ZM12.5 3H9.5V13H12.5V3ZM8 6H10V8H8V6ZM6 6H8V10H6V6Z"/>
                </svg>
                <svg v-else-if="item.type === 'button'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M6 2L10 8L6 14L5 13L8.5 8L5 3L6 2Z"/>
                </svg>
                <svg v-else-if="item.type === 'button,tools' || item.type === 'tools'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M14 8L8 2L2 8L8 14L14 8Z M6 8L8 6L10 8L8 10L6 8Z"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M6 2L10 8L6 14L5 13L8.5 8L5 3L6 2Z"/>
                </svg>
              </div>

              <div class="node-info">
                <div class="node-main">
                  <span class="node-name">{{ item.name }}</span>
                  <span class="type-badge" :class="item.type">
                    {{ typeMap[item.type]?.label || item.type }}
                  </span>
                  <span class="code-text">{{ item.code }}</span>
                </div>
                <div class="node-path" v-if="item.path">{{ item.path }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.permission-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tree-section {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checked-count {
  font-size: 13px;
  color: var(--color-interactive);
  padding-right: 8px;
  border-right: 1px solid var(--color-hairline);
  margin-right: 4px;
}

.btn-text {
  padding: 8px 12px;
  background: none;
  border: none;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.btn-text:hover {
  background-color: var(--color-info-bg);
}

.tree-container {
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  max-height: 600px;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
}

.tree-content {
  padding: 8px 0;
}

.tree-node {
  user-select: none;
}

.node-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 8px;
  transition: background-color var(--transition-fast);
}

.node-row:hover {
  background-color: var(--color-canvas);
}

.expand-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  background-color: rgba(0, 0, 0, 0.06);
  color: var(--color-ink);
}

.expand-icon {
  display: flex;
  transition: transform var(--transition-fast);
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  width: 20px;
}

.checkbox-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-wrapper input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-hairline);
  border-radius: 4px;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-wrapper:hover .checkmark {
  border-color: var(--color-interactive);
}

.checkbox-wrapper input:checked + .checkmark {
  background-color: var(--color-interactive);
  border-color: var(--color-interactive);
}

.checkbox-wrapper input:checked + .checkmark::after {
  content: '';
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  margin-bottom: 2px;
}

.checkbox-placeholder {
  width: 18px;
}

.node-type-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-type-icon.menu {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--color-interactive);
}

.node-type-icon.api {
  background-color: rgba(139, 92, 246, 0.15);
  color: #c4391a;
}

.node-type-icon.button {
  background-color: rgba(16, 185, 129, 0.15);
  color: var(--color-success);
}

.node-type-icon[class~="button,tools"],
.node-type-icon.tools {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
}

.type-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.type-badge.menu {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--color-interactive);
}

.type-badge.api {
  background-color: rgba(139, 92, 246, 0.15);
  color: #c4391a;
}

.type-badge.button {
  background-color: rgba(16, 185, 129, 0.15);
  color: var(--color-success);
}

.type-badge[class~="button,tools"],
.type-badge.tools {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.code-text {
  font-size: 12px;
  color: var(--color-muted);
  font-family: monospace;
}

.node-path {
  font-size: 12px;
  color: var(--color-muted);
  margin-top: 2px;
  font-family: monospace;
}
</style>
