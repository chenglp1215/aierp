<script setup lang="ts">
defineOptions({ name: 'PendingOutboundWorkspace' })

import { ref, onMounted, computed } from 'vue'
import { pendingOutboundApi, warehouseApi } from '../../services/api'

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

const showOutboundModal = ref(false)
const selectedPending = ref<PendingOutbound | null>(null)
const outboundQty = ref(0)
const outboundLoading = ref(false)

const filteredWarehouses = computed(() => {
  return warehouses.value
})

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

const handlePageChange = (newPage: number) => {
  page.value = newPage
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

onMounted(async () => {
  await loadWarehouses()
  await loadPendingOutbounds()
})
</script>

<template>
  <div class="pending-outbound-workspace">
    <div class="page-header">
      <h2>待出库管理</h2>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>仓库</label>
          <select v-model="filters.warehouse_id" class="form-select">
            <option value="">全部仓库</option>
            <option v-for="wh in filteredWarehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
          </select>
        </div>
        <div class="filter-item">
          <label>销售订单号</label>
          <input type="text" v-model="filters.sales_order_no" class="form-input" placeholder="输入订单号搜索" />
        </div>
        <div class="filter-item">
          <label>状态</label>
          <select v-model="filters.status" class="form-select">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="filter-actions">
          <button class="btn-primary" @click="handleSearch">查询</button>
          <button class="btn-secondary" @click="handleReset">重置</button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="pendingOutbounds.length === 0" class="empty-state">
        暂无待出库单
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>待出库单号</th>
              <th>销售订单号</th>
              <th>行号</th>
              <th>仓库</th>
              <th>商品编码</th>
              <th>规格编码</th>
              <th class="col-num">锁定数量</th>
              <th class="col-num">已出库数量</th>
              <th class="col-num">待出库数量</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in pendingOutbounds" :key="item.id">
              <td>{{ item.pending_no }}</td>
              <td>{{ item.sales_order_no }}</td>
              <td>{{ item.row_no }}</td>
              <td>{{ item.warehouse_name }}</td>
              <td>{{ item.product_code }}</td>
              <td>{{ item.spec_code }}</td>
              <td class="col-num">{{ item.locked_qty }}</td>
              <td class="col-num">{{ item.out_qty }}</td>
              <td class="col-num">{{ item.locked_qty - item.out_qty }}</td>
              <td>
                <span class="status-tag" :class="getStatusClass(item.status)">
                  {{ getStatusLabel(item.status) }}
                </span>
              </td>
              <td>{{ item.created_at }}</td>
              <td>
                <button
                  v-if="item.status !== 'full' && item.status !== 'cancelled'"
                  class="btn-action"
                  @click="openOutboundModal(item)"
                >
                  出库
                </button>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="total > pageSize" class="pagination">
        <button class="page-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
        <span class="page-info">第 {{ page }} 页 / 共 {{ Math.ceil(total / pageSize) }} 页</span>
        <button class="page-btn" :disabled="page >= Math.ceil(total / pageSize)" @click="handlePageChange(page + 1)">下一页</button>
      </div>
    </div>

    <!-- 出库确认弹窗 -->
    <div class="modal-overlay" v-if="showOutboundModal">
      <div class="modal">
        <div class="modal-header">
          <h3>确认出库</h3>
          <button class="modal-close" @click="showOutboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <span class="info-label">待出库单号：</span>
            <span>{{ selectedPending?.pending_no }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">商品编码：</span>
            <span>{{ selectedPending?.product_code }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">规格编码：</span>
            <span>{{ selectedPending?.spec_code }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">仓库：</span>
            <span>{{ selectedPending?.warehouse_name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">待出库数量：</span>
            <span>{{ selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0 }}</span>
          </div>
          <div class="form-group">
            <label>出库数量</label>
            <input type="number" v-model.number="outboundQty" class="form-input" :max="selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0" min="1" />
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
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-item label {
  font-size: 12px;
  color: var(--text-muted);
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-card);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.col-num {
  text-align: right;
  white-space: nowrap;
}

.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.partial { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }

.text-muted { color: var(--text-muted); }

.btn-action {
  padding: 4px 10px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-action:hover { background-color: var(--accent-blue-hover); }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.page-btn {
  padding: 6px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) { background-color: var(--bg-tertiary); }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.page-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.form-select, .form-input {
  padding: 6px 10px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  min-width: 150px;
}

.form-input { width: 180px; }

.form-select:focus, .form-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.btn-primary {
  padding: 6px 14px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover { background-color: var(--accent-blue-hover); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  padding: 6px 14px;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover { background-color: var(--bg-tertiary); }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 400px;
  max-width: 90vw;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover { color: var(--text-primary); }

.modal-body {
  padding: 20px;
}

.info-row {
  display: flex;
  margin-bottom: 12px;
  font-size: 13px;
}

.info-label {
  color: var(--text-secondary);
  min-width: 100px;
}

.form-group {
  margin-top: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}
</style>
