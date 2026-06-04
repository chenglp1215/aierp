<script setup lang="ts">
defineOptions({ name: 'SalesWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { salesOrderApi } from '../../services/api'

// Types
interface SalesOrderItem {
  id: number
  row_no: number
  product_id: number | null
  product_name: string | null
  product_code: string | null
  spec_id: number | null
  spec_code: string | null
  brand_id: number | null
  brand_name: string | null
  warehouse_id: number | null
  warehouse_name: string | null
  qty: number
  price: number
  discount: number
  discounted_price: number | null
  amt: number | null
  shipping_method: string | null
  pushed: boolean
  out_qty: number
  return_qty: number
  exchange_qty: number
  supplement_qty: number
  created_at: string
  updated_at: string
}

interface SalesOrder {
  id: number
  order_no: string
  order_date: string
  customer_id: number
  customer_name: string
  sale_user_id: number | null
  sale_user_name: string | null
  order_status: string
  delivery_status: string
  push_status: string | null
  invoice_status: string
  finance_status: string
  total_amt: number
  tax_rate: number
  tax_amt: number
  total_tax_amt: number
  total_discount_amt: number
  cost_amt: number
  profit_amt: number
  expect_deliver_date: string | null
  settle_type: string | null
  remark: string | null
  creator_id: number | null
  creator_name: string | null
  created_at: string
  updated_at: string
  items: SalesOrderItem[]
}

// 状态映射
const statusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待审核', class: 'pending' },
  audited: { label: '已审核', class: 'audited' },
  partially_pushed_to_purchase: { label: '部分下推', class: 'partial-pushed' },
  pushed_to_purchase: { label: '已下推', class: 'pushed' },
  closed: { label: '已关闭', class: 'closed' },
  cancelled: { label: '已取消', class: 'cancelled' },
  none: { label: '无', class: 'none' },
  partial: { label: '部分', class: 'partial' },
  full: { label: '完成', class: 'full' }
}

const financeStatusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'none' },
  partial_paid: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'full' },
  reconciled: { label: '已对账', class: 'closed' }
}

const getStatusInfo = (status: string) => statusMap[status] || { label: status, class: '' }
const getFinanceStatusInfo = (status: string) => financeStatusMap[status] || { label: status, class: '' }

// State
const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')

// 展开行状态
const expandedRows = ref<string[]>([])

// 选中行状态
const selectedOrders = ref<string[]>([])

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return orders.value.length > 0 && selectedOrders.value.length === orders.value.length
})

// 格式化方法
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatAmount = (amount: number) => {
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

// 加载订单列表
const loadOrders = async () => {
  loading.value = true
  try {
    const res = await salesOrderApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      order_no: keyword.value || undefined
    })
    orders.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载订单列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 展开/收起行
const toggleExpand = (orderNo: string) => {
  const index = expandedRows.value.indexOf(orderNo)
  if (index === -1) {
    expandedRows.value.push(orderNo)
  } else {
    expandedRows.value.splice(index, 1)
  }
}

// 选中/取消选中订单
const handleSelectOrder = (orderNo: string) => {
  const index = selectedOrders.value.indexOf(orderNo)
  if (index === -1) {
    selectedOrders.value.push(orderNo)
  } else {
    selectedOrders.value.splice(index, 1)
  }
}

// 全选/取消全选
const handleSelectAll = () => {
  if (isAllSelected.value) {
    selectedOrders.value = []
  } else {
    selectedOrders.value = orders.value.map(o => o.order_no)
  }
}

// 清除选择
const clearSelection = () => {
  selectedOrders.value = []
}

// 批量提交审核
const handleBatchSubmit = async () => {
  if (selectedOrders.value.length === 0) {
    window.showToast('请选择要提交的订单', 'warning')
    return
  }

  let successCount = 0
  let skipCount = 0

  for (const orderNo of selectedOrders.value) {
    const order = orders.value.find(o => o.order_no === orderNo)
    if (order && order.order_status === 'draft') {
      try {
        await salesOrderApi.submit(orderNo)
        successCount++
      } catch (error) {
        console.error(`提交订单 ${orderNo} 失败:`, error)
      }
    } else {
      skipCount++
    }
  }

  if (successCount > 0) {
    window.showToast(`成功提交 ${successCount} 个订单`, 'success')
    loadOrders()
    clearSelection()
  }
  if (skipCount > 0) {
    window.showToast(`跳过 ${skipCount} 个非草稿状态订单`, 'info')
  }
}

// 搜索
const handleSearch = () => {
  page.value = 1
  loadOrders()
}

// 重置筛选
const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  page.value = 1
  loadOrders()
}

// 分页
const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadOrders()
}

// 提交审核
const handleSubmitOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.submit(orderNo)
    window.showToast('订单已提交审核', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '提交失败', 'error')
  }
}

// 审核通过
const handleApproveOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.approve(orderNo)
    window.showToast('订单审核通过', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  }
}

