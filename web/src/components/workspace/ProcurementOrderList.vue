<script setup lang="ts">
defineOptions({ name: 'ProcurementOrderList' })

import { ref, computed, onMounted } from 'vue'
import { procurementOrderApi } from '../../services/api'

// Types
interface ProcurementOrderItem {
  product_id: string
  product_name: string
  product_code?: string
  quantity: number
  unit_price: number
  subtotal: number
}

interface ProcurementOrder {
  id: string
  procurement_no: string
  supplier_id: string
  supplier_name: string
  contact_phone?: string
  delivery_address?: string
  items: ProcurementOrderItem[]
  total_amount: number
  status: string
  sales_order_id?: string
  expected_delivery_date?: string
  remarks?: string
  created_at: string
  updated_at: string
}

// Constants
const statusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待确认', class: 'pending' },
  confirmed: { label: '已确认', class: 'confirmed' },
  purchased: { label: '已采购', class: 'purchased' },
  received: { label: '已收货', class: 'received' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const orderStatuses = Object.entries(statusMap).map(([value, { label }]) => ({ value, label }))

// State
const loading = ref(false)
const orders = ref<ProcurementOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')

// Modals
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const selectedOrder = ref<ProcurementOrder | null>(null)
const deleteTargetId = ref<string | null>(null)
const deleteLoading = ref(false)
const detailLoading = ref(false)

// Computed
const hasActiveFilters = computed(() => !!(keyword.value || filterStatus.value))

// Methods
const loadOrders = async () => {
  loading.value = true
  try {
    const res = await procurementOrderApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      keyword: keyword.value || undefined
    })
    orders.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载采购单列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  loadOrders()
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadOrders()
}

