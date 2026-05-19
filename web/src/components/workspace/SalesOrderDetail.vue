<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { salesOrderApi, purchaseOrderApi, receivableApi, brandApi } from '../../services/api'
import PushPurchaseItemSelectModal from './PushPurchaseItemSelectModal.vue'

interface Props {
  orderNo?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  back: []
  navigate: [id: string, extra?: Record<string, any>]
}>()

// ============ 状态 ============
const loading = ref(true)
const order = ref<any>(null)
const flows = ref<any[]>([])
const purchaseOrders = ref<any[]>([])
const receivables = ref<any[]>([])
const actionLoading = ref(false)
const showPushItemSelect = ref(false)
const pushableItems = ref<any[]>([])

// 成本明细相关
const costItems = ref<any[]>([])
const activeMainTab = ref<'items' | 'purchase' | 'receivable' | 'cost'>('items')
const flowExpanded = ref(false)

// ============ 状态映射 ============
const orderStatusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待审核', class: 'pending' },  // 兼容历史数据
  audited: { label: '已审核', class: 'audited' },
  partially_pushed_to_purchase: { label: '部分下推', class: 'partial-pushed' },  // 文案调整
  pushed_to_purchase: { label: '已下推采购', class: 'pushed' },
  closed: { label: '已完成', class: 'closed' },  // 文案调整
  cancelled: { label: '已取消', class: 'cancelled' }
}

const deliveryStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未发货', class: 'none' },
  partial: { label: '部分发货', class: 'partial' },
  full: { label: '全部发货', class: 'full' }
}

const receiveStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未收货', class: 'none' },
  partial: { label: '部分收货', class: 'partial' },
  full: { label: '全部收货', class: 'full' }
}

const invoiceStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未开票', class: 'none' },
  partial: { label: '部分开票', class: 'partial' },
  full: { label: '全部开票', class: 'full' }
}

const financeStatusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'none' },
  partial_paid: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'full' },
  reconciled: { label: '已对账', class: 'reconciled' }
}

const purchaseStatusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  audited: { label: '已审核', class: 'audited' },
  closed: { label: '已结案', class: 'closed' },
  cancelled: { label: '已作废', class: 'cancelled' }
}

const receivableStatusMap: Record<string, { label: string; class: string }> = {
  pending: { label: '待收款', class: 'draft' },
  partial: { label: '部分收款', class: 'partial' },
  completed: { label: '已收清', class: 'full' },
  overdue: { label: '逾期', class: 'cancelled' }
}

const stockStatusMap: Record<string, { label: string; class: string }> = {
  normal: { label: '充足', class: 'stock-normal' },
  low_stock: { label: '偏低', class: 'stock-low' },
  out_of_stock: { label: '缺货', class: 'stock-out' },
  overstock: { label: '积压', class: 'stock-over' }
}

// 成本类型映射
const costTypeMap: Record<string, string> = {
  purchase: '采购成本',
  freight: '运费',
  transfer: '调货费',
  other: '其他'
}

// 来源类型映射
const sourceTypeMap: Record<string, string> = {
  purchase_order: '采购单',
  manual: '手动添加'
}

// ============ 测试状态修改弹窗 ============
const showTestStatusModal = ref(false)
const testStatusLoading = ref(false)
const testStatusForm = ref({
  delivery_status: '',
  receive_status: '',
  finance_status: '',
  invoice_status: ''
})

const deliveryStatusOptions = [
  { value: 'none', label: '未发货' },
  { value: 'partial', label: '部分发货' },
  { value: 'full', label: '全部发货' }
]

const receiveStatusOptions = [
  { value: 'none', label: '未收货' },
  { value: 'partial', label: '部分收货' },
  { value: 'full', label: '全部收货' }
]

const invoiceStatusOptions = [
  { value: 'none', label: '未开票' },
  { value: 'partial', label: '部分开票' },
  { value: 'full', label: '全部开票' }
]

const financeStatusOptions = [
  { value: 'unpaid', label: '未付款' },
  { value: 'partial_paid', label: '部分付款' },
  { value: 'paid', label: '已付款' },
  { value: 'reconciled', label: '已对账' }
]