// 驳回
const handleRejectOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.reject(orderNo)
    window.showToast('订单已驳回', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  }
}

// 订单状态选项
const orderStatuses = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '待审核' },
  { value: 'audited', label: '已审核' },
  { value: 'partially_pushed_to_purchase', label: '部分下推' },
  { value: 'pushed_to_purchase', label: '已下推' },
  { value: 'closed', label: '已关闭' },
  { value: 'cancelled', label: '已取消' }
]

onMounted(() => {
  loadOrders()
})
</script>

<template>
  <div class="sales-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">销售管理</h2>
      <button class="primary-btn">新建销售订单</button>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索订单编号..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option v-for="s in orderStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="keyword || filterStatus">重置</button>
      </div>
    </div>

    <!-- 批量操作 -->
    <div class="batch-actions" v-if="selectedOrders.length > 0">
      <span class="selected-count">已选择 {{ selectedOrders.length }} 条</span>
      <button class="batch-btn" @click="handleBatchSubmit">批量提交审核</button>
      <button class="batch-btn secondary" @click="clearSelection">取消选择</button>
    </div>

    <!-- 表格区域 -->
    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 40px">
              <input type="checkbox" @change="handleSelectAll" :checked="isAllSelected" />
            </th>
            <th style="width: 40px"></th>
            <th style="width: 110px">订单日期</th>
            <th style="width: 130px">订单编号</th>
            <th>客户名称</th>
            <th style="width: 100px; text-align: right">订单金额</th>
            <th style="width: 80px">订单状态</th>
            <th style="width: 80px; text-align: right">成本</th>
            <th style="width: 80px; text-align: right">利润</th>
            <th style="width: 80px">财务状态</th>
            <th style="width: 80px">发票状态</th>
            <th style="width: 80px">发货状态</th>
            <th style="width: 80px">下推状态</th>
            <th style="width: 80px">业务员</th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="15" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="orders.length === 0">
            <td colspan="15" class="empty-cell">暂无数据</td>
          </tr>
          <template v-else v-for="order in orders" :key="order.order_no">
            <tr :class="{ 'selected-row': selectedOrders.includes(order.order_no) }">
              <td>
                <input
                  type="checkbox"
                  :checked="selectedOrders.includes(order.order_no)"
                  @change="handleSelectOrder(order.order_no)"
                />
              </td>
              <td>
                <button class="expand-btn" @click="toggleExpand(order.order_no)">
                  {{ expandedRows.includes(order.order_no) ? '▼' : '▶' }}
                </button>
              </td>
              <td>{{ formatDate(order.order_date) }}</td>
              <td>{{ order.order_no }}</td>
              <td>{{ order.customer_name }}</td>
              <td style="text-align: right">{{ formatAmount(order.total_tax_amt) }}</td>
              <td>
                <span class="status-tag" :class="getStatusInfo(order.order_status).class">
                  {{ getStatusInfo(order.order_status).label }}
                </span>
              </td>
              <td style="text-align: right">{{ formatAmount(order.cost_amt) }}</td>
              <td style="text-align: right" :class="{ 'profit-positive': order.profit_amt >= 0, 'profit-negative': order.profit_amt < 0 }">
                {{ formatAmount(order.profit_amt) }}
              </td>
              <td>
                <span class="status-tag" :class="getFinanceStatusInfo(order.finance_status).class">
                  {{ getFinanceStatusInfo(order.finance_status).label }}
                </span>
              </td>
              <td>
                <span class="status-tag" :class="getStatusInfo(order.invoice_status).class">
                  {{ getStatusInfo(order.invoice_status).label }}
                </span>
              </td>
              <td>
                <span class="status-tag" :class="getStatusInfo(order.delivery_status).class">
                  {{ getStatusInfo(order.delivery_status).label }}
                </span>
              </td>
              <td>
                <span class="status-tag" :class="getStatusInfo(order.push_status || 'none').class">
                  {{ getStatusInfo(order.push_status || 'none').label }}
                </span>
              </td>
              <td>{{ order.sale_user_name || '-' }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link">详情</button>
                  <button class="btn-link" v-if="order.order_status === 'draft'">编辑</button>
                  <button class="btn-link highlight" @click="handleSubmitOrder(order.order_no)" v-if="order.order_status === 'draft'">提交审核</button>
                  <button class="btn-link success" @click="handleApproveOrder(order.order_no)" v-if="order.order_status === 'pending'">审核通过</button>
                  <button class="btn-link warning" @click="handleRejectOrder(order.order_no)" v-if="order.order_status === 'pending'">驳回</button>
                </div>
              </td>
            </tr>
            <!-- 展开行 - 商品明细 -->
            <tr v-if="expandedRows.includes(order.order_no)" class="expanded-row">
              <td colspan="15">
                <div class="expanded-content">
                  <table class="items-detail-table">
                    <thead>
                      <tr>
                        <th>品牌名</th>
                        <th>规格编号</th>
                        <th>产品名称</th>
                        <th>数量</th>
                        <th style="text-align: right">原价</th>
                        <th style="text-align: right">退货</th>
                        <th style="text-align: right">换货</th>
                        <th style="text-align: right">补货</th>
                        <th style="text-align: right">含税单价</th>
                        <th style="text-align: right">合计</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in order.items" :key="item.id">
                        <td>{{ item.brand_name || '-' }}</td>
                        <td>{{ item.spec_code || '-' }}</td>
                        <td>{{ item.product_name || '-' }}</td>
                        <td style="text-align: right">{{ item.qty }}</td>
                        <td style="text-align: right">{{ formatAmount(item.price) }}</td>
                        <td style="text-align: right">{{ item.return_qty }}</td>
                        <td style="text-align: right">{{ item.exchange_qty }}</td>
                        <td style="text-align: right">{{ item.supplement_qty }}</td>
                        <td style="text-align: right">{{ formatAmount(item.price * (1 + (order.tax_rate || 0.13))) }}</td>
                        <td style="text-align: right">{{ formatAmount(item.amt || 0) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <div class="pagination" v-if="total > 0">
        <span class="pagination-info">共 {{ total }} 条</span>
        <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
        <span class="pagination-current">第 {{ page }} 页</span>
        <button class="pagination-btn" :disabled="orders.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sales-workspace {
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
  color: var(--color-ink);
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  border: none;
  cursor: pointer;
}

.primary-btn:hover {
  background-color: var(--color-interactive-hover);
}

/* 筛选区域 */
.filter-section {
  background-color: var(--color-canvas);
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
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.filter-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.filter-select {
  padding: 8px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
  cursor: pointer;
  min-width: 120px;
}

.filter-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background-color: var(--color-interactive-hover);
}

.filter-btn.reset-btn {
  background-color: transparent;
  color: var(--color-muted);
  border: 1px solid var(--color-hairline);
}

.filter-btn.reset-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-ink);
}

