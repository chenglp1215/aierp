<script setup lang="ts">
defineOptions({ name: 'SalesWorkspace' })

import { ref, onMounted } from 'vue'
import DataTable from './DataTable.vue'
import { salesOrderApi } from '../../services/api'

interface SalesOrder {
  id: string
  order_no: string
  customer_name: string
  final_amount: number
  status: string
  payment_status: string
  order_date: string
}

const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const columns = [
  { key: 'order_no', label: '订单编号', width: '140px' },
  { key: 'customer_name', label: '客户名称' },
  { key: 'final_amount', label: '订单金额', align: 'right' as const },
  { key: 'status', label: '订单状态' },
  { key: 'payment_status', label: '付款状态' },
  { key: 'order_date', label: '下单日期' }
]

const statusMap: Record<string, string> = {
  draft: '草稿',
  pending: '待确认',
  confirmed: '已确认',
  processing: '处理中',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消'
}

const paymentStatusMap: Record<string, string> = {
  unpaid: '未付款',
  partial: '部分付款',
  paid: '已付款'
}

const formatStatus = (status: string) => statusMap[status] || status
const formatPaymentStatus = (status: string) => paymentStatusMap[status] || status
const formatAmount = (amount: number) => `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`

const loadOrders = async () => {
  loading.value = true
  try {
    const res = await salesOrderApi.list({ page: page.value, page_size: pageSize.value })
    orders.value = res.items.map((item: any) => ({
      ...item,
      status: formatStatus(item.status),
      payment_status: formatPaymentStatus(item.payment_status),
      final_amount: formatAmount(item.final_amount),
      order_date: item.order_date ? new Date(item.order_date).toLocaleDateString('zh-CN') : '-'
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载订单列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAction = (actionId: string, row: any) => {
  console.log('Action:', actionId, row)
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadOrders()
}

onMounted(() => {
  loadOrders()
})
</script>

<template>
  <div class="sales-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">销售管理</h2>
      <button class="primary-btn" @click="handleAction('create', null)">新建销售订单</button>
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">销售订单列表</h3>
        <div class="section-actions">
          <input type="text" class="search-input" placeholder="搜索订单..." />
          <button class="action-btn">筛选</button>
          <button class="action-btn">导出</button>
        </div>
      </div>
      <DataTable
        :columns="columns"
        :data="orders"
        :loading="loading"
        :actions="[{ id: 'detail', label: '详情', type: 'default' as const }, { id: 'ship', label: '发货', type: 'primary' as const }]"
        @action="handleAction"
      />
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

.table-section {
  background-color: var(--bg-card);
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
  color: var(--text-primary);
}

.section-actions {
  display: flex;
  gap: 8px;
}

.search-input {
  padding: 6px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.action-btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
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
</style>
