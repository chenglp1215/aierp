<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { purchaseOrderApi } from '../../services/api'

interface Props {
  purchaseNo?: string
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
const actionLoading = ref(false)
const supplierOptions = ref<any[]>([])
const showLogisticsModal = ref(false) // 物流信息弹窗
const logisticsLoading = ref(false) // 物流信息提交加载状态

// 物流表单
const logisticsForm = ref({
  logistics_company: '',
  logistics_no: '',
  source_purchase_order_id: '',
  expect_arrive_date: ''
})

// ============ 状态映射 ============
const purchaseStatusMap: Record<string, { label: string; class: string }> = {
  pending_review: { label: '待审核', class: 'pending-review' },
  ready_purchase: { label: '准备采购', class: 'ready-purchase' },
  purchasing: { label: '采购中', class: 'purchasing' },
  completed: { label: '采购完成', class: 'completed' },
  closed: { label: '已关闭', class: 'closed' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const inStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未入库', class: 'none' },
  partial: { label: '部分入库', class: 'partial' },
  full: { label: '全部入库', class: 'full' }
}

const payStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未付款', class: 'none' },
  partial: { label: '部分付款', class: 'partial' },
  full: { label: '已结清', class: 'full' }
}

// ============ 计算属性 ============
const currentStatus = computed(() => order.value?.purchase_status)
const isPendingReview = computed(() => currentStatus.value === 'pending_review')
const isReadyPurchase = computed(() => currentStatus.value === 'ready_purchase')
const isPurchasing = computed(() => currentStatus.value === 'purchasing')
const isCompleted = computed(() => currentStatus.value === 'completed')
const canEditSupplier = computed(() => isPendingReview.value || isReadyPurchase.value)
const canEditLogistics = computed(() => isPendingReview.value || isReadyPurchase.value)

// ============ 数据加载 ============
const loadOrder = async () => {
  if (!props.purchaseNo) return
  loading.value = true
  try {
    const [orderRes, flowsRes] = await Promise.all([
      purchaseOrderApi.getByPurchaseNo(props.purchaseNo),
      purchaseOrderApi.getStatusFlows(props.purchaseNo)
    ])
    order.value = orderRes
    flows.value = flowsRes || []

    // 初始化物流表单
    logisticsForm.value = {
      logistics_company: order.value?.logistics_company || '',
      logistics_no: order.value?.logistics_no || '',
      source_purchase_order_id: order.value?.source_purchase_order_id || '',
      expect_arrive_date: order.value?.expect_arrive_date || ''
    }
  } catch (e) {
    console.error('加载采购单详情失败:', e)
  } finally {
    loading.value = false
  }
}

const loadSupplierOptions = async () => {
  if (!props.purchaseNo) return
  try {
    const res = await purchaseOrderApi.getAvailableSuppliers(props.purchaseNo)
    supplierOptions.value = res || []
  } catch (e) {
    console.error('加载供应商列表失败:', e)
    supplierOptions.value = []
  }
}

// ============ 业务操作 ============
const handleRecall = async () => {
  if (!order.value) return
  if (!confirm('确定要撤回该采购单吗？撤回后将删除采购单并更新销售单状态。')) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.recall(order.value.purchase_no)
    window.showToast('采购单撤回成功', 'success')
    emit('back')
  } catch (error: any) {
    window.showToast(error.message || '撤回失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleApprove = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await purchaseOrderApi.approve(order.value.purchase_no)
    window.showToast('采购单审核通过', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleStartPurchase = async () => {
  if (!order.value) return
  // 回显已有物流信息
  logisticsForm.value = {
    logistics_company: order.value.logistics_company || '',
    logistics_no: order.value.logistics_no || '',
    source_purchase_order_id: order.value.source_purchase_order_id || '',
    expect_arrive_date: order.value.expect_arrive_date || ''
  }
  showLogisticsModal.value = true
}

// 填写物流信息后开始采购
const handleStartPurchaseWithLogistics = async () => {
  if (!order.value) return
  logisticsLoading.value = true
  try {
    // 先更新物流信息
    await purchaseOrderApi.updateLogistics(order.value.purchase_no, {
      logistics_company: logisticsForm.value.logistics_company || undefined,
      logistics_no: logisticsForm.value.logistics_no || undefined,
      source_purchase_order_id: logisticsForm.value.source_purchase_order_id || undefined,
      expect_arrive_date: logisticsForm.value.expect_arrive_date || undefined
    })
    // 再执行开始采购
    await purchaseOrderApi.startPurchase(order.value.purchase_no)
    window.showToast('采购已开始', 'success')
    showLogisticsModal.value = false
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    logisticsLoading.value = false
  }
}

// 跳过物流信息直接开始采购
const handleStartPurchaseLater = async () => {
  if (!order.value) return
  logisticsLoading.value = true
  try {
    await purchaseOrderApi.startPurchase(order.value.purchase_no)
    window.showToast('采购已开始', 'success')
    showLogisticsModal.value = false
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    logisticsLoading.value = false
  }
}

const handleComplete = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await purchaseOrderApi.complete(order.value.purchase_no)
    window.showToast('采购完成', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleRollback = async () => {
  if (!order.value) return
  const targetStatus = isReadyPurchase.value ? '待审核' : '准备采购'
  if (!confirm(`确定要回退到${targetStatus}状态吗？`)) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.rollback(order.value.purchase_no)
    window.showToast('状态回退成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '回退失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleSupplierChange = async (supplierId: number) => {
  if (!order.value || !canEditSupplier.value) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.updateSupplier(order.value.purchase_no, supplierId)
    window.showToast('供应商更新成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
    await loadOrder()
  } finally {
    actionLoading.value = false
  }
}

const handleLogisticsSubmit = async () => {
  if (!order.value || !canEditLogistics.value) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.updateLogistics(order.value.purchase_no, logisticsForm.value)
    window.showToast('物流信息更新成功', 'success')
    await loadOrder()
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleBack = () => {
  emit('back')
}

const navigateToSalesOrder = () => {
  if (order.value?.source_sale_order_no) {
    emit('navigate', 'sales-order', { orderNo: order.value.source_sale_order_no })
  }
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
    purchase_status: '采购状态',
    in_status: '入库状态',
    pay_status: '付款状态'
  }
  return map[field] || field
}

const formatAmount = (amount: number | undefined) => {
  if (amount === undefined || amount === null) return '¥0.00'
  return `¥${amount.toFixed(2)}`
}

// ============ 初始化 ============
onMounted(() => { loadOrder(); loadSupplierOptions() })
onActivated(() => { loadOrder(); loadSupplierOptions() })
watch(() => props.purchaseNo, () => { if (props.purchaseNo) { loadOrder(); loadSupplierOptions() } })
</script>

<template>
  <div class="purchase-order-detail">
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
          <h2 class="order-title">{{ order.purchase_no }}</h2>
          <span class="status-tag" :class="getStatusClass(purchaseStatusMap, order.purchase_status)">
            {{ getStatusLabel(purchaseStatusMap, order.purchase_status) }}
          </span>
        </div>
        <div class="header-actions">
          <!-- 待审核状态操作 -->
          <template v-if="isPendingReview">
            <button class="btn-primary" @click="handleApprove" :disabled="actionLoading">审核通过</button>
            <button class="btn-danger" @click="handleRecall" :disabled="actionLoading">撤回</button>
          </template>
          <!-- 准备采购状态操作 -->
          <template v-else-if="isReadyPurchase">
            <button class="btn-primary" @click="handleStartPurchase" :disabled="actionLoading">开始采购</button>
            <button class="btn-warning" @click="handleRollback" :disabled="actionLoading">回退</button>
          </template>
          <!-- 采购中状态操作 -->
          <template v-else-if="isPurchasing">
            <button class="btn-primary" @click="handleComplete" :disabled="actionLoading">采购完成</button>
            <button class="btn-warning" @click="handleRollback" :disabled="actionLoading">回退</button>
          </template>
        </div>
      </div>

      <!-- 关联销售单信息 -->
      <div class="section-card" v-if="order.source_sales_order">
        <h3 class="section-title">关联销售单</h3>
        <div class="info-inline">
          <span class="info-tag">
            <strong>销售单号:</strong>
            <span class="order-link" @click="navigateToSalesOrder">{{ order.source_sales_order.order_no }}</span>
          </span>
          <span class="info-tag"><strong>客户:</strong> {{ order.source_sales_order.customer_name }}</span>
          <span class="info-tag"><strong>订单日期:</strong> {{ order.source_sales_order.order_date }}</span>
          <span class="info-tag"><strong>金额:</strong> {{ formatAmount(order.source_sales_order.total_amt) }}</span>
        </div>
      </div>

      <!-- 双栏：基本信息 + 状态信息 -->
      <div class="two-col-row">
        <div class="col-left">
          <div class="section-card">
            <h3 class="section-title">基本信息</h3>
            <div class="info-grid">
              <div class="info-item"><label>采购单号</label><span>{{ order.purchase_no }}</span></div>
              <div class="info-item"><label>采购类型</label><span>{{ order.purchase_type === 'direct' ? '直运采购' : '仓库采购' }}</span></div>
              <div class="info-item"><label>品牌</label><span>{{ order.brand_name || '-' }}</span></div>
              <div class="info-item">
                <label>供应商</label>
                <div v-if="canEditSupplier" class="search-select">
                  <select :value="order.supplier_id" @change="handleSupplierChange(Number(($event.target as HTMLSelectElement).value))" class="supplier-select">
                    <option value="0">请选择供应商</option>
                    <option v-for="supplier in supplierOptions" :key="supplier.id" :value="supplier.id">
                      {{ supplier.name }}
                      <template v-if="supplier.is_priority"> (优先)</template>
                      <template v-if="supplier.discount"> (折扣: {{ Math.round(supplier.discount * 100) }}%)</template>
                    </option>
                  </select>
                </div>
                <span v-else>{{ order.supplier_name || '-' }}</span>
              </div>
              <div class="info-item"><label>结算方式</label><span>{{ order.settle_type || '-' }}</span></div>
              <div class="info-item"><label>预计到货日</label><span>{{ order.expect_arrive_date || '-' }}</span></div>
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="section-card">
            <h3 class="section-title">状态信息</h3>
            <div class="status-list">
              <div class="status-row">
                <label>采购状态</label>
                <span class="status-tag" :class="getStatusClass(purchaseStatusMap, order.purchase_status)">
                  {{ getStatusLabel(purchaseStatusMap, order.purchase_status) }}
                </span>
              </div>
              <div class="status-row">
                <label>入库状态</label>
                <span class="status-tag" :class="getStatusClass(inStatusMap, order.in_status)">
                  {{ getStatusLabel(inStatusMap, order.in_status) }}
                </span>
              </div>
              <div class="status-row">
                <label>付款状态</label>
                <span class="status-tag" :class="getStatusClass(payStatusMap, order.pay_status)">
                  {{ getStatusLabel(payStatusMap, order.pay_status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 物流信息（准备采购状态可编辑） -->
      <div class="section-card" v-if="isReadyPurchase || order.logistics_company || order.logistics_no || order.source_purchase_order_id">
        <h3 class="section-title">物流信息</h3>
        <div class="logistics-form" v-if="canEditLogistics">
          <div class="form-row">
            <div class="form-item">
              <label>物流公司</label>
              <input type="text" v-model="logisticsForm.logistics_company" placeholder="请输入物流公司" />
            </div>
            <div class="form-item">
              <label>物流单号</label>
              <input type="text" v-model="logisticsForm.logistics_no" placeholder="请输入物流单号" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-item">
              <label>采购源订单ID</label>
              <input type="text" v-model="logisticsForm.source_purchase_order_id" placeholder="如1688订单号" />
            </div>
            <div class="form-item">
              <label>预计到货日期</label>
              <input type="date" v-model="logisticsForm.expect_arrive_date" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-primary" @click="handleLogisticsSubmit" :disabled="actionLoading">保存物流信息</button>
          </div>
        </div>
        <div class="info-inline" v-else>
          <span class="info-tag" v-if="order.logistics_company"><strong>物流公司:</strong> {{ order.logistics_company }}</span>
          <span class="info-tag" v-if="order.logistics_no"><strong>物流单号:</strong> {{ order.logistics_no }}</span>
          <span class="info-tag" v-if="order.source_purchase_order_id"><strong>源订单ID:</strong> {{ order.source_purchase_order_id }}</span>
          <span class="info-tag" v-if="order.expect_arrive_date"><strong>预计到货:</strong> {{ order.expect_arrive_date }}</span>
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
                <th class="col-num">采购数量</th>
                <th class="col-num">已入库</th>
                <th class="col-num">采购单价</th>
                <th class="col-num">折扣</th>
                <th class="col-num">金额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in order.items" :key="item.row_no">
                <td>{{ item.row_no }}</td>
                <td>{{ item.product_name || item.product_id }}</td>
                <td>{{ item.brand_name || '-' }}</td>
                <td>{{ item.spec_code || '-' }}</td>
                <td class="col-num">{{ item.purchase_qty }}</td>
                <td class="col-num">{{ item.in_qty }}</td>
                <td class="col-num">{{ item.purchase_price?.toFixed(2) }}</td>
                <td class="col-num">{{ ((item.discount || 1) * 100).toFixed(0) }}%</td>
                <td class="col-num">{{ item.amt?.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 金额信息 -->
      <div class="section-card">
        <h3 class="section-title">金额信息</h3>
        <div class="amount-list">
          <div class="amount-row">
            <span class="amount-label">商品总金额</span>
            <span class="amount-value">{{ formatAmount(order.total_amt) }}</span>
          </div>
          <div class="amount-row">
            <span class="amount-label">运费</span>
            <span class="amount-value">{{ formatAmount(order.freight_amt) }}</span>
          </div>
          <div class="amount-row">
            <span class="amount-label">税额</span>
            <span class="amount-value">{{ formatAmount(order.tax_amt) }}</span>
          </div>
          <div class="amount-row highlight">
            <span class="amount-label">含税合计</span>
            <span class="amount-value">{{ formatAmount(order.total_tax_amt) }}</span>
          </div>
        </div>
      </div>

      <!-- 备注 -->
      <div class="section-card" v-if="order.remark">
        <h3 class="section-title">备注</h3>
        <p class="remarks-text">{{ order.remark }}</p>
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

    <!-- 物流信息弹窗 -->
    <div class="modal-overlay" v-if="showLogisticsModal">
      <div class="modal logistics-modal">
        <div class="modal-header">
          <h3>开始采购 - 物流信息</h3>
          <button class="modal-close" @click="showLogisticsModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <p class="text-muted mb-3">采购单号: <strong>{{ order?.purchase_no }}</strong></p>
          <div class="form-row">
            <div class="form-group">
              <label>物流公司</label>
              <input v-model="logisticsForm.logistics_company" placeholder="请输入物流公司" />
            </div>
            <div class="form-group">
              <label>物流单号</label>
              <input v-model="logisticsForm.logistics_no" placeholder="请输入物流单号" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>采购源订单ID</label>
              <input v-model="logisticsForm.source_purchase_order_id" placeholder="如1688订单号" />
            </div>
            <div class="form-group">
              <label>预计到货日期</label>
              <input v-model="logisticsForm.expect_arrive_date" type="date" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="handleStartPurchaseLater" :disabled="logisticsLoading">
            {{ logisticsLoading ? '处理中...' : '后续填写' }}
          </button>
          <button class="btn-primary" @click="handleStartPurchaseWithLogistics" :disabled="logisticsLoading">
            {{ logisticsLoading ? '处理中...' : '开始采购' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.purchase-order-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--color-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-hairline);
  border-top-color: var(--color-interactive);
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
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-canvas);
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
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.order-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
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
  background: var(--color-canvas);
  border: 1px solid var(--color-card-border);
  border-radius: var(--radius-sm);
  padding: var(--space-xl);
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 14px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-hairline);
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
  color: var(--color-muted);
}

.info-item span {
  font-size: 14px;
  color: var(--color-ink);
}

/* 信息行内 */
.info-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.info-tag {
  font-size: 13px;
  color: var(--color-ink);
}

.info-tag strong {
  color: var(--color-muted);
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
  color: var(--color-muted);
  min-width: 70px;
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.status-tag.pending-review { background-color: var(--color-neutral-bg); color: var(--color-body-muted); }
.status-tag.ready-purchase { background-color: var(--color-info-bg); color: var(--color-interactive); }
.status-tag.purchasing { background-color: var(--color-warning-bg); color: #92400e; }
.status-tag.completed { background-color: var(--color-success-bg); color: var(--color-success); }
.status-tag.closed { background-color: var(--color-success-bg); color: var(--color-success); }
.status-tag.cancelled { background-color: var(--color-danger-bg); color: var(--color-danger); }
.status-tag.none { background-color: var(--color-neutral-bg); color: var(--color-body-muted); }
.status-tag.partial { background-color: var(--color-warning-bg); color: #92400e; }
.status-tag.full { background-color: var(--color-success-bg); color: var(--color-success); }

/* 物流表单 */
.logistics-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-item label {
  font-size: 12px;
  color: var(--color-muted);
}

.form-item input {
  padding: 8px 10px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.form-item input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

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
  background-color: var(--color-neutral-bg);
  color: var(--color-muted);
  font-weight: 500;
  border-bottom: 1px solid var(--color-hairline);
  white-space: nowrap;
}

.data-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}

.col-num {
  text-align: right;
  white-space: nowrap;
}

.order-link {
  color: var(--color-interactive);
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
  color: var(--color-muted);
}

.amount-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.amount-row.highlight .amount-value {
  color: var(--color-interactive);
  font-size: 17px;
}

/* 供应商选择 */
.supplier-select {
  width: 100%;
  padding: 6px 10px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
  cursor: pointer;
}

.supplier-select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

/* 备注 */
.remarks-text {
  font-size: 13px;
  color: var(--color-ink);
  line-height: 1.6;
  margin: 0;
}

/* 空状态 */
.empty-state {
  padding: 28px;
  text-align: center;
  color: var(--color-muted);
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
  background-color: var(--color-hairline);
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
  background-color: var(--color-interactive);
  border: 2px solid var(--color-canvas);
}

.flow-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.flow-time { font-size: 12px; color: var(--color-muted); }
.flow-desc { font-size: 13px; color: var(--color-ink); }
.flow-field { font-weight: 500; margin-right: 8px; }
.flow-old { color: var(--color-muted); text-decoration: line-through; margin-right: 4px; }
.flow-arrow { color: var(--color-muted); margin-right: 4px; }
.flow-new { color: var(--color-interactive); font-weight: 500; }
.flow-operator { font-size: 12px; color: var(--color-muted); }
.flow-remark { font-size: 12px; color: var(--color-muted); font-style: italic; }

/* 按钮 */
.btn-primary {
  padding: 8px 16px;
  background-color: var(--color-interactive);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover { background-color: var(--color-interactive-hover); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-warning {
  padding: 8px 16px;
  background-color: var(--color-warning);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-warning:hover { background-color: var(--color-warning); filter: brightness(1.15); }
.btn-warning:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-danger {
  padding: 8px 16px;
  background-color: var(--color-danger);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover { background-color: var(--color-danger); filter: brightness(1.15); }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

/* ============ 物流信息弹窗 ============ */

.logistics-modal {
  width: 520px;
  max-width: 90vw;
}

.logistics-modal .modal-body {
  padding: 20px;
}

.logistics-modal .mb-3 {
  margin-bottom: 16px;
}

.logistics-modal .form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.logistics-modal .form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.logistics-modal .form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
}

.logistics-modal .form-group input {
  padding: 8px 12px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background-color: var(--color-canvas);
  color: var(--color-ink);
  transition: border-color 0.2s;
}

.logistics-modal .form-group input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.logistics-modal .modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-hairline);
}

@media (max-width: 900px) {
  .two-col-row, .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