const openTestStatusModal = () => {
  if (!order.value) return
  testStatusForm.value = {
    delivery_status: order.value.delivery_status || 'none',
    receive_status: order.value.receive_status || 'none',
    finance_status: order.value.finance_status || 'unpaid',
    invoice_status: order.value.invoice_status || 'none'
  }
  showTestStatusModal.value = true
}

const handleTestUpdateStatus = async () => {
  if (!order.value) return
  testStatusLoading.value = true
  try {
    const result = await salesOrderApi.testUpdateStatus(order.value.order_no, testStatusForm.value)
    window.showToast(result.auto_completed ? '状态已更新，订单已自动完成' : '状态已更新', 'success')
    showTestStatusModal.value = false
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
  } finally {
    testStatusLoading.value = false
  }
}

// ============ 计算属性 ============
const canPushPurchase = computed(() => {
  const s = order.value?.status?.order_status
  return s === 'audited' || s === 'partially_pushed_to_purchase'
})

// 成本合计
const totalCostAmount = computed(() => {
  return costItems.value.reduce((sum, item) => sum + (item.amount || 0), 0)
})

// 预估利润
const estimatedProfit = computed(() => {
  if (!order.value) return 0
  return (order.value.total_tax_amt || 0) - totalCostAmount.value
})

// ============ 数据加载 ============
const loadOrder = async () => {
  if (!props.orderNo) return
  loading.value = true
  try {
    const [orderData, flowsData] = await Promise.all([
      salesOrderApi.getByOrderNo(props.orderNo),
      salesOrderApi.getStatusFlows(props.orderNo)
    ])
    order.value = orderData
    flows.value = flowsData || []
    await Promise.all([loadPurchaseOrders(), loadReceivables(), loadCostItems()])
  } catch (e) {
    console.error('加载订单详情失败:', e)
  } finally {
    loading.value = false
  }
}

const loadPurchaseOrders = async () => {
  if (!props.orderNo) return
  try {
    const res = await purchaseOrderApi.list({ source_sale_order_no: props.orderNo, page_size: 100 })
    purchaseOrders.value = res?.items || []
  } catch (e) {
    console.error('加载关联采购单失败:', e)
  }
}

const loadReceivables = async () => {
  if (!props.orderNo) return
  try {
    const res = await receivableApi.list({ sales_order_no: props.orderNo, page_size: 100 })
    receivables.value = res?.items || []
  } catch (e) {
    console.error('加载关联收款单失败:', e)
  }
}

const loadCostItems = async () => {
  if (!props.orderNo) return
  try {
    const res = await salesOrderApi.getCostItems(props.orderNo)
    costItems.value = res?.items || []
  } catch (e) {
    console.error('加载成本明细失败:', e)
    costItems.value = []
  }
}

