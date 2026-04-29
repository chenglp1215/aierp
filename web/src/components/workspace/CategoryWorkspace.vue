<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { categoryApi, type CategoryTreeNode, type CategoryFormData } from '../../services/api'

const loading = ref(false)
const categoryTree = ref<CategoryTreeNode[]>([])
const expandedIds = ref<Set<string>>(new Set())
const selectedId = ref<string | null>(null)
const showFormModal = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref<CategoryTreeNode | null>(null)
const editingCategory = ref<CategoryTreeNode | null>(null)
const formLoading = ref(false)

const categoryForm = ref<CategoryFormData>({
  name: '',
  parent_id: null,
  tax_code: '',
  sort_order: 0,
  is_shop_display: true
})

const flatTreeData = computed(() => {
  const result: (CategoryTreeNode & { depth: number; expanded: boolean; hasChildren: boolean })[] = []
  const traverse = (nodes: CategoryTreeNode[], depth = 0) => {
    for (const node of nodes) {
      const hasChildren = node.children && node.children.length > 0
      result.push({
        ...node,
        depth,
        expanded: expandedIds.value.has(node.id),
        hasChildren
      })
      if (hasChildren && expandedIds.value.has(node.id)) {
        traverse(node.children!, depth + 1)
      }
    }
  }
  traverse(categoryTree.value)
  return result
})

const loadCategoryTree = async () => {
  loading.value = true
  try {
    const res = await categoryApi.getTree()
    categoryTree.value = res.result || []
    expandAll()
  } catch (error) {
    console.error('加载分类树失败:', error)
  } finally {
    loading.value = false
  }
}

const expandAll = () => {
  const allIds = new Set<string>()
  const collectIds = (nodes: CategoryTreeNode[]) => {
    for (const node of nodes) {
      if (node.children && node.children.length > 0) {
        allIds.add(node.id)
        collectIds(node.children)
      }
    }
  }
  collectIds(categoryTree.value)
  expandedIds.value = allIds
}

