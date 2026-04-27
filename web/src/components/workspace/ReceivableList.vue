<script setup lang="ts">
defineOptions({ name: 'ReceivableList' })

import { ref, computed, onMounted } from 'vue'
import { receivableApi, customerApi } from '../../services/api'

// Types
interface PaymentRecord {
  amount: number
  payment_method?: string
  payment_date?: string
  remarks?: string
}

interface Receivable {
  id: string
  receivable_no: string
  customer_id: string
  customer_name: string
  sales_order_id: string
  sales_order_no: string
  total_amount: number
  paid_amount: number
  status: string
  records: PaymentRecord[]
  remarks?: string
  created_at: string
  updated_at: string
}

interface Customer {
  id: string
  name: string
}

// Constants
const statusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'unpaid' },
  partial: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'paid' },
  overdue: { label: '逾期', class: 'overdue' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const paymentMethods = [
  { value: 'cash', label: '现金' },
  { value: 'bank_transfer', label: '银行转账' },
  { value: 'wechat', label: '微信' },
  { value: 'alipay', label: '支付宝' },
  { value: 'other', label: '其他' }
]

const receivableStatuses = Object.entries(statusMap).map(([value, { label }]) => ({ value, label }))

// State
const loading = ref(false)
const receivables = ref<Receivable[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')
const filterCustomerId = ref('')

// Modals
const showDetailModal = ref(false)
const showPaymentModal = ref(false)
const showDeleteConfirm = ref(false)
const selectedReceivable = ref<Receivable | null>(null)
const deleteTargetId = ref<string | null>(null)
const detailLoading = ref(false)
const paymentLoading = ref(false)
const deleteLoading = ref(false)

// Customer list for dropdown
const customerList = ref<Customer[]>([])

// Payment form
const paymentForm = ref({
  amount: 0,
  payment_method: '',
  remarks: ''
})

// Computed
const hasActiveFilters = computed(() => !!(keyword.value || filterStatus.value || filterCustomerId.value))

// Methods
const loadReceivables = async () => {
  loading.value = true
  try {
    const res = await receivableApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      customer_id: filterCustomerId.value || undefined,
      keyword: keyword.value || undefined
    })
    receivables.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载应收单列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    const res = await customerApi.list({ page_size: 100 })
    customerList.value = res.items.map((c: any) => ({ id: c.id, name: c.name }))
  } catch (error) {
    console.error('加载客户列表失败:', error)
  }
}

const handleSearch = () => {
  page.value = 1
  loadReceivables()
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadReceivables()
}