// ============ 状态操作 ============
const handleSubmit = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.submit(order.value.order_no)
    window.showToast('订单已提交审核', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '提交失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleAudit = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.approve(order.value.order_no)
    window.showToast('订单审核成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleReject = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.reject(order.value.order_no)
    window.showToast('订单已驳回', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleCancel = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.cancel(order.value.order_no)
    window.showToast('订单取消成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '取消失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

// ============ 业务操作 ============

const handlePushPurchase = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    const fullOrder = await salesOrderApi.getByOrderNo(order.value.order_no)
    const items = fullOrder.items || []

    // 批量获取品牌的采购人信息
    const uniqueBrandIds = [...new Set(items.map((item: any) => item.brand_id).filter(Boolean))] as string[]
    const purchaserMap: Record<string, { purchaser_id: string; purchaser_name: string }> = {}

    if (uniqueBrandIds.length > 0) {
      try {
        const purchaserRes = await brandApi.batchGetPurchasers(uniqueBrandIds)
        Object.assign(purchaserMap, purchaserRes.result || {})
      } catch {}
    }

    const enrichedItems = items.map((item: any) => ({
      ...item,
      purchaser_name: item.brand_id && purchaserMap[item.brand_id]
        ? purchaserMap[item.brand_id].purchaser_name
        : ''
    }))

    pushableItems.value = enrichedItems
    showPushItemSelect.value = true
  } catch (error: any) {
    window.showToast(error.message || '加载商品数据失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleSubmitPushPurchase = async (selectedRowNos: number[]) => {
  if (!order.value) return
  actionLoading.value = true
  try {
    const items = selectedRowNos.map(row_no => ({ row_no }))
    const result = await salesOrderApi.pushToPurchase(order.value.order_no, items)
    const count = result?.purchase_orders?.length || 0
    window.showToast(`下推采购成功，共生成${count}张采购单`, 'success')
    showPushItemSelect.value = false
    pushableItems.value = []
    await loadOrder()
    await loadPurchaseOrders()
  } catch (error: any) {
    window.showToast(error.message || '下推采购失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleClosePushItemSelect = () => {
  showPushItemSelect.value = false
  pushableItems.value = []
}

const handleClose = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    // 使用 cancel 接口关闭订单（后端会根据状态判断）
    await salesOrderApi.cancel(order.value.order_no)
    window.showToast('订单关闭成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '关闭失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleBack = () => {
  emit('back')
}

const navigateToPurchaseOrder = () => {
  emit('navigate', 'purchase-order')
}

// ============ 工具函数 ============
const getStatusLabel = (map: Record<string, { label: string; class: string }>, value: string) => {
  return map[value]?.label || value
}

const getStatusClass = (map: Record<string, { label: string; class: string }>, value: string) => {
  return map[value]?.class || ''
}

const getFlowFieldName = (field: string) => {
  const map: Record<string, string> = {
    order_status: '订单状态', delivery_status: '发货状态',
    receive_status: '收货状态', invoice_status: '开票状态'
  }
  return map[field] || field
}

// ============ 初始化 ============
onMounted(() => { loadOrder() })
onActivated(() => { loadOrder() })
watch(() => props.orderNo, () => { if (props.orderNo) loadOrder() })
</script>

<template>
  <div class="sales-order-detail">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else-if="order">
      <!-- 顶部栏 -->
      <div class="detail-header">
        <div class="header-left">
          <button class="back-btn" @click="handleBack">
            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
              <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
            </svg>
            返回
          </button>
          <h2 class="order-title">{{ order.order_no }}</h2>
          <span class="status-tag" :class="getStatusClass(orderStatusMap, order.order_status)">
            {{ getStatusLabel(orderStatusMap, order.order_status) }}
          </span>
        </div>
        <div class="header-actions">
          <button v-if="order.order_status === 'draft'" class="btn-primary" @click="handleSubmit" :disabled="actionLoading">提交审核</button>
          <!-- 兼容历史数据：pending 状态显示审核通过和驳回按钮 -->
          <button v-if="order.order_status === 'pending'" class="btn-primary" @click="handleAudit" :disabled="actionLoading">审核通过</button>
          <button v-if="order.order_status === 'pending'" class="btn-warning" @click="handleReject" :disabled="actionLoading">驳回</button>
          <button v-if="canPushPurchase" class="btn-primary" @click="handlePushPurchase" :disabled="actionLoading">下推采购</button>
          <!-- 取消订单仅限草稿状态 -->
          <button v-if="order.order_status === 'draft'" class="btn-danger" @click="handleCancel" :disabled="actionLoading">取消订单</button>
          <!-- 测试修改状态按钮 -->
          <button class="btn-secondary" @click="openTestStatusModal" :disabled="actionLoading">测试修改状态</button>
        </div>
      </div>

      <!-- 基本信息 + 状态进度 + 金额信息 -->
      <div class="top-section">
        <!-- 基本信息横向布局 -->
        <div class="section-card">
          <div class="info-row">
            <div class="info-item-inline">
              <label>客户</label>
              <span>{{ order.customer_name || order.customer_id || '-' }}</span>
            </div>
            <div class="info-item-inline">
              <label>销售员</label>
              <span>{{ order.sale_user_name || order.sale_user_id || '-' }}</span>
            </div>
            <div class="info-item-inline">
              <label>订单日期</label>
              <span>{{ order.order_date || '-' }}</span>
            </div>
            <div class="info-item-inline">
              <label>结算方式</label>
              <span>{{ order.settle_type || '-' }}</span>
            </div>
            <div class="info-item-inline">
              <label>期望交货日</label>
              <span>{{ order.expect_deliver_date || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 状态卡片网格 -->
        <div class="section-card">
          <h3 class="section-title">状态信息</h3>
          <div class="status-cards">
            <div class="status-card">
              <div class="status-card-label">订单状态</div>
              <span class="status-tag" :class="getStatusClass(orderStatusMap, order.order_status)">
                {{ getStatusLabel(orderStatusMap, order.order_status) }}
              </span>
            </div>
            <div class="status-card">
              <div class="status-card-label">发货状态</div>
              <span class="status-tag" :class="getStatusClass(deliveryStatusMap, order.delivery_status)">
                {{ getStatusLabel(deliveryStatusMap, order.delivery_status) }}
              </span>
            </div>
            <div class="status-card">
              <div class="status-card-label">收货状态</div>
              <span class="status-tag" :class="getStatusClass(receiveStatusMap, order.receive_status)">
                {{ getStatusLabel(receiveStatusMap, order.receive_status) }}
              </span>
            </div>
            <div class="status-card">
              <div class="status-card-label">开票状态</div>
              <span class="status-tag" :class="getStatusClass(invoiceStatusMap, order.invoice_status)">
                {{ getStatusLabel(invoiceStatusMap, order.invoice_status) }}
              </span>
            </div>
            <div class="status-card">
              <div class="status-card-label">财务状态</div>
              <span class="status-tag" :class="getStatusClass(financeStatusMap, order.finance_status)">
                {{ getStatusLabel(financeStatusMap, order.finance_status) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 金额信息 -->
        <div class="section-card">
          <h3 class="section-title">金额信息</h3>
          <div class="amount-grid">
            <div class="amount-item">
              <span class="amount-label">不含税总额</span>
              <span class="amount-value">¥{{ order.total_amt?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="amount-item">
              <span class="amount-label">税额</span>
              <span class="amount-value">¥{{ order.tax_amt?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="amount-item highlight">
              <span class="amount-label">含税总额</span>
              <span class="amount-value">¥{{ order.total_tax_amt?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="amount-item">
              <span class="amount-label">成本合计</span>
              <span class="amount-value">¥{{ totalCostAmount.toFixed(2) }}</span>
            </div>
            <div class="amount-item" :class="{ profit: estimatedProfit > 0, loss: estimatedProfit < 0 }">
              <span class="amount-label">预估利润</span>
              <span class="amount-value">¥{{ estimatedProfit.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 发货信息 + 开票信息 双栏 -->
      <div class="two-col-row" v-if="order.deliver_info || order.invoice_info">
        <div class="col-left" v-if="order.deliver_info">
          <div class="section-card">
            <h3 class="section-title">发货信息</h3>
            <div class="info-inline">
              <span class="info-tag"><strong>收货人:</strong> {{ order.deliver_info.person_name || '-' }}</span>
              <span class="info-tag"><strong>电话:</strong> {{ order.deliver_info.person_tel || '-' }}</span>
              <span class="info-tag"><strong>地址:</strong> {{ [order.deliver_info.province, order.deliver_info.city, order.deliver_info.addr].filter(Boolean).join(' ') || '-' }}</span>
            </div>
          </div>
        </div>
        <div class="col-right" v-if="order.invoice_info">
          <div class="section-card">
            <h3 class="section-title">开票信息</h3>
            <div class="info-inline">
              <span class="info-tag"><strong>抬头:</strong> {{ order.invoice_info.invoice_title || '-' }}</span>
              <span class="info-tag"><strong>税号:</strong> {{ order.invoice_info.tax_number || '-' }}</span>
              <span class="info-tag"><strong>开户行:</strong> {{ order.invoice_info.bank_name || '-' }}</span>
              <span class="info-tag"><strong>账号:</strong> {{ order.invoice_info.bank_account || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 备注 -->
      <div class="section-card" v-if="order.remark">
        <h3 class="section-title">备注</h3>
        <p class="remarks-text">{{ order.remark }}</p>
      </div>

      <!-- 主 Tab 区域 -->
      <div class="section-card">
        <div class="main-tabs">
          <button
            class="tab-btn"
            :class="{ active: activeMainTab === 'items' }"
            @click="activeMainTab = 'items'"
          >
            商品明细 <span class="tab-count">({{ order.items?.length || 0 }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeMainTab === 'purchase' }"
            @click="activeMainTab = 'purchase'"
          >
            采购单 <span class="tab-count">({{ purchaseOrders.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeMainTab === 'receivable' }"
            @click="activeMainTab = 'receivable'"
          >
            收款单 <span class="tab-count">({{ receivables.length }})</span>
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeMainTab === 'cost' }"
            @click="activeMainTab = 'cost'"
          >
            成本明细 <span class="tab-count">({{ costItems.length }})</span>
          </button>
        </div>

        <!-- 商品明细 Tab -->
        <div v-if="activeMainTab === 'items'">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>行号</th>
                  <th>商品</th>
                  <th>品牌</th>
                  <th>规格</th>
                  <th>仓库</th>
                  <th class="col-num">数量</th>
                  <th class="col-num">库存</th>
                  <th>库存状态</th>
                  <th class="col-num">单价</th>
                  <th class="col-num">金额</th>
                  <th>发货方式</th>
                  <th>下推状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in order.items" :key="item.row_no" :class="{ 'row-pushed': item.pushed }">
                  <td>{{ item.row_no }}</td>
                  <td>{{ item.product_name || item.product_id }}</td>
                  <td>{{ item.brand_name || '-' }}</td>
                  <td>{{ item.spec_code || '-' }}</td>
                  <td>{{ item.shipping_method === '直运' ? '--' : (item.warehouse_name || '-') }}</td>
                  <td class="col-num">{{ item.qty }}</td>
                  <td class="col-num">{{ item.stock_quantity ?? '-' }}</td>
                  <td>
                    <span v-if="item.stock_status" class="status-tag" :class="getStatusClass(stockStatusMap, item.stock_status)">
                      {{ getStatusLabel(stockStatusMap, item.stock_status) }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </td>
                  <td class="col-num">{{ item.price?.toFixed(2) }}</td>
                  <td class="col-num">{{ item.amt?.toFixed(2) }}</td>
                  <td>{{ item.shipping_method }}</td>
                  <td>
                    <span v-if="item.shipping_method !== '直运' && (item.stock_quantity ?? 0) >= item.qty" class="status-tag stock-sufficient">库存发货，无需采购</span>
                    <span v-else-if="item.pushed" class="status-tag pushed">已下推</span>
                    <span v-else class="status-tag pending">待下推</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 采购单 Tab -->
        <div v-if="activeMainTab === 'purchase'">
          <div v-if="purchaseOrders.length === 0" class="empty-state">暂无关联采购单</div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>采购单号</th>
                  <th>采购类型</th>
                  <th>品牌</th>
                  <th>供应商</th>
                  <th class="col-num">含税总额</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="po in purchaseOrders" :key="po.purchase_no">
                  <td><span class="order-link" @click="navigateToPurchaseOrder">{{ po.purchase_no }}</span></td>
                  <td>{{ po.purchase_type === 'direct' ? '直运采购' : '仓库采购' }}</td>
                  <td>{{ po.brand_name || '-' }}</td>
                  <td>{{ po.supplier_name || '-' }}</td>
                  <td class="col-num">{{ po.total_tax_amt?.toFixed(2) }}</td>
                  <td><span class="status-tag" :class="getStatusClass(purchaseStatusMap, po.status?.purchase_status)">{{ getStatusLabel(purchaseStatusMap, po.status?.purchase_status) }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 收款单 Tab -->
        <div v-if="activeMainTab === 'receivable'">
          <div v-if="receivables.length === 0" class="empty-state">暂无关联收款单</div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>收款单号</th>
                  <th>客户</th>
                  <th class="col-num">应收金额</th>
                  <th class="col-num">已收金额</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in receivables" :key="r.id">
                  <td>{{ r.receivable_no }}</td>
                  <td>{{ r.customer_name || '-' }}</td>
                  <td class="col-num">{{ r.total_amount?.toFixed(2) }}</td>
                  <td class="col-num">{{ r.paid_amount?.toFixed(2) }}</td>
                  <td><span class="status-tag" :class="getStatusClass(receivableStatusMap, r.status)">{{ getStatusLabel(receivableStatusMap, r.status) }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 成本明细 Tab -->
        <div v-if="activeMainTab === 'cost'">
          <div v-if="costItems.length === 0" class="empty-state">暂无成本明细，采购单审核后自动生成</div>
          <template v-else>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>成本类型</th>
                    <th class="col-num">金额</th>
                    <th>来源</th>
                    <th>来源单号</th>
                    <th>备注</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in costItems" :key="item.id">
                    <td>{{ costTypeMap[item.cost_type] || item.cost_type }}</td>
                    <td class="col-num">¥{{ item.amount?.toFixed(2) }}</td>
                    <td>{{ sourceTypeMap[item.source_type] || item.source_type }}</td>
                    <td>{{ item.source_no || '-' }}</td>
                    <td>{{ item.remark || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="cost-summary">
              <span class="cost-summary-label">成本合计</span>
              <span class="cost-summary-value">¥{{ totalCostAmount.toFixed(2) }}</span>
            </div>
          </template>
        </div>
      </div>

      <!-- 状态流转记录（可折叠） -->
      <div class="section-card collapsible-section" v-if="flows.length > 0">
        <div class="section-header" @click="flowExpanded = !flowExpanded">
          <h3 class="section-title">
            <svg class="collapse-icon" :class="{ expanded: flowExpanded }" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
              <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
            </svg>
            状态流转记录
            <span class="record-count">({{ flows.length }})</span>
          </h3>
        </div>
        <div class="collapsible-content" v-show="flowExpanded">
          <div class="flow-timeline">
            <div v-for="flow in flows" :key="flow.id" class="flow-item">
              <div class="flow-dot"></div>
              <div class="flow-content">
                <div class="flow-time">{{ flow.operate_time }}</div>
                <div class="flow-desc">
                  <span class="flow-field">{{ getFlowFieldName(flow.field) }}</span>
                  <span v-if="flow.old_value" class="flow-old">{{ flow.old_value }}</span>
                  <span v-if="flow.old_value" class="flow-arrow">→</span>
                  <span class="flow-new">{{ flow.new_value }}</span>
                </div>
                <div class="flow-operator">操作人: {{ flow.operator }}</div>
                <div v-if="flow.remark" class="flow-remark">{{ flow.remark }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="section-card" v-else>
        <h3 class="section-title">状态流转记录</h3>
        <div class="empty-state">暂无流转记录</div>
      </div>
    </template>

    <PushPurchaseItemSelectModal
      :visible="showPushItemSelect"
      :items="pushableItems"
      @close="handleClosePushItemSelect"
      @submit="handleSubmitPushPurchase"
    />

    <!-- 测试状态修改弹窗 -->
    <div class="modal-overlay" v-if="showTestStatusModal">
      <div class="modal" style="width: 400px;">
        <div class="modal-header">
          <h3>测试修改状态</h3>
          <button class="modal-close" @click="showTestStatusModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <p style="color: #e67e22; margin-bottom: 16px; font-size: 12px;">
            注意：此功能仅用于测试自动完成机制，后续版本删除。
          </p>
          <div class="form-group" style="margin-bottom: 12px;">
            <label>发货状态</label>
            <select v-model="testStatusForm.delivery_status" class="form-select">
              <option v-for="opt in deliveryStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom: 12px;">
            <label>收货状态</label>
            <select v-model="testStatusForm.receive_status" class="form-select">
              <option v-for="opt in receiveStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom: 12px;">
            <label>财务状态</label>
            <select v-model="testStatusForm.finance_status" class="form-select">
              <option v-for="opt in financeStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom: 12px;">
            <label>开票状态</label>
            <select v-model="testStatusForm.invoice_status" class="form-select">
              <option v-for="opt in invoiceStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showTestStatusModal = false">取消</button>
          <button class="btn-primary" @click="handleTestUpdateStatus" :disabled="testStatusLoading">
            {{ testStatusLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sales-order-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
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

/* 顶部栏 */
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.order-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 顶部区域 */
.top-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

/* 基本信息横向布局 */
.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.info-item-inline {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 120px;
}

.info-item-inline label {
  font-size: 12px;
  color: var(--text-muted);
}

.info-item-inline span {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

/* 状态卡片网格 */
.status-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.status-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  min-width: 100px;
  flex: 1;
}

.status-card-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* 金额网格 */
.amount-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.amount-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 100px;
}

.amount-item .amount-label {
  font-size: 12px;
  color: var(--text-muted);
}

.amount-item .amount-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.amount-item.highlight .amount-value {
  color: var(--accent-blue);
  font-size: 17px;
}

.amount-item.profit .amount-value {
  color: var(--accent-green);
}

.amount-item.loss .amount-value {
  color: var(--accent-red);
}

/* 双栏布局 */
.two-col-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.col-left, .col-right {
  min-width: 0;
}

/* 区块卡片 */
.section-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-card);
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 14px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.info-item label {
  font-size: 12px;
  color: var(--text-muted);
}

.info-item span {
  font-size: 14px;
  color: var(--text-primary);
}

/* 信息行内 */
.info-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.info-tag {
  font-size: 13px;
  color: var(--text-primary);
}

.info-tag strong {
  color: var(--text-secondary);
  margin-right: 4px;
}

/* 状态列表 */
.status-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-row label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 70px;
}

.status-control {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.status-select {
  padding: 5px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
}

.status-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.audited { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.partial-pushed { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.status-tag.pushed { background-color: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.status-tag.closed { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.none { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.reconciled { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.pending { background-color: rgba(255, 152, 0, 0.1); color: #ff9800; }
.status-tag.stock-sufficient { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.stock-normal { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.stock-low { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.stock-out { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.stock-over { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }

.text-muted { color: var(--text-muted); font-size: 13px; }

/* 表格 */
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
  padding: 9px 12px;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.data-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.data-table tr.row-pushed td {
  opacity: 0.55;
}

.col-num {
  text-align: right;
  white-space: nowrap;
}

.order-link {
  color: var(--accent-blue);
  cursor: pointer;
  text-decoration: none;
}

.order-link:hover {
  text-decoration: underline;
}

/* 金额列表 */
.amount-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.amount-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.amount-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.amount-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.amount-row.highlight .amount-value {
  color: var(--accent-blue);
  font-size: 17px;
}

/* 备注 */
.remarks-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0;
}

/* Tab 切换 */
.related-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  padding: 8px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.tab-count {
  margin-left: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

/* 主 Tab */
.main-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
}

/* 成本汇总 */
.cost-summary {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  margin-top: 12px;
}

.cost-summary-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.cost-summary-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-blue);
}

/* 空状态 */
.empty-state {
  padding: 28px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

/* 流转时间线 */
.flow-timeline {
  position: relative;
  padding-left: 24px;
}

.flow-timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: var(--border-color);
}

.flow-item {
  position: relative;
  padding-bottom: 18px;
}

.flow-item:last-child { padding-bottom: 0; }

.flow-dot {
  position: absolute;
  left: -20px;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--accent-blue);
  border: 2px solid var(--bg-card);
}

.flow-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.flow-time { font-size: 12px; color: var(--text-muted); }
.flow-desc { font-size: 13px; color: var(--text-primary); }
.flow-field { font-weight: 500; margin-right: 8px; }
.flow-old { color: var(--text-muted); text-decoration: line-through; margin-right: 4px; }
.flow-arrow { color: var(--text-muted); margin-right: 4px; }
.flow-new { color: var(--accent-blue); font-weight: 500; }
.flow-operator { font-size: 12px; color: var(--text-muted); }
.flow-remark { font-size: 12px; color: var(--text-muted); font-style: italic; }

/* 折叠区块 */
.collapsible-section .section-header {
  cursor: pointer;
  user-select: none;
}

.collapsible-section .section-title {
  display: flex;
  align-items: center;
  gap: 4px;
}

.collapse-icon {
  transition: transform 0.2s ease;
  color: var(--text-muted);
}

.collapse-icon.expanded {
  transform: rotate(90deg);
}

.record-count {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: normal;
  margin-left: 4px;
}

.collapsible-content {
  padding-top: 14px;
}

/* 按钮 */
.btn-primary {
  padding: 8px 16px;
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

.btn-warning {
  padding: 8px 16px;
  background-color: #f59e0b;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-warning:hover { background-color: #d97706; }
.btn-warning:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-danger {
  padding: 8px 16px;
  background-color: var(--accent-red);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover { background-color: #dc2626; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 900px) {
  .two-col-row {
    grid-template-columns: 1fr;
  }
}
</style>
