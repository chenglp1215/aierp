<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface PurchaseOrderPreview {
  purchase_type: string
  source_sale_order_no: string
  brand_id: string
  brand_name: string
  supplier_id: string
  purchase_user_id: string | null
  receive_info: any
  expect_arrive_date: string | null
  settle_type: string
  remark: string
  items: PurchaseOrderItemPreview[]
}

interface PurchaseOrderItemPreview {
  row_no: number
  product_id: string
  spec_id: string | null
  brand_id: string | null
  brand_name: string | null
  purchase_qty: number
  in_qty: number
  return_qty: number
  purchase_price: number
  discount: number
  amt: number
  shipping_method: string | null
  source_sale_row_no: number | null
  warehouse_id: string | null
}

const props = defineProps<{
  visible: boolean
  orderNo: string
  previewData: PurchaseOrderPreview[]
}>()

const emit = defineEmits<{
  close: []
  submit: [purchaseOrders: any[]]
}>()

const loading = ref(false)
const localData = ref<PurchaseOrderPreview[]>([])

watch(() => props.previewData, (newData) => {
  localData.value = JSON.parse(JSON.stringify(newData))
}, { immediate: true, deep: true })

const visibleOrders = computed(() => {
  return localData.value.filter(order => order.items.length > 0)
})

const totalAmount = computed(() => {
  return visibleOrders.value.reduce((sum, order) => {
    return sum + order.items.reduce((itemSum, item) => itemSum + (item.amt || 0), 0)
  }, 0)
})

const formatPrice = (val: number) => {
  return val?.toFixed(2) || '0.00'
}

const removeOrder = (index: number) => {
  const orderIndex = localData.value.indexOf(visibleOrders.value[index])
  if (orderIndex > -1) {
    localData.value.splice(orderIndex, 1)
  }
}

const removeItem = (orderIndex: number, itemIndex: number) => {
  const order = visibleOrders.value[orderIndex]
  if (order) {
    order.items.splice(itemIndex, 1)
  }
}

const handleSubmit = () => {
  if (visibleOrders.value.length === 0) {
    window.showToast('请至少保留一张采购单', 'warning')
    return
  }
  loading.value = true
  emit('submit', visibleOrders.value)
}

const handleClose = () => {
  emit('close')
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="handleClose">
    <div class="modal preview-modal">
      <div class="modal-header">
        <h3>下推采购预览 — 共 {{ visibleOrders.length }} 张采购单</h3>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div v-if="visibleOrders.length === 0" class="empty-state">
          没有可提交的采购单，请检查商品明细
        </div>
        <div v-else class="order-list">
          <div v-for="(order, oIndex) in visibleOrders" :key="oIndex" class="order-card">
            <div class="order-card-header">
              <div class="order-card-title">
                <span class="type-tag" :class="order.purchase_type === 'direct' ? 'direct' : 'warehouse'">
                  {{ order.purchase_type === 'direct' ? '直运' : '仓库' }}
                </span>
                <span class="brand-name">{{ order.brand_name || order.brand_id }}</span>
              </div>
              <button class="btn-remove-order" @click="removeOrder(oIndex)" title="移除此采购单">
                <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </div>

            <div class="order-card-fields">
              <div class="field-row">
                <label>采购人员</label>
                <input type="text" v-model="order.purchase_user_id" placeholder="请输入采购人员" class="field-input" />
              </div>
              <div class="field-row">
                <label>备注</label>
                <input type="text" v-model="order.remark" placeholder="请输入备注" class="field-input" />
              </div>
            </div>

            <div class="items-table-wrapper">
              <table class="items-table">
                <thead>
                  <tr>
                    <th>商品ID</th>
                    <th>规格</th>
                    <th>数量</th>
                    <th>单价</th>
                    <th>金额</th>
                    <th class="col-action"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, iIndex) in order.items" :key="iIndex">
                    <td>{{ item.product_id }}</td>
                    <td>{{ item.spec_id || '-' }}</td>
                    <td>{{ item.purchase_qty }}</td>
                    <td>{{ formatPrice(item.purchase_price) }}</td>
                    <td>{{ formatPrice(item.amt) }}</td>
                    <td class="col-action">
                      <button class="btn-remove-item" @click="removeItem(oIndex, iIndex)" title="移除商品">
                        <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="order-card-footer">
              小计: <strong>¥{{ formatPrice(order.items.reduce((s, item) => s + (item.amt || 0), 0)) }}</strong>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <div class="total-info" v-if="visibleOrders.length > 0">
          合计: <strong>¥{{ formatPrice(totalAmount) }}</strong>
        </div>
        <div class="footer-actions">
          <button class="btn-secondary" @click="handleClose">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="loading || visibleOrders.length === 0">
            {{ loading ? '提交中...' : '提交下推采购单' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.preview-modal {
  background: var(--color-canvas);
  border-radius: 8px;
  width: 900px;
  max-width: 95vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-hairline);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--color-ink);
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--color-muted);
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.modal-close:hover {
  color: var(--color-ink);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-muted);
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  border: 1px solid var(--color-hairline);
  border-radius: 6px;
  overflow: hidden;
}

.order-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-canvas);
}

.order-card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.type-tag.direct {
  background: rgba(255, 152, 0, 0.15);
  color: var(--color-warning);
}

.type-tag.warehouse {
  background: rgba(76, 175, 80, 0.15);
  color: var(--color-success);
}

.brand-name {
  font-weight: 500;
  color: var(--color-ink);
}

.btn-remove-order {
  background: none;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.btn-remove-order:hover {
  color: var(--color-danger);
  background: rgba(239, 83, 80, 0.1);
}

.order-card-fields {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-row label {
  font-size: 13px;
  color: var(--color-muted);
  min-width: 70px;
  flex-shrink: 0;
}

.field-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-canvas);
  color: var(--color-ink);
  outline: none;
}

.field-input:focus {
  border-color: var(--color-interactive);
}

.items-table-wrapper {
  overflow-x: auto;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.items-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--color-muted);
  border-bottom: 1px solid var(--color-hairline);
  white-space: nowrap;
}

.items-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}

.items-table tbody tr:last-child td {
  border-bottom: none;
}

.items-table .col-action {
  width: 40px;
  text-align: center;
}

.btn-remove-item {
  background: none;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
  display: inline-flex;
  align-items: center;
}

.btn-remove-item:hover {
  color: var(--color-danger);
  background: rgba(239, 83, 80, 0.1);
}

.order-card-footer {
  padding: 10px 16px;
  text-align: right;
  font-size: 13px;
  color: var(--color-muted);
  border-top: 1px solid var(--color-hairline);
}

.order-card-footer strong {
  color: var(--color-ink);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid var(--color-hairline);
}

.total-info {
  font-size: 14px;
  color: var(--color-muted);
}

.total-info strong {
  color: var(--color-interactive);
  font-size: 16px;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  background: var(--color-canvas);
  color: var(--color-ink);
  cursor: pointer;
  font-size: 13px;
}

.btn-secondary:hover {
  background: var(--color-canvas);
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: var(--color-interactive);
  color: #fff;
  cursor: pointer;
  font-size: 13px;
}

.btn-primary:hover {
  background: var(--color-interactive);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
