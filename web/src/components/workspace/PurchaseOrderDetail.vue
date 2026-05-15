<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { purchaseOrderApi, supplierApi } from '../../services/api'

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

// ============ 状态映射 ============
const purchaseStatusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  audited: { label: '已审核', class: 'audited' },
  closed: { label: '已结案', class: 'closed' },
  cancelled: { label: '已作废', class: 'cancelled' }
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
const isDraft = computed(() => order.value?.status?.purchase_status === 'draft')
const isAudited = computed(() => order.value?.status?.purchase_status === 'audited')
const canEdit = computed(() => isDraft.value)

// ============ 数据加载 ============
const loadOrder = async () => {
  if (!props.purchaseNo) return
  loading.value = true
  try {
    const [orderRes, flowsRes] = await Promise.all([
      purchaseOrderApi.getByPurchaseNo(props.purchaseNo),
      purchaseOrderApi.getStatusFlows(props.purchaseNo)
    ])
    order.value = orderRes.result
    flows.value = flowsRes.result || []
  } catch (e) {
    console.error('加载采购单详情失败:', e)
  } finally {
    loading.value = false
  }
}

const loadSupplierOptions = async () => {
  if (!order.value?.brand_id) return
  try {
    const res = await supplierApi.getByBrandId(order.value.brand_id)
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
    order.value = { ...order.value, status: { ...order.value.status, purchase_status: 'audited' } }
    const flowsRes = await purchaseOrderApi.getStatusFlows(order.value.purchase_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleClose = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await purchaseOrderApi.close(order.value.purchase_no)
    window.showToast('采购单结案成功', 'success')
    order.value = { ...order.value, status: { ...order.value.status, purchase_status: 'closed' } }
    const flowsRes = await purchaseOrderApi.getStatusFlows(order.value.purchase_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '结案失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleReaudit = async () => {
  if (!order.value) return
  if (!confirm('确定要重审该采购单吗？重审后将撤回到草稿状态。')) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.reaudit(order.value.purchase_no)
    window.showToast('采购单重审成功', 'success')
    order.value = { ...order.value, status: { ...order.value.status, purchase_status: 'draft' } }
    const flowsRes = await purchaseOrderApi.getStatusFlows(order.value.purchase_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '重审失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleVoid = async () => {
  if (!order.value) return
  if (!confirm('确定要作废该采购单吗？')) return

  actionLoading.value = true
  try {
    await purchaseOrderApi.void(order.value.purchase_no)
    window.showToast('采购单作废成功', 'success')
    order.value = { ...order.value, status: { ...order.value.status, purchase_status: 'cancelled' } }
    const flowsRes = await purchaseOrderApi.getStatusFlows(order.value.purchase_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '作废失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handleSupplierChange = async (supplierId: string) => {
  if (!order.value || !canEdit.value) return

  const selectedSupplier = supplierOptions.value.find(s => s.id === supplierId)
  if (!selectedSupplier) return

  actionLoading.value = true
  try {
    // 更新供应商并重新计算商品价格
    const updateData = {
      supplier_id: supplierId,
      items: order.value.items.map((item: any) => {
        // 获取供应商对品牌的折扣率
        const discount = selectedSupplier.supplied_brands?.find((sb: any) => sb.brand_id === item.brand_id)?.discount || 1.0
        const newPrice = (item.purchase_price / (item.discount || 1.0)) * discount
        return {
          ...item,
          purchase_price: newPrice,
          discount: discount,
          amt: item.purchase_qty * newPrice
        }
      })
    }

    await purchaseOrderApi.update(order.value.purchase_no, updateData)
    window.showToast('供应商更新成功', 'success')

    // 重新加载订单数据
    const orderRes = await purchaseOrderApi.getByPurchaseNo(order.value.purchase_no)
    order.value = orderRes.result
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
    // 重新加载原始数据
    await loadOrder()
  } finally {
    actionLoading.value = false
  }
}

const handleFreightChange = async (event: Event) => {
  if (!order.value || !canEdit.value) return

  const newFreight = parseFloat((event.target as HTMLInputElement).value) || 0
  actionLoading.value = true
  try {
    await purchaseOrderApi.update(order.value.purchase_no, { freight_amt: newFreight })
    window.showToast('运费更新成功', 'success')
    order.value = { ...order.value, freight_amt: newFreight }
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
    await loadOrder()
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
onMounted(() => { loadOrder() })
onActivated(() => { loadOrder() })
watch(() => props.purchaseNo, () => { if (props.purchaseNo) loadOrder() })
watch(() => order.value?.brand_id, () => { if (order.value?.brand_id) loadSupplierOptions() })
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
          <span class="status-tag" :class="getStatusClass(purchaseStatusMap, order.status?.purchase_status)">
            {{ getStatusLabel(purchaseStatusMap, order.status?.purchase_status) }}
          </span>
        </div>
        <div class="header-actions">
          <!-- 草稿状态操作 -->
          <template v-if="isDraft">
            <button class="btn-primary" @click="handleApprove" :disabled="actionLoading">审核通过</button>
            <button class="btn-danger" @click="handleRecall" :disabled="actionLoading">撤回</button>
          </template>
          <!-- 已审核状态操作 -->
          <template v-else-if="isAudited">
            <button class="btn-primary" @click="handleClose" :disabled="actionLoading">结案</button>
            <button class="btn-warning" @click="handleReaudit" :disabled="actionLoading">重审</button>
            <button class="btn-danger" @click="handleRecall" :disabled="actionLoading">撤回</button>
            <button class="btn-danger-outline" @click="handleVoid" :disabled="actionLoading">作废</button>
          </template>
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
                <div v-if="canEdit" class="search-select">
                  <div class="search-input-wrapper">
                    <select :value="order.supplier_id" @change="handleSupplierChange(($event.target as HTMLSelectElement).value)" class="supplier-select">
                      <option value="">请选择供应商</option>
                      <option v-for="supplier in supplierOptions" :key="supplier.id" :value="supplier.id">
                        {{ supplier.name }}
                        <template v-if="supplier.supplied_brands">
                          (折扣: {{ (supplier.supplied_brands.find((sb: any) => sb.brand_id === order.brand_id)?.discount || 1) * 100 }}%)
                        </template>
                      </option>
                    </select>
                  </div>
                </div>
                <span v-else>{{ order.supplier_name || '-' }}</span>
              </div>
              <div class="info-item"><label>采购员</label><span>{{ order.purchase_user_id || '-' }}</span></div>
              <div class="info-item"><label>结算方式</label><span>{{ order.settle_type }}</span></div>
              <div class="info-item"><label>预计到货日</label><span>{{ order.expect_arrive_date || '-' }}</span></div>
              <div class="info-item" v-if="order.source_sale_order_no">
                <label>来源销售单</label>
                <span class="order-link" @click="navigateToSalesOrder">{{ order.source_sale_order_no }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="section-card">
            <h3 class="section-title">状态信息</h3>
            <div class="status-list">
              <div class="status-row">
                <label>采购状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(purchaseStatusMap, order.status?.purchase_status)">
                    {{ getStatusLabel(purchaseStatusMap, order.status?.purchase_status) }}
                  </span>
                </div>
              </div>
              <div class="status-row">
                <label>入库状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(inStatusMap, order.status?.in_status)">
                    {{ getStatusLabel(inStatusMap, order.status?.in_status) }}
                  </span>
                </div>
              </div>
              <div class="status-row">
                <label>付款状态</label>
                <div class="status-control">
                  <span class="status-tag" :class="getStatusClass(payStatusMap, order.status?.pay_status)">
                    {{ getStatusLabel(payStatusMap, order.status?.pay_status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 收货信息 -->
      <div class="section-card" v-if="order.receive_info">
        <h3 class="section-title">收货信息</h3>
        <div class="info-inline">
          <span class="info-tag" v-if="order.receive_info.type === 'customer'">
            <strong>类型:</strong> 直运发给客户
          </span>
          <span class="info-tag" v-else-if="order.receive_info.type === 'warehouse'">
            <strong>类型:</strong> 入库到仓库
          </span>
          <span class="info-tag" v-if="order.receive_info.warehouse_name">
            <strong>仓库:</strong> {{ order.receive_info.warehouse_name }}
          </span>
          <span class="info-tag" v-if="order.receive_info.contact_person">
            <strong>收货人:</strong> {{ order.receive_info.contact_person }}
          </span>
          <span class="info-tag" v-if="order.receive_info.contact_tel">
            <strong>电话:</strong> {{ order.receive_info.contact_tel }}
          </span>
          <span class="info-tag" v-if="order.receive_info.customer_addr">
            <strong>地址:</strong> {{ [order.receive_info.province, order.receive_info.city, order.receive_info.customer_addr].filter(Boolean).join(' ') }}
          </span>
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
                <th>发货方式</th>
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
                <td>{{ item.shipping_method }}</td>
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
                <span class="amount-label">商品总金额</span>
                <span class="amount-value">{{ formatAmount(order.total_amt) }}</span>
              </div>
              <div class="amount-row">
                <span class="amount-label">运费</span>
                <span class="amount-value" v-if="canEdit">
                  <input
                    type="number"
                    :value="order.freight_amt"
                    @change="handleFreightChange"
                    min="0"
                    step="0.01"
                    class="freight-input"
                  />
                </span>
                <span class="amount-value" v-else>{{ formatAmount(order.freight_amt) }}</span>
              </div>
              <div class="amount-row highlight">
                <span class="amount-label">合计金额</span>
                <span class="amount-value">{{ formatAmount(order.total_amt + (order.freight_amt || 0)) }}</span>
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

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.audited { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.closed { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.none { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }

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

/* 运费输入框 */
.freight-input {
  width: 120px;
  padding: 4px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  text-align: right;
}

.freight-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

/* 供应商选择 */
.supplier-select {
  width: 100%;
  padding: 6px 10px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.supplier-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

/* 备注 */
.remarks-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0;
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

.btn-danger-outline {
  padding: 8px 16px;
  background-color: transparent;
  color: var(--accent-red);
  border: 1px solid var(--accent-red);
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger-outline:hover { background-color: rgba(239, 68, 68, 0.1); }
.btn-danger-outline:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 900px) {
  .two-col-row {
    grid-template-columns: 1fr;
  }
}
</style>