/* 批量操作 */
.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: var(--color-info-bg);
  border-radius: var(--radius-md);
}

.selected-count {
  font-size: 14px;
  color: var(--color-interactive);
  font-weight: 500;
}

.batch-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.batch-btn:hover {
  background-color: var(--color-interactive-hover);
}

.batch-btn.secondary {
  background-color: transparent;
  color: var(--color-muted);
  border: 1px solid var(--color-hairline);
}

.batch-btn.secondary:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-ink);
}

/* 表格区域 */
.table-section {
  background-color: var(--color-canvas);
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
  border-bottom: 1px solid var(--color-hairline);
}

.data-table th {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.data-table td {
  font-size: 13px;
  color: var(--color-ink);
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--color-muted);
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.draft { background-color: var(--color-neutral-bg); color: var(--color-muted); }
.status-tag.pending { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.audited { background-color: var(--color-info-bg); color: var(--color-interactive); }
.status-tag.partial-pushed { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.pushed { background-color: var(--color-accent-soft); color: #c4391a; }
.status-tag.closed { background-color: var(--color-success-bg); color: var(--color-success); }
.status-tag.cancelled { background-color: var(--color-danger-bg); color: var(--color-danger); }
.status-tag.none { background-color: var(--color-neutral-bg); color: var(--color-muted); }
.status-tag.partial { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.full { background-color: var(--color-success-bg); color: var(--color-success); }

/* 展开行 */
.expand-btn {
  background: none;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: 4px;
  font-size: 12px;
}

.expand-btn:hover {
  color: var(--color-interactive);
}

.expanded-row {
  background-color: var(--color-neutral-bg);
}

.expanded-content {
  padding: 12px 20px;
}

.items-detail-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-canvas);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.items-detail-table th,
.items-detail-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 12px;
}

.items-detail-table th {
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.items-detail-table td {
  color: var(--color-ink);
}

/* 选中行 */
.selected-row {
  background-color: var(--color-info-bg) !important;
}

/* 利润颜色 */
.profit-positive {
  color: var(--color-success);
}

.profit-negative {
  color: var(--color-danger);
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 4px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-link:hover {
  background-color: var(--color-info-bg);
}

.btn-link.highlight {
  color: var(--color-success);
  font-weight: 500;
}

.btn-link.success {
  color: var(--color-success);
}

.btn-link.success:hover {
  background-color: var(--color-success-bg);
}

.btn-link.warning {
  color: var(--color-warning);
}

.btn-link.warning:hover {
  background-color: var(--color-warning-bg);
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-hairline);
}

.pagination-info {
  font-size: 13px;
  color: var(--color-muted);
}

.pagination-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: var(--color-neutral-bg);
  color: var(--color-ink);
  font-size: 13px;
  border: 1px solid var(--color-hairline);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.pagination-btn:hover:not(:disabled) {
  background-color: var(--color-interactive);
  color: white;
  border-color: var(--color-interactive);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-current {
  font-size: 13px;
  color: var(--color-muted);
}
</style>