const toggleExpand = (id: string) => {
  const newSet = new Set(expandedIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedIds.value = newSet
}

const selectNode = (id: string) => {
  selectedId.value = id
}

const getSelectedNode = computed(() => {
  if (!selectedId.value) return null
  const findNode = (nodes: CategoryTreeNode[]): CategoryTreeNode | null => {
    for (const node of nodes) {
      if (node.id === selectedId.value) return node
      if (node.children) {
        const found = findNode(node.children)
        if (found) return found
      }
    }
    return null
  }
  return findNode(categoryTree.value)
})

const resetForm = () => {
  categoryForm.value = {
    name: '',
    parent_id: null,
    tax_code: '',
    sort_order: 0,
    is_shop_display: true
  }
  editingCategory.value = null
}

const openCreateRoot = () => {
  resetForm()
  showFormModal.value = true
}

const openCreateChild = () => {
  const node = getSelectedNode.value
  if (!node || node.level >= 3) return
  resetForm()
  categoryForm.value.parent_id = node.id
  showFormModal.value = true
}

const openEdit = () => {
  const node = getSelectedNode.value
  if (!node) return
  editingCategory.value = node
  categoryForm.value = {
    name: node.name,
    parent_id: node.parent_id,
    tax_code: node.tax_code || '',
    sort_order: node.sort_order,
    is_shop_display: node.is_shop_display
  }
  showFormModal.value = true
}

const handleSave = async () => {
  if (!categoryForm.value.name?.trim()) {
    window.showToast('请输入分类名称', 'warning')
    return
  }
  formLoading.value = true
  try {
    if (editingCategory.value) {
      await categoryApi.update(editingCategory.value.id, categoryForm.value)
      window.showToast('分类更新成功', 'success')
    } else {
      await categoryApi.create(categoryForm.value)
      window.showToast('分类创建成功', 'success')
    }
    showFormModal.value = false
    loadCategoryTree()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = () => {
  const node = getSelectedNode.value
  if (!node) return
  if (node.children && node.children.length > 0) {
    window.showToast('该分类下存在子分类，无法删除', 'error')
    return
  }
  deleteTarget.value = node
  showDeleteModal.value = true
}

const handleDelete = async () => {
  if (!deleteTarget.value) return
  formLoading.value = true
  try {
    await categoryApi.delete(deleteTarget.value.id)
    window.showToast('分类删除成功', 'success')
    showDeleteModal.value = false
    deleteTarget.value = null
    selectedId.value = null
    loadCategoryTree()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const getLevelName = (level: number) => {
  const names: Record<number, string> = { 1: '一级', 2: '二级', 3: '三级' }
  return names[level] || `${level}级`
}

const getLevelColor = (level: number) => {
  const colors: Record<number, string> = {
    1: 'var(--accent-blue)',
    2: 'var(--accent-green)',
    3: 'var(--accent-orange)'
  }
  return colors[level] || 'var(--text-muted)'
}

onMounted(() => {
  loadCategoryTree()
})
</script>

<template>
  <div class="category-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">分类管理</h2>
      <div class="header-actions">
        <button class="text-btn" @click="expandAll">展开全部</button>
        <button class="primary-btn" @click="openCreateRoot">新建分类</button>
      </div>
    </div>

    <div class="category-container">
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="categoryTree.length === 0" class="empty-state">
        暂无分类，点击"新建分类"创建
      </div>
      <div v-else class="tree-view">
        <div class="tree-header">
          <span class="col-name">分类名称</span>
          <span class="col-level">层级</span>
          <span class="col-tax">税务编码</span>
          <span class="col-sort">排序</span>
          <span class="col-display">展示</span>
          <span class="col-actions">操作</span>
        </div>
        <div class="tree-body">
          <div
            v-for="node in flatTreeData"
            :key="node.id"
            class="tree-row"
            :class="{ selected: selectedId === node.id, 'has-child': node.hasChildren }"
            :style="{ paddingLeft: node.depth * 24 + 12 + 'px' }"
            @click="selectNode(node.id)"
          >
            <span class="col-name">
              <span
                class="expand-btn"
                :class="{ expanded: node.expanded, invisible: !node.hasChildren }"
                @click.stop="toggleExpand(node.id)"
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                </svg>
              </span>
              <span class="node-icon" :style="{ color: getLevelColor(node.level) }">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l-5.5 9h11L12 2zm0 3.84L13.93 9h-3.87L12 5.84zM17.5 13c-2.49 0-4.5 2.01-4.5 4.5s2.01 4.5 4.5 4.5 4.5-2.01 4.5-4.5-2.01-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5zM3 21.5h8v-8H3v8zm2-6h4v4H5v-4z"/>
                </svg>
              </span>
              <span class="node-name">{{ node.name }}</span>
            </span>
            <span class="col-level">
              <span class="level-tag" :style="{ backgroundColor: getLevelColor(node.level) + '20', color: getLevelColor(node.level) }">
                {{ getLevelName(node.level) }}
              </span>
            </span>
            <span class="col-tax">{{ node.tax_code || '-' }}</span>
            <span class="col-sort">{{ node.sort_order }}</span>
            <span class="col-display">
              <span :class="['status-dot', node.is_shop_display ? 'active' : 'inactive']"></span>
            </span>
            <span class="col-actions">
              <button class="action-btn" @click.stop="selectedId = node.id; openEdit()">编辑</button>
              <button
                class="action-btn"
                @click.stop="selectedId = node.id; openCreateChild()"
                :disabled="node.level >= 3"
              >添加下级</button>
              <button
                class="action-btn danger"
                @click.stop="selectedId = node.id; confirmDelete()"
                :disabled="node.hasChildren"
              >删除</button>
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showFormModal" @click.self="showFormModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingCategory ? '编辑分类' : '新建分类' }}</h3>
          <button class="modal-close" @click="showFormModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>分类名称 *</label>
            <input type="text" v-model="categoryForm.name" placeholder="请输入分类名称" />
          </div>
          <div class="form-group">
            <label>父分类</label>
            <select v-model="categoryForm.parent_id">
              <option :value="null">无（顶级分类）</option>
              <option v-for="node in flatTreeData.filter(n => n.level < 3)" :key="node.id" :value="node.id">
                {{ '　├ '.repeat(node.depth) }}{{ node.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>税务编码</label>
            <input type="text" v-model="categoryForm.tax_code" placeholder="请输入税务编码" />
          </div>
          <div class="form-group">
            <label>排序</label>
            <input type="number" v-model="categoryForm.sort_order" placeholder="数字越小越靠前" min="0" />
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="categoryForm.is_shop_display" />
              商城展示
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showFormModal = false">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDeleteModal" @click.self="showDeleteModal = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除分类 <strong>"{{ deleteTarget?.name }}"</strong> 吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="formLoading">
            {{ formLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.text-btn {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.text-btn:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.primary-btn {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.category-container {
  flex: 1;
  min-height: 0;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  min-height: 300px;
}

.tree-view {
  flex: 1;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.tree-header {
  display: grid;
  grid-template-columns: 1fr 80px 120px 60px 60px 160px;
  gap: 8px;
  padding: 12px 16px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}

.tree-body {
  flex: 1;
  overflow-y: auto;
}

.tree-row {
  display: grid;
  grid-template-columns: 1fr 80px 120px 60px 60px 160px;
  gap: 8px;
  padding: 10px 16px;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  font-size: 13px;
}

.tree-row:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

.tree-row.selected {
  background-color: rgba(0, 120, 212, 0.12);
}

.col-name {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.expand-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}

.expand-btn.invisible {
  visibility: hidden;
}

.expand-btn.expanded {
  transform: rotate(90deg);
}

.expand-btn svg {
  width: 16px;
  height: 16px;
}

.node-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.node-icon svg {
  width: 16px;
  height: 16px;
}

.node-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.level-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.col-tax,
.col-sort {
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-display {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active {
  background-color: var(--accent-green);
}

.status-dot.inactive {
  background-color: var(--text-muted);
}

.col-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}

.action-btn {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.action-btn:hover:not(:disabled) {
  background-color: rgba(0, 120, 212, 0.1);
}

.action-btn.danger {
  color: var(--accent-red);
}

.action-btn.danger:hover:not(:disabled) {
  background-color: rgba(239, 68, 68, 0.1);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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
  width: 95%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.confirm-modal {
  max-width: 400px;
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
  display: flex;
  align-items: center;
  justify-content: center;
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

.modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input[type="text"],
.form-group input[type="number"],
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

.checkbox-group {
  flex-direction: row;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
  cursor: pointer;
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
  cursor: pointer;
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
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
