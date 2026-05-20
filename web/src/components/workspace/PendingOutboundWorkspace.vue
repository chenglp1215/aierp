<script setup lang="ts">
defineOptions({ name: 'PendingOutboundWorkspace' })

import { ref, onMounted, computed } from 'vue'
import { pendingOutboundApi, warehouseApi } from '../../services/api'

// ============ 接口定义 ============

interface PendingOutbound {
  id: number
  pending_no: string
  sales_order_no: string
  row_no: number
  warehouse_id: number
  warehouse_name: string
  spec_id: number
  product_code: string
  spec_code: string
  locked_qty: number
  out_qty: number
  status: string
  created_at: string
}

interface Warehouse {
  id: string
  name: string
}

// ============ 状态变量 ============

const loading = ref(false)
const pendingOutbounds = ref<PendingOutbound[]>([])
const warehouses = ref<Warehouse[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  warehouse_id: '',
  sales_order_no: '',
  status: ''
})

// ============ 状态映射 ============

const statusMap: Record<string, { label: string; class: string }> = {
  pending: { label: '待出库', class: 'pending' },
  partial: { label: '部分出库', class: 'partial' },
  full: { label: '已出库', class: 'full' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待出库' },
  { value: 'partial', label: '部分出库' },
  { value: 'full', label: '已出库' },
  { value: 'cancelled', label: '已取消' }
]

// ============ 弹窗状态 ============

const showOutboundModal = ref(false)
const selectedPending = ref<PendingOutbound | null>(null)
const outboundQty = ref(0)
const outboundLoading = ref(false)

// ============ 计算属性 ============

const filteredWarehouses = computed(() => {
  return warehouses.value
})

const hasActiveFilters = computed(() => {
  return filters.value.warehouse_id || filters.value.sales_order_no || filters.value.status
})

// ============ 方法 ============

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page_size: 100 })
    warehouses.value = res?.items || []
  } catch (e) {
    console.error('加载仓库列表失败:', e)
  }
}