const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  page.value = 1
  loadOrders()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const openDetail = async (order: ProcurementOrder) => {
  selectedOrder.value = order
  detailLoading.value = true
  showDetailModal.value = true
  try {
    const res = await procurementOrderApi.getById(order.id)
    selectedOrder.value = res
  } catch (error) {
    console.error('加载采购单详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const confirmDelete = (orderId: string) => {
  deleteTargetId.value = orderId
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  deleteLoading.value = true
  try {
    await procurementOrderApi.delete(deleteTargetId.value)
    alert('采购单删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadOrders()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const handleUpdateStatus = async (orderId: string, status: string) => {
  try {
    await procurementOrderApi.updateStatus(orderId, status)
    alert('状态更新成功')
    loadOrders()
    if (selectedOrder.value?.id === orderId) {
      const res = await procurementOrderApi.getById(orderId)
      selectedOrder.value = res
    }
  } catch (error: any) {
    alert(error.message || '状态更新失败')
  }
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatAmount = (amount: number) => {
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

const getStatusInfo = (status: string) => statusMap[status] || { label: status, class: '' }

// Lifecycle
onMounted(() => {
  loadOrders()
})
</script>

<template>
  <div class="procurement-order-list">
    <div class="workspace-header">
      <h2 class="workspace-title">采购单管理</h2>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索采购单编号、供应商..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in orderStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
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
          状态: {{ getStatusInfo(filterStatus).label }}
          <button class="tag-close" @click="filterStatus = ''; handleSearch()">×</button>
        </span>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 140px">采购单编号</th>
            <th>供应商名称</th>
            <th style="width: 100px">联系电话</th>
            <th style="width: 120px; text-align: right">采购金额</th>
            <th style="width: 80px">采购状态</th>
            <th style="width: 140px">关联销售单</th>
            <th style="width: 100px">创建日期</th>
            <th style="width: 120px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="orders.length === 0">
            <td colspan="8" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="order in orders" :key="order.id">
            <td>{{ order.procurement_no }}</td>
            <td>{{ order.supplier_name }}</td>
            <td>{{ order.contact_phone || '-' }}</td>
            <td style="text-align: right">{{ formatAmount(order.total_amount) }}</td>
            <td>
              <span class="status-tag" :class="getStatusInfo(order.status).class">
                {{ getStatusInfo(order.status).label }}
              </span>
            </td>
            <td>{{ order.sales_order_id || '-' }}</td>
            <td>{{ formatDate(order.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openDetail(order)">详情</button>
                <button class="btn-link danger" @click="confirmDelete(order.id)" v-if="order.status === 'draft'">删除</button>
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
      <button class="pagination-btn" :disabled="orders.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <!-- Order Detail Modal -->
    <div class="modal-overlay" v-if="showDetailModal" @click.self="showDetailModal = false">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>采购单详情 - {{ selectedOrder?.procurement_no }}</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedOrder">
          <div class="detail-loading" v-if="detailLoading">加载中...</div>
          <template v-else>
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>采购单编号</label>
                  <span>{{ selectedOrder.procurement_no }}</span>
                </div>
                <div class="detail-item">
                  <label>采购状态</label>
                  <span class="status-tag" :class="getStatusInfo(selectedOrder.status).class">
                    {{ getStatusInfo(selectedOrder.status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>创建时间</label>
                  <span>{{ formatDateTime(selectedOrder.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>更新时间</label>
                  <span>{{ formatDateTime(selectedOrder.updated_at) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>供应商信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>供应商名称</label>
                  <span>{{ selectedOrder.supplier_name }}</span>
                </div>
                <div class="detail-item">
                  <label>联系电话</label>
                  <span>{{ selectedOrder.contact_phone || '-' }}</span>
                </div>
                <div class="detail-item full-width">
                  <label>交货地址</label>
                  <span>{{ selectedOrder.delivery_address || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedOrder.sales_order_id">
              <h4>关联销售订单</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>销售订单ID</label>
                  <span>{{ selectedOrder.sales_order_id }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>商品明细</h4>
              <table class="detail-table">
                <thead>
                  <tr>
                    <th>商品名称</th>
                    <th>商品编码</th>
                    <th style="text-align: right">数量</th>
                    <th style="text-align: right">采购单价</th>
                    <th style="text-align: right">小计</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in selectedOrder.items" :key="index">
                    <td>{{ item.product_name }}</td>
                    <td>{{ item.product_code || '-' }}</td>
                    <td style="text-align: right">{{ item.quantity }}</td>
                    <td style="text-align: right">{{ formatAmount(item.unit_price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.subtotal) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="4" style="text-align: right; font-weight: 600;">采购总金额：</td>
                    <td style="text-align: right; font-weight: 600;" class="amount-highlight">
                      {{ formatAmount(selectedOrder.total_amount) }}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div class="detail-section" v-if="selectedOrder.expected_delivery_date">
              <h4>预计交货日期</h4>
              <p class="info-text">{{ formatDate(selectedOrder.expected_delivery_date) }}</p>
            </div>

            <div class="detail-section" v-if="selectedOrder.remarks">
              <h4>备注</h4>
              <p class="remarks-text">{{ selectedOrder.remarks }}</p>
            </div>

            <div class="detail-section" v-if="selectedOrder.status !== 'cancelled' && selectedOrder.status !== 'received'">
              <h4>状态更新</h4>
              <div class="status-actions">
                <button
                  class="btn-primary"
                  @click="handleUpdateStatus(selectedOrder.id, 'confirmed')"
                  v-if="selectedOrder.status === 'draft' || selectedOrder.status === 'pending'"
                >
                  确认采购
                </button>
                <button
                  class="btn-primary"
                  @click="handleUpdateStatus(selectedOrder.id, 'purchased')"
                  v-if="selectedOrder.status === 'confirmed'"
                >
                  已采购
                </button>
                <button
                  class="btn-primary"
                  @click="handleUpdateStatus(selectedOrder.id, 'received')"
                  v-if="selectedOrder.status === 'purchased'"
                >
                  已收货
                </button>
                <button
                  class="btn-danger"
                  @click="handleUpdateStatus(selectedOrder.id, 'cancelled')"
                  v-if="['draft', 'pending', 'confirmed'].includes(selectedOrder.status)"
                >
                  取消采购
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该采购单吗？此操作不可恢复。</p>
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
.procurement-order-list {
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
  min-width: 120px;
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
  overflow-x: auto;
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

.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.confirmed { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.purchased { background-color: rgba(139, 92, 246, 0.1); color: var(--accent-purple); }
.status-tag.received { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }

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

/* Modal styles */
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
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.detail-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  background-color: var(--bg-card);
  z-index: 1;
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
  gap: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.detail-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.detail-section {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
}

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full-width {
  grid-column: span 3;
}

.detail-item label {
  font-size: 12px;
  color: var(--text-muted);
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.detail-table th,
.detail-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.detail-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.detail-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.detail-table tfoot td {
  border-bottom: none;
  background-color: var(--bg-secondary);
}

.amount-highlight {
  color: var(--accent-blue) !important;
  font-weight: 600;
}

.info-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}

.remarks-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
}

.status-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Buttons */
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
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-item.full-width {
    grid-column: span 2;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>
