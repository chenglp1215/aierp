<script setup lang="ts">
defineOptions({ name: 'RoleManagement' })

import { ref, onMounted, computed } from 'vue'
import { roleApi, permissionApi } from '../../services/api'

interface Role {
  id: string
  name: string
  code: string
  description?: string
  is_fixed?: boolean
  permission_ids?: string[]
  permissions?: { id: string }[]
  created_at?: string
}

interface Permission {
  id: string
  code: string
  name: string
  type: string
  path?: string
  sort_order?: number
  parent_id?: string
  children?: Permission[]
}

const loading = ref(false)
const roles = ref<Role[]>([])
const permissionTree = ref<Permission[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const showModal = ref(false)
const showDeleteConfirm = ref(false)
const editingRole = ref<Role | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)

const expandedKeys = ref<Set<string>>(new Set())
const checkedKeys = ref<Set<string>>(new Set())

const roleForm = ref({
  name: '',
  code: '',
  description: '',
  permission_ids: [] as string[]
})

const columns = [
  { key: 'name', label: '角色名' },
  { key: 'code', label: '角色代码' },
  { key: 'description', label: '描述' },
  { key: 'is_fixed', label: '类型' },
  { key: 'created_at', label: '创建时间' }
]

const typeMap: Record<string, { label: string; color: string }> = {
  menu: { label: '菜单', color: 'menu' },
  button: { label: '按钮', color: 'button' },
  api: { label: 'API', color: 'api' }
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const loadRoles = async () => {
  loading.value = true
  try {
    const res = await roleApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined
    })
    roles.value = (res.items || []).map((role: any) => ({
      ...role,
      permission_ids: (role.permissions || []).map((p: any) => p.id || p)
    }))
    total.value = res.total || 0
  } catch (error) {
    console.error('加载角色列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadPermissionTree = async () => {
  try {
    const res = await permissionApi.getTree()
    permissionTree.value = Array.isArray(res) ? res : (res.items || [])
    autoExpandFirstLevel()
  } catch (error) {
    console.error('加载权限树失败:', error)
  }
}

const autoExpandFirstLevel = () => {
  expandedKeys.value = new Set(
    permissionTree.value
      .filter(p => p.children && p.children.length > 0)
      .map(p => p.id)
  )
}

const toggleExpand = (key: string) => {
  const newSet = new Set(expandedKeys.value)
  if (newSet.has(key)) {
    newSet.delete(key)
  } else {
    newSet.add(key)
  }
  expandedKeys.value = newSet
}

const isExpanded = (key: string) => expandedKeys.value.has(key)

const flattenTree = (
  items: Permission[],
  level: number = 0
): { item: Permission; level: number; hasChildren: boolean }[] => {
  const result: { item: Permission; level: number; hasChildren: boolean }[] = []
  for (const item of items) {
    const hasChildren = !!(item.children && item.children.length > 0)
    result.push({ item, level, hasChildren })
    if (hasChildren && expandedKeys.value.has(item.id)) {
      result.push(...flattenTree(item.children!, level + 1))
    }
  }
  return result
}

const flatPermissions = computed(() => flattenTree(permissionTree.value))

const getAllDescendantKeys = (item: Permission): string[] => {
  const keys: string[] = []
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
  roleForm.value.permission_ids = Array.from(newSet)
}

const isChecked = (key: string) => checkedKeys.value.has(key)

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadRoles()
}