const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  filterCustomerId.value = ''
  page.value = 1
  loadReceivables()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const openDetail = async (receivable: Receivable) => {
  selectedReceivable.value = receivable
  detailLoading.value = true
  showDetailModal.value = true
  try {
    const res = await receivableApi.getById(receivable.id)
    selectedReceivable.value = res
  } catch (error) {
    console.error('加载应收单详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const openPaymentModal = (receivable: Receivable) => {
  selectedReceivable.value = receivable
  const remainingAmount = receivable.total_amount - receivable.paid_amount
  paymentForm.value = {
    amount: remainingAmount,
    payment_method: '',
    remarks: ''
  }
  showPaymentModal.value = true
}

const closePaymentModal = () => {
  showPaymentModal.value = false
  selectedReceivable.value = null
  paymentForm.value = {
    amount: 0,
    payment_method: '',
    remarks: ''
  }
}

const confirmDelete = (receivableId: string) => {
  deleteTargetId.value = receivableId
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  deleteLoading.value = true
  try {
    await receivableApi.delete(deleteTargetId.value)
    alert('应收单删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadReceivables()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const handleRecordPayment = async () => {
  if (!selectedReceivable.value) return
  if (paymentForm.value.amount <= 0) {
    alert('请输入正确的付款金额')
    return
  }
  if (paymentForm.value.amount > selectedReceivable.value.total_amount - selectedReceivable.value.paid_amount) {
    alert('付款金额不能超过剩余应付金额')
    return
  }

  paymentLoading.value = true
  try {
    await receivableApi.recordPayment(selectedReceivable.value.id, {
      amount: paymentForm.value.amount,
      payment_method: paymentForm.value.payment_method || undefined,
      remarks: paymentForm.value.remarks || undefined
    })
    alert('收款记录成功')
    closePaymentModal()
    loadReceivables()
    // Refresh detail if modal is open
    if (showDetailModal.value && selectedReceivable.value) {
      const res = await receivableApi.getById(selectedReceivable.value.id)
      selectedReceivable.value = res
    }
  } catch (error: any) {
    alert(error.message || '收款记录失败')
  } finally {
    paymentLoading.value = false
  }
}

const handleUpdateStatus = async (receivableId: string, status: string) => {
  try {
    await receivableApi.updateStatus(receivableId, status)
    alert('状态更新成功')
    loadReceivables()
    if (selectedReceivable.value?.id === receivableId) {
      const res = await receivableApi.getById(receivableId)
      selectedReceivable.value = res
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

const getPaymentMethodLabel = (method: string | undefined) => {
  if (!method) return '-'
  return paymentMethods.find(m => m.value === method)?.label || method
}

const getRemainingAmount = (receivable: Receivable) => {
  return receivable.total_amount - receivable.paid_amount
}

const getPaymentProgress = (receivable: Receivable) => {
  if (receivable.total_amount === 0) return 0
  return Math.round((receivable.paid_amount / receivable.total_amount) * 100)
}

// Lifecycle
onMounted(() => {
  loadReceivables()
  loadCustomers()
})
</script>

<template>
  <div class="receivable-list">
    <div class="workspace-header">
      <h2 class="workspace-title">应收款管理</h2>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索应收单编号、客户名称..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterCustomerId" @change="handleSearch">
            <option value="">全部客户</option>
            <option v-for="c in customerList" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in receivableStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
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
            <th style="width: 140px">应收单编号</th>
            <th>客户名称</th>
            <th style="width: 130px">关联订单</th>
            <th style="width: 120px; text-align: right">应收金额</th>
            <th style="width: 120px; text-align: right">已收金额</th>
            <th style="width: 80px">收款状态</th>
            <th style="width: 100px">创建日期</th>
            <th style="width: 150px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="receivables.length === 0">
            <td colspan="8" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="receivable in receivables" :key="receivable.id">
            <td>{{ receivable.receivable_no }}</td>
            <td>{{ receivable.customer_name }}</td>
            <td>{{ receivable.sales_order_no }}</td>
            <td style="text-align: right">{{ formatAmount(receivable.total_amount) }}</td>
            <td style="text-align: right">
              <span class="amount-paid">{{ formatAmount(receivable.paid_amount) }}</span>
            </td>
            <td>
              <span class="status-tag" :class="getStatusInfo(receivable.status).class">
                {{ getStatusInfo(receivable.status).label }}
              </span>
            </td>
            <td>{{ formatDate(receivable.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openDetail(receivable)">详情</button>
                <button class="btn-link highlight" @click="openPaymentModal(receivable)" v-if="receivable.status !== 'paid' && receivable.status !== 'cancelled'">收款</button>
                <button class="btn-link danger" @click="confirmDelete(receivable.id)" v-if="receivable.status === 'unpaid'">删除</button>
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
      <button class="pagination-btn" :disabled="receivables.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <!-- Receivable Detail Modal -->
    <div class="modal-overlay" v-if="showDetailModal" @click.self="showDetailModal = false">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>应收单详情 - {{ selectedReceivable?.receivable_no }}</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedReceivable">
          <div class="detail-loading" v-if="detailLoading">加载中...</div>
          <template v-else>
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>应收单编号</label>
                  <span>{{ selectedReceivable.receivable_no }}</span>
                </div>
                <div class="detail-item">
                  <label>收款状态</label>
                  <span class="status-tag" :class="getStatusInfo(selectedReceivable.status).class">
                    {{ getStatusInfo(selectedReceivable.status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>创建时间</label>
                  <span>{{ formatDateTime(selectedReceivable.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>更新时间</label>
                  <span>{{ formatDateTime(selectedReceivable.updated_at) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>客户与订单信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>客户名称</label>
                  <span>{{ selectedReceivable.customer_name }}</span>
                </div>
                <div class="detail-item">
                  <label>销售订单编号</label>
                  <span>{{ selectedReceivable.sales_order_no }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>收款信息</h4>
              <div class="payment-summary">
                <div class="payment-progress-bar">
                  <div
                    class="payment-progress-fill"
                    :style="{ width: getPaymentProgress(selectedReceivable) + '%' }"
                  ></div>
                </div>
                <div class="payment-summary-row">
                  <div class="payment-summary-item">
                    <span class="label">应收金额</span>
                    <span class="value">{{ formatAmount(selectedReceivable.total_amount) }}</span>
                  </div>
                  <div class="payment-summary-item">
                    <span class="label">已收金额</span>
                    <span class="value highlight">{{ formatAmount(selectedReceivable.paid_amount) }}</span>
                  </div>
                  <div class="payment-summary-item">
                    <span class="label">剩余金额</span>
                    <span class="value" :class="{ 'amount-danger': getRemainingAmount(selectedReceivable) > 0 }">
                      {{ formatAmount(getRemainingAmount(selectedReceivable)) }}
                    </span>
                  </div>
                  <div class="payment-summary-item">
                    <span class="label">收款进度</span>
                    <span class="value">{{ getPaymentProgress(selectedReceivable) }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-header-row">
                <h4>收款记录</h4>
                <button
                  class="btn-primary btn-sm"
                  @click="openPaymentModal(selectedReceivable)"
                  v-if="selectedReceivable.status !== 'paid' && selectedReceivable.status !== 'cancelled'"
                >
                  记录收款
                </button>
              </div>
              <div class="records-list" v-if="selectedReceivable.records && selectedReceivable.records.length > 0">
                <table class="records-table">
                  <thead>
                    <tr>
                      <th>收款金额</th>
                      <th>付款方式</th>
                      <th>收款日期</th>
                      <th>备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(record, index) in selectedReceivable.records" :key="index">
                      <td class="amount-cell">{{ formatAmount(record.amount) }}</td>
                      <td>{{ getPaymentMethodLabel(record.payment_method) }}</td>
                      <td>{{ formatDateTime(record.payment_date) }}</td>
                      <td>{{ record.remarks || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="empty-records" v-else>
                暂无收款记录
              </div>
            </div>

            <div class="detail-section" v-if="selectedReceivable.remarks">
              <h4>备注</h4>
              <p class="remarks-text">{{ selectedReceivable.remarks }}</p>
            </div>

            <div class="detail-section" v-if="selectedReceivable.status !== 'cancelled'">
              <h4>状态更新</h4>
              <div class="status-actions">
                <button
                  class="btn-danger"
                  @click="handleUpdateStatus(selectedReceivable.id, 'cancelled')"
                  v-if="['unpaid', 'partial', 'overdue'].includes(selectedReceivable.status)"
                >
                  取消应收单
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <div class="modal-overlay" v-if="showPaymentModal" @click.self="closePaymentModal">
      <div class="modal payment-modal">
        <div class="modal-header">
          <h3>记录收款</h3>
          <button class="modal-close" @click="closePaymentModal">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedReceivable">
          <div class="payment-info">
            <div class="info-row">
              <span class="label">应收单编号：</span>
              <span class="value">{{ selectedReceivable.receivable_no }}</span>
            </div>
            <div class="info-row">
              <span class="label">客户名称：</span>
              <span class="value">{{ selectedReceivable.customer_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">应收金额：</span>
              <span class="value">{{ formatAmount(selectedReceivable.total_amount) }}</span>
            </div>
            <div class="info-row">
              <span class="label">已收金额：</span>
              <span class="value">{{ formatAmount(selectedReceivable.paid_amount) }}</span>
            </div>
            <div class="info-row highlight">
              <span class="label">本次可收金额：</span>
              <span class="value">{{ formatAmount(getRemainingAmount(selectedReceivable)) }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>收款金额 *</label>
            <input
              type="number"
              v-model.number="paymentForm.amount"
              min="0.01"
              :max="getRemainingAmount(selectedReceivable)"
              step="0.01"
              placeholder="请输入收款金额"
            />
          </div>

          <div class="form-group">
            <label>付款方式</label>
            <select v-model="paymentForm.payment_method">
              <option value="">请选择付款方式</option>
              <option v-for="m in paymentMethods" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>备注</label>
            <textarea
              v-model="paymentForm.remarks"
              placeholder="请输入备注信息"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closePaymentModal">取消</button>
          <button class="btn-primary" @click="handleRecordPayment" :disabled="paymentLoading">
            {{ paymentLoading ? '提交中...' : '确认收款' }}
          </button>
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
          <p>确定要删除该应收单吗？此操作不可恢复。</p>
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
.receivable-list {
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

.amount-paid {
  color: var(--accent-green);
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.unpaid { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.paid { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.overdue { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.cancelled { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }

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

.btn-link.highlight {
  color: var(--accent-green);
  font-weight: 500;
}

.btn-link.highlight:hover {
  background-color: rgba(16, 185, 129, 0.1);
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

.payment-modal {
  max-width: 500px;
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
  gap: 20px;
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

.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-header-row h4 {
  margin: 0;
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

.detail-item label {
  font-size: 12px;
  color: var(--text-muted);
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
}

.payment-summary {
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  padding: 16px;
}

.payment-progress-bar {
  height: 8px;
  background-color: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.payment-progress-fill {
  height: 100%;
  background-color: var(--accent-green);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.payment-summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.payment-summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.payment-summary-item .label {
  font-size: 12px;
  color: var(--text-muted);
}

.payment-summary-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.payment-summary-item .value.highlight {
  color: var(--accent-green);
}

.payment-summary-item .value.amount-danger {
  color: var(--accent-red);
}

.records-list {
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
}

.records-table th,
.records-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.records-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.records-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.records-table .amount-cell {
  color: var(--accent-green);
  font-weight: 500;
}

.empty-records {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
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

/* Payment modal */
.payment-info {
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  padding: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
}

.info-row .label {
  color: var(--text-muted);
}

.info-row .value {
  color: var(--text-primary);
  font-weight: 500;
}

.info-row.highlight .value {
  color: var(--accent-blue);
  font-size: 16px;
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

.btn-primary.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
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

  .payment-summary-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>
