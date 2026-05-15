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
const activeRelatedTab = ref<'purchase' | 'receivable'>('purchase')

// ============ 状态映射 ============
const orderStatusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待审核', class: 'pending' },
  audited: { label: '已审核', class: 'audited' },
  partially_pushed_to_purchase: { label: '部分下推采购', class: 'partial-pushed' },
  pushed_to_purchase: { label: '已下推采购', class: 'pushed' },
  closed: { label: '已关闭', class: 'closed' },
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

// ============ 计算属性 ============
const canPushPurchase = computed(() => {
  const s = order.value?.status?.order_status
  return s === 'audited' || s === 'partially_pushed_to_purchase'
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
    await Promise.all([loadPurchaseOrders(), loadReceivables()])
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
          <button v-if="order.order_status === 'pending'" class="btn-primary" @click="handleAudit" :disabled="actionLoading">审核通过</button>
          <button v-if="order.order_status === 'pending'" class="btn-warning" @click="handleReject" :disabled="actionLoading">驳回</button>
          <button v-if="canPushPurchase" class="btn-primary" @click="handlePushPurchase" :disabled="actionLoading">下推采购</button>
          <button v-if="order.order_status === 'audited'" class="btn-warning" @click="handleClose" :disabled="actionLoading">关闭订单</button>
          <button v-if="order.order_status === 'draft' || order.order_status === 'pending' || order.order_status === 'audited'" class="btn-danger" @click="handleCancel" :disabled="actionLoading">取消订单</button>
        </div>
      </div>

      <!-- 双栏：基本信息 + 状态信息 -->
      <div class="two-col-row">
        <div class="col-left">
          <div class="section-card">
            <h3 class="section-title">基本信息</h3>
            <div class="info-grid">
              <div class="info-item"><label>订单编号</label><span>{{ order.order_no }}</span></div>
              <div class="info-item"><label>订单日期</label><span>{{ order.order_date }}</span></div>
              <div class="info-item"><label>客户</label><span>{{ order.customer_name || order.customer_id }}</span></div>
              <div class="info-item"><label>销售员</label><span>{{ order.sale_user_name || order.sale_user_id || '-' }}</span></div>
              <div class="info-item"><label>结算方式</label><span>{{ order.settle_type }}</span></div>
              <div class="info-item"><label>期望交货日</label><span>{{ order.expect_deliver_date || '-' }}</span></div>
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="section-card">
            <h3 class="section-title">状态信息</h3>
            <div class="status-list">
              <div class="status-row">
                <label>订单状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(orderStatusMap, order.order_status)">{{ getStatusLabel(orderStatusMap, order.order_status) }}</span>
                </div>
              </div>
              <div class="status-row">
                <label>发货状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(deliveryStatusMap, order.delivery_status)">{{ getStatusLabel(deliveryStatusMap, order.delivery_status) }}</span>
                </div>
              </div>
              <div class="status-row">
                <label>收货状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(receiveStatusMap, order.receive_status)">{{ getStatusLabel(receiveStatusMap, order.receive_status) }}</span>
                </div>
              </div>
              <div class="status-row">
                <label>开票状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(invoiceStatusMap, order.invoice_status)">{{ getStatusLabel(invoiceStatusMap, order.invoice_status) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 发货信息 -->
      <div class="section-card" v-if="order.deliver_info">
        <h3 class="section-title">发货信息</h3>
        <div class="info-inline">
          <span class="info-tag"><strong>收货人:</strong> {{ order.deliver_info.person_name || '-' }}</span>
          <span class="info-tag"><strong>电话:</strong> {{ order.deliver_info.person_tel || '-' }}</span>
          <span class="info-tag"><strong>地址:</strong> {{ [order.deliver_info.province, order.deliver_info.city, order.deliver_info.addr].filter(Boolean).join(' ') || '-' }}</span>
        </div>
      </div>

      <!-- 开票信息 -->
      <div class="section-card" v-if="order.invoice_info">
        <h3 class="section-title">开票信息</h3>
        <div class="info-inline">
          <span class="info-tag"><strong>抬头:</strong> {{ order.invoice_info.invoice_title || '-' }}</span>
          <span class="info-tag"><strong>税号:</strong> {{ order.invoice_info.tax_number || '-' }}</span>
          <span class="info-tag"><strong>开户行:</strong> {{ order.invoice_info.bank_name || '-' }}</span>
          <span class="info-tag"><strong>账号:</strong> {{ order.invoice_info.bank_account || '-' }}</span>
        </div>
      </div>

      <!-- 商品明细 -->
      <div class="section-card">
        <h3 class="section-title">商品明细 ({{ order.items?.length || 0 }})</h3>
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

      <!-- 双栏：金额 + 备注 -->
      <div class="two-col-row">
        <div class="col-left">
          <div class="section-card">
            <h3 class="section-title">金额信息</h3>
            <div class="amount-list">
              <div class="amount-row">
                <span class="amount-label">不含税总额</span>
                <span class="amount-value">¥{{ order.total_amt?.toFixed(2) }}</span>
              </div>
              <div class="amount-row">
                <span class="amount-label">税额</span>
                <span class="amount-value">¥{{ order.tax_amt?.toFixed(2) }}</span>
              </div>
              <div class="amount-row highlight">
                <span class="amount-label">含税总额</span>
                <span class="amount-value">¥{{ order.total_tax_amt?.toFixed(2) }}</span>
              </div>
              <div class="amount-row" v-if="order.total_discount_amt">
                <span class="amount-label">整单折扣</span>
                <span class="amount-value">¥{{ order.total_discount_amt?.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="section-card" v-if="order.remark">
            <h3 class="section-title">备注</h3>
            <p class="remarks-text">{{ order.remark }}</p>
          </div>
        </div>
      </div>

      <!-- 关联单据 Tab -->
      <div class="section-card">
        <div class="related-tabs">
          <button class="tab-btn" :class="{ active: activeRelatedTab === 'purchase' }" @click="activeRelatedTab = 'purchase'">
            采购单 <span class="tab-count">{{ purchaseOrders.length }}</span>
          </button>
          <button class="tab-btn" :class="{ active: activeRelatedTab === 'receivable' }" @click="activeRelatedTab = 'receivable'">
            收款单 <span class="tab-count">{{ receivables.length }}</span>
          </button>
        </div>

        <div v-if="activeRelatedTab === 'purchase'">
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

        <div v-if="activeRelatedTab === 'receivable'">
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
      </div>

      <!-- 状态流转记录 -->
      <div class="section-card">
        <h3 class="section-title">状态流转记录</h3>
        <div v-if="flows.length === 0" class="empty-state">暂无流转记录</div>
        <div v-else class="flow-timeline">
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
    </template>

    <PushPurchaseItemSelectModal
      :visible="showPushItemSelect"
      :items="pushableItems"
      @close="handleClosePushItemSelect"
      @submit="handleSubmitPushPurchase"
    />
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
