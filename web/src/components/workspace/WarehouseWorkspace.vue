<script setup lang="ts">
defineOptions({ name: 'WarehouseWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { warehouseApi, warehouseLocationApi } from '../../services/api'

const emit = defineEmits<{
  (e: 'navigate', id: string, extraData?: Record<string, any>): void
}>()

interface Warehouse {
  id: string
  warehouse_code: string
  name: string
  address: string
  manager_id?: string
  manager_name: string
  status: string
  description?: string
  created_at?: string
  updated_at?: string
  display_status?: string
}

interface ManagerCandidate {
  id: string
  username: string
  full_name: string
}

const loading = ref(false)
const warehouses = ref<Warehouse[]>([])
const tableData = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')

const showWarehouseModal = ref(false)
const editingWarehouse = ref<Warehouse | null>(null)
const formLoading = ref(false)

const managerCandidates = ref<ManagerCandidate[]>([])
const loadingCandidates = ref(false)

const warehouseForm = ref<Partial<Warehouse>>({
  name: '',
  address: '',
  manager_id: '',
  manager_name: '',
  status: 'active',
  description: ''
})

const warehouseStatuses = [
  { value: 'active', label: '启用' },
  { value: 'inactive', label: '停用' },
  { value: 'maintenance', label: '维护中' }
]

const statusMap: Record<string, string> = {
  active: '启用',
  inactive: '停用',
  maintenance: '维护中'
}

const formatStatus = (status: string) => statusMap[status] || status

const buildTableData = () => {
  tableData.value = warehouses.value.map(w => ({
    _id: w.id,
    ...w,
    display_status: formatStatus(w.status),
    status_class: w.status
  }))
}

const loadWarehouses = async () => {
  loading.value = true
  try {
    const res = await warehouseApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined
    })
    warehouses.value = res.result?.items || res.items || []
    total.value = res.result?.total || res.total || 0
    buildTableData()
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
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

const viewInventory = (row: any) => {
  emit('navigate', 'inventory', {
    warehouseId: row.id,
    warehouseName: row.name
  })
}

const resetWarehouseForm = () => {
  warehouseForm.value = {
    name: '',
    address: '',
    manager_id: '',
    manager_name: '',
    status: 'active',
    description: ''
  }
  editingWarehouse.value = null
}

const loadManagerCandidates = async () => {
  if (managerCandidates.value.length > 0) return
  loadingCandidates.value = true
  try {
    const res = await warehouseApi.getManagerCandidates()
    managerCandidates.value = res || []
  } catch (error) {
    console.error('加载管理员候选失败:', error)
    managerCandidates.value = []
  } finally {
    loadingCandidates.value = false
  }
}

const handleManagerSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selectedId = target.value
  warehouseForm.value.manager_id = selectedId
  const selected = managerCandidates.value.find(c => c.id === selectedId)
  if (selected) {
    warehouseForm.value.manager_name = selected.full_name
  }
}

const openCreateWarehouse = () => {
  resetWarehouseForm()
  loadManagerCandidates()
  showWarehouseModal.value = true
}

const openEditWarehouse = (row: any) => {
  const warehouse = warehouses.value.find(w => w.id === row._id)
  if (!warehouse) return
  editingWarehouse.value = warehouse
  warehouseForm.value = {
    name: warehouse.name,
    address: warehouse.address,
    manager_id: warehouse.manager_id || '',
    manager_name: warehouse.manager_name || '',
    status: warehouse.status || 'active',
    description: warehouse.description || ''
  }
  loadManagerCandidates()
  showWarehouseModal.value = true
}

const handleSaveWarehouse = async () => {
  if (!warehouseForm.value.name?.trim()) {
    window.showToast('请输入仓库名称', 'warning')
    return
  }
  if (!warehouseForm.value.address?.trim()) {
    window.showToast('请输入仓库地址', 'warning')
    return
  }

  formLoading.value = true
  try {
    if (editingWarehouse.value) {
      await warehouseApi.update(editingWarehouse.value.id, warehouseForm.value)
      window.showToast('仓库更新成功', 'success')
      const index = warehouses.value.findIndex(w => w.id === editingWarehouse.value!.id)
      if (index !== -1) {
        warehouses.value[index] = {
          ...warehouses.value[index],
          ...warehouseForm.value,
          display_status: formatStatus(warehouseForm.value.status || warehouses.value[index].status)
        }
        buildTableData()
      }
    } else {
      await warehouseApi.create(warehouseForm.value)
      window.showToast('仓库创建成功', 'success')
      loadWarehouses()
    }
    showWarehouseModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}


// 库位管理相关
const showLocationModal = ref(false)
const editingLocation = ref<any | null>(null)
const locationList = ref<any[]>([])
const locationLoading = ref(false)
const locationFormLoading = ref(false)
const selectedWarehouseForLocation = ref<Warehouse | null>(null)

const locationForm = ref({
  location_code: '',
  location_name: '',
  status: 'active',
  description: ''
})

const loadLocations = async (warehouseId: string | number) => {
  locationLoading.value = true
  try {
    const res = await warehouseLocationApi.list({ warehouse_id: warehouseId, page_size: 200 })
    locationList.value = res?.items || []
  } catch (e) {
    console.error('加载库位列表失败:', e)
    locationList.value = []
  } finally {
    locationLoading.value = false
  }
}

const openLocationModal = (row: any) => {
  const warehouse = warehouses.value.find(w => w.id === row._id)
  if (!warehouse) return
  selectedWarehouseForLocation.value = warehouse
  editingLocation.value = null
  locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
  loadLocations(warehouse.id)
  showLocationModal.value = true
}

const openEditLocation = (loc: any) => {
  editingLocation.value = loc
  locationForm.value = {
    location_code: loc.location_code || '',
    location_name: loc.location_name || '',
    status: loc.status || 'active',
    description: loc.description || ''
  }
}

const handleSaveLocation = async () => {
  if (!locationForm.value.location_code.trim()) {
    window.showToast('请输入库位编码', 'warning')
    return
  }
  if (!selectedWarehouseForLocation.value) return

  locationFormLoading.value = true
  try {
    if (editingLocation.value) {
      await warehouseLocationApi.update(editingLocation.value.id, locationForm.value)
      window.showToast('库位更新成功', 'success')
    } else {
      await warehouseLocationApi.create({
        warehouse_id: selectedWarehouseForLocation.value.id,
        ...locationForm.value
      })
      window.showToast('库位创建成功', 'success')
    }
    await loadLocations(selectedWarehouseForLocation.value.id)
    editingLocation.value = null
    locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    locationFormLoading.value = false
  }
}

const handleDeleteLocation = async (loc: any) => {
  if (!confirm('确定删除该库位吗？')) return
  try {
    await warehouseLocationApi.delete(loc.id)
    window.showToast('库位删除成功', 'success')
    if (selectedWarehouseForLocation.value) {
      await loadLocations(selectedWarehouseForLocation.value.id)
    }
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

const cancelLocationEdit = () => {
  editingLocation.value = null
  locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
}

onMounted(() => {
  loadWarehouses()
  loadManagerCandidates()
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
    </div>

    <div class="table-section" style="position: relative;">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="tableData"
        :column-config="{ resizable: true }"
      >
        <vxe-column type="seq" title="序号" width="60" class-name="col--center" />
        <vxe-column field="warehouse_code" title="仓库编码" min-width="150" class-name="col--center" />
        <vxe-column field="name" title="仓库名称" min-width="180" />
        <vxe-column field="address" title="仓库地址" min-width="200" show-overflow />
        <vxe-column field="manager_name" title="管理员" min-width="100" class-name="col--center" />
        <vxe-column field="display_status" title="状态" min-width="80" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status_class">{{ row.display_status }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" min-width="180" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="viewInventory(row)">查看库存</button>
              <button class="btn-link" @click="openLocationModal(row)">库位管理</button>
              <button class="btn-link" @click="openEditWarehouse(row)">编辑</button>
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
              <label>仓库管理员</label>
              <select
                :value="warehouseForm.manager_id"
                @change="handleManagerSelect"
                :disabled="loadingCandidates"
              >
                <option value="">请选择管理员</option>
                <option
                  v-for="candidate in managerCandidates"
                  :key="candidate.id"
                  :value="candidate.id"
                >
                  {{ candidate.full_name }} ({{ candidate.username }})
                </option>
              </select>
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


    <!-- 库位管理弹窗 -->
    <div class="modal-overlay" v-if="showLocationModal">
      <div class="modal" style="max-width: 700px;">
        <div class="modal-header">
          <h3>{{ selectedWarehouseForLocation?.name }} - 库位管理</h3>
          <button class="modal-close" @click="showLocationModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="location-form" v-if="!editingLocation">
            <div class="form-row">
              <div class="form-group">
                <label>库位编码 *</label>
                <input type="text" v-model="locationForm.location_code" placeholder="如 A-01" />
              </div>
              <div class="form-group">
                <label>库位名称</label>
                <input type="text" v-model="locationForm.location_name" placeholder="可选" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>状态</label>
                <select v-model="locationForm.status">
                  <option value="active">启用</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
              <div class="form-group">
                <label>描述</label>
                <input type="text" v-model="locationForm.description" placeholder="可选" />
              </div>
            </div>
            <button class="btn-primary" @click="handleSaveLocation" :disabled="locationFormLoading" style="align-self: flex-end;">
              {{ locationFormLoading ? '保存中...' : '添加库位' }}
            </button>
          </div>
          <div class="location-form" v-else>
            <div class="form-row">
              <div class="form-group">
                <label>库位编码 *</label>
                <input type="text" v-model="locationForm.location_code" />
              </div>
              <div class="form-group">
                <label>库位名称</label>
                <input type="text" v-model="locationForm.location_name" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>状态</label>
                <select v-model="locationForm.status">
                  <option value="active">启用</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
              <div class="form-group">
                <label>描述</label>
                <input type="text" v-model="locationForm.description" />
              </div>
            </div>
            <div style="display: flex; gap: 8px; align-self: flex-end;">
              <button class="btn-secondary" @click="cancelLocationEdit">取消</button>
              <button class="btn-primary" @click="handleSaveLocation" :disabled="locationFormLoading">
                {{ locationFormLoading ? '保存中...' : '保存' }}
              </button>
            </div>
          </div>
          <div class="location-list">
            <div v-if="locationLoading" style="text-align: center; padding: 20px; color: var(--text-muted);">加载中...</div>
            <table v-else class="location-table">
              <thead>
                <tr>
                  <th>库位编码</th>
                  <th>名称</th>
                  <th>状态</th>
                  <th>描述</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="loc in locationList" :key="loc.id">
                  <td>{{ loc.location_code }}</td>
                  <td>{{ loc.location_name || '-' }}</td>
                  <td>
                    <span class="status-tag" :class="loc.status">{{ loc.status === 'active' ? '启用' : '停用' }}</span>
                  </td>
                  <td>{{ loc.description || '-' }}</td>
                  <td>
                    <span class="action-btns">
                      <button class="btn-link" @click="openEditLocation(loc)">编辑</button>
                      <button class="btn-link danger" @click="handleDeleteLocation(loc)">删除</button>
                    </span>
                  </td>
                </tr>
                <tr v-if="locationList.length === 0">
                  <td colspan="5" style="text-align: center; color: var(--text-muted);">暂无库位</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showLocationModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.warehouse-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  margin: 0;
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

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
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

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  box-shadow: var(--shadow-card);
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

.table-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

[data-theme="dark"] .table-loading-overlay {
  background-color: rgba(0, 0, 0, 0.8);
}

.table-loading-content {
  padding: 20px 40px;
  background-color: var(--bg-card);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: var(--text-primary);
  font-size: 14px;
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

.location-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.location-list {
  max-height: 300px;
  overflow-y: auto;
}

.location-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.location-table th {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-weight: 500;
}

.location-table td {
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}
</style>