const loadPendingOutbounds = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }
    if (filters.value.warehouse_id) {
      params.warehouse_id = filters.value.warehouse_id
    }
    if (filters.value.sales_order_no) {
      params.sales_order_no = filters.value.sales_order_no
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    const res = await pendingOutboundApi.list(params)
    pendingOutbounds.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) {
    console.error('加载待出库单失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  loadPendingOutbounds()
}

const handleReset = () => {
  filters.value = {
    warehouse_id: '',
    sales_order_no: '',
    status: ''
  }
  page.value = 1
  loadPendingOutbounds()
}

// vxe-pager 分页处理函数
const handlePageChange = ({ currentPage, pageSize: newSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newSize
  loadPendingOutbounds()
}

const openOutboundModal = (item: PendingOutbound) => {
  selectedPending.value = item
  outboundQty.value = item.locked_qty - item.out_qty
  showOutboundModal.value = true
}

const handleOutbound = async () => {
  if (!selectedPending.value || outboundQty.value <= 0) return

  outboundLoading.value = true
  try {
    await pendingOutboundApi.execute(selectedPending.value.id, outboundQty.value)
    window.showToast('出库成功', 'success')
    showOutboundModal.value = false
    selectedPending.value = null
    outboundQty.value = 0
    await loadPendingOutbounds()
  } catch (error: any) {
    window.showToast(error.message || '出库失败', 'error')
  } finally {
    outboundLoading.value = false
  }
}

const getStatusLabel = (status: string) => statusMap[status]?.label || status
const getStatusClass = (status: string) => statusMap[status]?.class || ''

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

onMounted(async () => {
  await loadWarehouses()
  await loadPendingOutbounds()
})
</script>

<template>
  <div class="pending-outbound-workspace">
    <!-- 列表头部 -->
    <div class="workspace-header">
      <h2 class="workspace-title">待出库管理</h2>
    </div>

    <!-- 筛选区 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <select v-model="filters.warehouse_id" class="filter-select">
            <option value="">全部仓库</option>
            <option v-for="wh in filteredWarehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
          </select>
        </div>
        <div class="filter-item" style="flex: 1; min-width: 200px;">
          <input
            v-model="filters.sales_order_no"
            class="filter-input"
            placeholder="销售订单号"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select v-model="filters.status" class="filter-select">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button v-if="hasActiveFilters" class="filter-btn reset-btn" @click="handleReset">重置</button>
      </div>
    </div>

    <!-- 表格区 -->
    <div class="table-section">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="pendingOutbounds"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: ({ rowIndex }) => rowIndex + 1 + (page - 1) * pageSize }"
        :row-config="{ isHover: true }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column field="pending_no" title="待出库单号" width="160" class-name="col--center" />
        <vxe-column field="sales_order_no" title="销售订单号" width="160" class-name="col--center" />
        <vxe-column field="row_no" title="行号" width="60" class-name="col--center" />
        <vxe-column field="warehouse_name" title="仓库" width="120" class-name="col--left" />
        <vxe-column field="product_code" title="商品编码" width="140" class-name="col--left" />
        <vxe-column field="spec_code" title="规格编码" width="140" class-name="col--left" />
        <vxe-column field="locked_qty" title="锁定数量" width="100" class-name="col--right" />
        <vxe-column field="out_qty" title="已出库数量" width="100" class-name="col--right" />
        <vxe-column title="待出库数量" width="100" class-name="col--right">
          <template #default="{ row }">
            {{ row.locked_qty - row.out_qty }}
          </template>
        </vxe-column>
        <vxe-column field="status" title="状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getStatusClass(row.status)">
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="created_at" title="创建时间" width="160" class-name="col--center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </vxe-column>
        <vxe-column title="操作" width="80" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button
                v-if="row.status !== 'full' && row.status !== 'cancelled'"
                class="btn-link success"
                @click="openOutboundModal(row)"
              >
                出库
              </button>
              <span v-else class="text-muted">-</span>
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

    <!-- 出库确认弹窗 -->
    <div class="modal-overlay" v-if="showOutboundModal">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认出库</h3>
          <button class="modal-close" @click="showOutboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-grid">
              <div class="detail-item">
                <label>待出库单号</label>
                <span>{{ selectedPending?.pending_no }}</span>
              </div>
              <div class="detail-item">
                <label>商品编码</label>
                <span>{{ selectedPending?.product_code }}</span>
              </div>
              <div class="detail-item">
                <label>规格编码</label>
                <span>{{ selectedPending?.spec_code }}</span>
              </div>
              <div class="detail-item">
                <label>仓库</label>
                <span>{{ selectedPending?.warehouse_name }}</span>
              </div>
              <div class="detail-item">
                <label>待出库数量</label>
                <span>{{ selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0 }}</span>
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-row">
              <div class="form-group full-width">
                <label>出库数量</label>
                <input
                  type="number"
                  v-model.number="outboundQty"
                  class="form-control"
                  :max="selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0"
                  min="1"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showOutboundModal = false">取消</button>
          <button class="btn-primary" @click="handleOutbound" :disabled="outboundLoading || outboundQty <= 0">
            {{ outboundLoading ? '处理中...' : '确认出库' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pending-outbound-workspace {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ============ 头部 ============ */

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.workspace-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* ============ 筛选区 ============ */

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
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

.filter-input,
.filter-select {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.filter-input:focus,
.filter-select:focus {
  border-color: var(--accent-blue);
}

.filter-input {
  width: 100%;
}

.filter-select {
  min-width: 120px;
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

/* ============ 表格区 ============ */

.table-section {
  flex: 1;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  overflow-x: auto;
  position: relative;
}

.table-loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: var(--radius-lg);
}

.table-loading-content {
  padding: 12px 24px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

/* ============ 状态标签 ============ */

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.pending { background-color: rgba(245,158,11,0.1); color: var(--accent-yellow); }
.status-tag.partial { background-color: rgba(59,130,246,0.1); color: var(--accent-blue); }
.status-tag.full { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(128,128,128,0.1); color: var(--text-muted); }

.text-muted {
  color: var(--text-muted);
}

/* ============ 操作按钮 ============ */

.action-btns {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

.btn-link {
  padding: 4px 8px;
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color var(--transition-fast);
}

.btn-link:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.btn-link.success { color: var(--accent-green); }
.btn-link.success:hover { background-color: rgba(16,185,129,0.1); }

/* ============ 弹窗 ============ */

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
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.confirm-modal {
  width: 400px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  border-radius: var(--radius-sm);
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
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

/* ============ 详情展示 ============ */

.detail-section {
  margin-bottom: 24px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
}

/* ============ 表单 ============ */

.form-section {
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-control {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.form-control:focus {
  border-color: var(--accent-blue);
}

/* ============ 按钮 ============ */

.btn-secondary {
  padding: 8px 16px;
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.btn-primary {
  padding: 8px 16px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-primary:hover {
  background-color: var(--accent-blue-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ============ 响应式 ============ */

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-input,
  .filter-select {
    width: 100%;
  }
}
</style>
