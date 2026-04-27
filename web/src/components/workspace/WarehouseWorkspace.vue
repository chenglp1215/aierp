<script setup lang="ts">
defineOptions({ name: 'WarehouseWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { warehouseApi } from '../../services/api'

interface Warehouse {
  id: string
  warehouse_code: string
  name: string
  address: string
  manager_name: string
  manager_phone: string
  status: string
  description?: string
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const warehouses = ref<Warehouse[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')

const showWarehouseModal = ref(false)
const showDeleteConfirm = ref(false)
const editingWarehouse = ref<Warehouse | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)

const warehouseForm = ref<Partial<Warehouse>>({
  name: '',
  address: '',
  manager_name: '',
  manager_phone: '',
  status: 'active',
  description: ''
})

const warehouseStatuses = [
  { value: 'active', label: '启用' },
  { value: 'inactive', label: '停用' },
  { value: 'maintenance', label: '维护中' }
]

const columns = [
  { key: 'warehouse_code', label: '仓库编码', width: '180px' },
  { key: 'name', label: '仓库名称' },
  { key: 'address', label: '仓库地址' },
  { key: 'manager_name', label: '管理员', width: '100px' },
  { key: 'manager_phone', label: '联系电话', width: '130px' },
  { key: 'status', label: '状态', width: '80px' }
]

const statusMap: Record<string, string> = {
  active: '启用',
  inactive: '停用',
  maintenance: '维护中'
}

const formatStatus = (status: string) => statusMap[status] || status

const loadWarehouses = async () => {
  loading.value = true
  try {
    const res = await warehouseApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined
    })
    warehouses.value = res.items.map((item: Warehouse) => ({
      ...item,
      status: formatStatus(item.status)
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadWarehouses()
}

const handleSearch = () => {
  page.value = 1
  loadWarehouses()
}

const hasActiveFilters = computed(() => {
  return !!(keyword.value || filterStatus.value)
})

const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  page.value = 1
  loadWarehouses()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetWarehouseForm = () => {
  warehouseForm.value = {
    name: '',
    address: '',
    manager_name: '',
    manager_phone: '',
    status: 'active',
    description: ''
  }
  editingWarehouse.value = null
}

const openCreateWarehouse = () => {
  resetWarehouseForm()
  showWarehouseModal.value = true
}

const openEditWarehouse = (warehouse: Warehouse) => {
  editingWarehouse.value = warehouse
  warehouseForm.value = { ...warehouse }
  showWarehouseModal.value = true
}

const confirmDelete = (warehouseId: string) => {
  deleteTargetId.value = warehouseId
  showDeleteConfirm.value = true
}

const handleSaveWarehouse = async () => {
  if (!warehouseForm.value.name?.trim()) {
    alert('请输入仓库名称')
    return
  }
  if (!warehouseForm.value.address?.trim()) {
    alert('请输入仓库地址')
    return
  }
  if (!warehouseForm.value.manager_name?.trim()) {
    alert('请输入仓库管理员')
    return
  }
  if (!warehouseForm.value.manager_phone?.trim()) {
    alert('请输入管理员电话')
    return
  }

  formLoading.value = true
  try {
    if (editingWarehouse.value) {
      await warehouseApi.update(editingWarehouse.value.id, warehouseForm.value)
      alert('仓库更新成功')
    } else {
      await warehouseApi.create(warehouseForm.value)
      alert('仓库创建成功')
    }
    showWarehouseModal.value = false
    loadWarehouses()
  } catch (error: any) {
    alert(error.message || '操作失败')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await warehouseApi.delete(deleteTargetId.value)
    alert('仓库删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadWarehouses()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  loadWarehouses()
})
</script>

<template>
  <div class="warehouse-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">仓库管理</h2>
      <button class="primary-btn" @click="openCreateWarehouse">新建仓库</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索仓库名称、编码、管理员..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in warehouseStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
      <div class="active-filters" v-if="hasActiveFilters">
        <span class="filter-tag" v-if="keyword">
          关键词: {{ keyword }}
          <button class="tag-close" @click="clearKeyword">×</button>
        </span>
        <span class="filter-tag" v-if="filterStatus">
          状态: {{ formatStatus(filterStatus) }}
          <button class="tag-close" @click="filterStatus = ''; handleSearch()">×</button>
        </span>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" :style="{ width: col.width }">
              {{ col.label }}
            </th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="warehouses.length === 0">
            <td :colspan="columns.length + 1" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="warehouse in warehouses" :key="warehouse.id">
            <td>{{ warehouse.warehouse_code }}</td>
            <td>{{ warehouse.name }}</td>
            <td>{{ warehouse.address }}</td>
            <td>{{ warehouse.manager_name }}</td>
            <td>{{ warehouse.manager_phone }}</td>
            <td>
              <span class="status-tag" :class="warehouse.status.toLowerCase()">
                {{ warehouse.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openEditWarehouse(warehouse)">编辑</button>
                <button class="btn-link danger" @click="confirmDelete(warehouse.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="warehouses.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showWarehouseModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingWarehouse ? '编辑仓库' : '新建仓库' }}</h3>
          <button class="modal-close" @click="showWarehouseModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>仓库名称 *</label>
              <input type="text" v-model="warehouseForm.name" placeholder="请输入仓库名称" />
            </div>
            <div class="form-group">
              <label>仓库地址 *</label>
              <input type="text" v-model="warehouseForm.address" placeholder="请输入仓库地址" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>仓库管理员 *</label>
              <input type="text" v-model="warehouseForm.manager_name" placeholder="请输入管理员姓名" />
            </div>
            <div class="form-group">
              <label>管理员电话 *</label>
              <input type="text" v-model="warehouseForm.manager_phone" placeholder="请输入联系电话" />
            </div>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="warehouseForm.status">
              <option v-for="s in warehouseStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="warehouseForm.description" placeholder="请输入仓库描述" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showWarehouseModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveWarehouse" :disabled="formLoading">
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
          <p>确定要删除该仓库吗？此操作不可恢复。</p>
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
.warehouse-workspace {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.filter-select {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  min-width: 100px;
}

.filter-select:focus {
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

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 12px;
  background-color: rgba(0, 120, 212, 0.1);
  border-radius: 16px;
  font-size: 12px;
  color: var(--accent-blue);
}

.tag-close {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: rgba(0, 120, 212, 0.2);
  border: none;
  color: var(--accent-blue);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.tag-close:hover {
  background-color: var(--accent-blue);
  color: white;
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

.status-tag.maintenance {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
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
  white-space: nowrap;
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
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group textarea {
  resize: vertical;
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>