const handleSearch = () => {
  page.value = 1
  loadRoles()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetForm = () => {
  roleForm.value = {
    name: '',
    code: '',
    description: '',
    permission_ids: []
  }
  checkedKeys.value = new Set()
  editingRole.value = null
}

const openCreate = () => {
  resetForm()
  showModal.value = true
}

const openEdit = async (role: Role) => {
  editingRole.value = role
  roleForm.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
    permission_ids: role.permission_ids || []
  }
  checkedKeys.value = new Set(role.permission_ids || [])
  showModal.value = true
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSave = async () => {
  if (!roleForm.value.name?.trim()) {
    window.showToast('请输入角色名', 'warning')
    return
  }
  if (!roleForm.value.code?.trim()) {
    window.showToast('请输入角色代码', 'warning')
    return
  }

  formLoading.value = true
  try {
    const data = {
      name: roleForm.value.name,
      code: roleForm.value.code,
      description: roleForm.value.description || undefined,
      permission_ids: roleForm.value.permission_ids
    }

    if (editingRole.value) {
      await roleApi.update(editingRole.value.id, data)
      window.showToast('角色更新成功', 'success')
    } else {
      await roleApi.create(data)
      window.showToast('角色创建成功', 'success')
    }
    showModal.value = false
    loadRoles()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await roleApi.delete(deleteTargetId.value)
    window.showToast('角色删除成功', 'success')
    roles.value = roles.value.filter(r => r.id !== deleteTargetId.value)
    total.value--
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const checkAll = () => {
  const allKeys = new Set<string>()
  const collectKeys = (items: Permission[]) => {
    for (const item of items) {
      allKeys.add(item.id)
      if (item.children) {
        collectKeys(item.children)
      }
    }
  }
  collectKeys(permissionTree.value)
  checkedKeys.value = allKeys
  roleForm.value.permission_ids = Array.from(allKeys)
}

const uncheckAll = () => {
  checkedKeys.value = new Set()
  roleForm.value.permission_ids = []
}

onMounted(() => {
  loadRoles()
  loadPermissionTree()
})
</script>

<template>
  <div class="role-management">
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索角色名、代码..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="clearKeyword" v-if="keyword">重置</button>
        <button class="primary-btn" @click="openCreate" style="margin-left: auto;">新建角色</button>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key">{{ col.label }}</th>
            <th style="width: 180px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="roles.length === 0">
            <td :colspan="columns.length + 1" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="role in roles" :key="role.id">
            <td>{{ role.name }}</td>
            <td>{{ role.code }}</td>
            <td>{{ role.description || '-' }}</td>
            <td>
              <span v-if="role.is_fixed" class="fixed-tag">固化</span>
              <span v-else class="normal-tag">自定义</span>
            </td>
            <td>{{ formatDate(role.created_at) }}</td>
            <td>
              <div class="action-buttons" v-if="!role.is_fixed">
                <button class="btn-link" @click="openEdit(role)">编辑</button>
                <button class="btn-link danger" @click="confirmDelete(role.id)">删除</button>
              </div>
              <span v-else class="no-action">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="roles.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
      <div class="modal permission-modal">
        <div class="modal-header">
          <h3>{{ editingRole ? '编辑角色' : '新建角色' }}</h3>
          <button class="modal-close" @click="showModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>角色名 *</label>
              <input type="text" v-model="roleForm.name" placeholder="请输入角色名" />
            </div>
            <div class="form-group">
              <label>角色代码 *</label>
              <input type="text" v-model="roleForm.code" placeholder="请输入角色代码" />
            </div>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="roleForm.description" placeholder="请输入描述" />
          </div>

          <div class="permission-section">
            <div class="section-header">
              <label class="section-label">权限分配</label>
              <div class="perm-actions">
                <button class="btn-text" @click="checkAll">全选</button>
                <button class="btn-text" @click="uncheckAll">取消全选</button>
              </div>
            </div>
            <div class="permission-tree" v-if="permissionTree.length">
              <div
                v-for="{ item, level, hasChildren } in flatPermissions"
                :key="item.id"
                class="perm-row"
                :style="{ paddingLeft: (level * 20) + 'px' }"
              >
                <button
                  v-if="hasChildren"
                  class="expand-btn"
                  @click="toggleExpand(item.id)"
                >
                  <span class="expand-icon" :class="{ expanded: isExpanded(item.id) }">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                      <path d="M3 2L7 5L3 8" stroke="currentColor" stroke-width="1.5" fill="none"/>
                    </svg>
                  </span>
                </button>
                <span v-else class="expand-placeholder"></span>

                <label class="checkbox-wrapper">
                  <input
                    type="checkbox"
                    :checked="isChecked(item.id)"
                    @change="toggleCheckWithChildren(item)"
                  />
                  <span class="checkmark"></span>
                </label>

                <div class="perm-type-icon" :class="item.type">
                  <svg v-if="item.type === 'menu'" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M1 3h14v2H1V3zm0 4h14v2H1V7zm0 4h14v2H1v-2z"/>
                  </svg>
                  <svg v-else-if="item.type === 'api'" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M6.5 3H3.5V13H6.5V3ZM12.5 3H9.5V13H12.5V3ZM8 6H10V8H8V6ZM6 6H8V10H6V6Z"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M6 2L10 8L6 14L5 13L8.5 8L5 3L6 2Z"/>
                  </svg>
                </div>

                <div class="perm-info">
                  <span class="perm-name">{{ item.name }}</span>
                  <span class="type-badge" :class="item.type">
                    {{ typeMap[item.type]?.label || item.type }}
                  </span>
                </div>
                <span class="perm-code">{{ item.code }}</span>
              </div>
            </div>
            <div v-else class="empty-permissions">暂无可分配的权限</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showModal = false">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该角色吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.role-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
}

.filter-item.search-filter {
  flex: 1;
  min-width: 200px;
}

.filter-input {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.filter-input::placeholder {
  color: var(--text-muted);
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.filter-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background-color: var(--accent-blue-hover);
}

.filter-btn.reset-btn {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.filter-btn.reset-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.data-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.inactive {
  background-color: rgba(128, 128, 128, 0.1);
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: 4px;
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

.no-action {
  color: var(--text-muted);
}

.fixed-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background-color: rgba(245, 158, 11, 0.15);
  color: var(--accent-yellow);
}

.normal-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background-color: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.pagination-info {
  font-size: 13px;
  color: var(--text-muted);
}

.pagination-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.pagination-btn:hover:not(:disabled) {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-current {
  font-size: 13px;
  color: var(--text-secondary);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.permission-modal {
  max-width: 750px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.permission-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.perm-actions {
  display: flex;
  gap: 4px;
}

.btn-text {
  padding: 4px 8px;
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.btn-text:hover {
  background-color: rgba(59, 130, 246, 0.1);
}

.permission-tree {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  padding: 8px;
  max-height: 350px;
  overflow-y: auto;
}

.perm-row {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  gap: 8px;
  border-radius: 4px;
  transition: background-color var(--transition-fast);
}

.perm-row:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.expand-btn {
  width: 18px;
  height: 18px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.expand-icon {
  display: flex;
  transition: transform var(--transition-fast);
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  width: 18px;
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
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-radius: 3px;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-wrapper:hover .checkmark {
  border-color: var(--accent-blue);
}

.checkbox-wrapper input:checked + .checkmark {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.checkbox-wrapper input:checked + .checkmark::after {
  content: '';
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  margin-bottom: 2px;
}

.perm-type-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.perm-type-icon.menu {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.perm-type-icon.api {
  background-color: rgba(139, 92, 246, 0.15);
  color: var(--accent-purple);
}

.perm-type-icon.button {
  background-color: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.perm-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.perm-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
}

.type-badge {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
}

.type-badge.menu {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.type-badge.api {
  background-color: rgba(139, 92, 246, 0.15);
  color: var(--accent-purple);
}

.type-badge.button {
  background-color: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.perm-code {
  font-size: 11px;
  color: var(--text-muted);
  font-family: monospace;
  flex-shrink: 0;
}

.empty-permissions {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-red);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-modal {
  max-width: 400px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}
</style>
