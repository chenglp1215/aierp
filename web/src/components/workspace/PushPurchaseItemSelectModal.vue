<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface OrderItem {
  row_no: number
  product_id: string
  product_name?: string
  brand_name?: string
  brand_id?: string
  purchaser_name?: string
  spec_id?: string
  spec_code?: string
  qty: number
  price: number
  amt: number
  purchase_qty?: number
  pushed_qty?: number
  shipping_method?: string
  stock_quantity?: number
  stock_status?: string
}

const props = defineProps<{
  visible: boolean
  items: OrderItem[]
}>()

const emit = defineEmits<{
  close: []
  submit: [selectedRowNos: number[]]
}>()

const loading = ref(false)
const selectedRowNos = ref<Set<number>>(new Set())

watch(() => props.visible, (val) => {
  if (val) {
    loading.value = false
    const newSet = new Set<number>()
    props.items.forEach(item => {
      const purchaseQty = item.purchase_qty ?? 0
      const pushedQty = item.pushed_qty ?? 0
      const pendingQty = purchaseQty - pushedQty
      // 有待下推数量才默认选中
      if (pendingQty > 0) {
        newSet.add(item.row_no)
      }
    })
    selectedRowNos.value = newSet
  }
}, { immediate: true })

// 计算待下推数量
const getPendingQty = (item: OrderItem): number => {
  const purchaseQty = item.purchase_qty ?? 0
  const pushedQty = item.pushed_qty ?? 0
  return Math.max(0, purchaseQty - pushedQty)
}

// 判断是否可下推：有待下推数量
const isPushable = (item: OrderItem): boolean => {
  return getPendingQty(item) > 0
}

// 直运商品始终可下推；非直运商品仅库存不足时可下推
const pushableItems = computed(() => {
  return props.items.filter(item => isPushable(item))
})

const allSelected = computed(() => {
  return pushableItems.value.length > 0 && pushableItems.value.every(item => selectedRowNos.value.has(item.row_no))
})

const selectedCount = computed(() => {
  return pushableItems.value.filter(item => selectedRowNos.value.has(item.row_no)).length
})

const toggleAll = () => {
  if (allSelected.value) {
    pushableItems.value.forEach(item => selectedRowNos.value.delete(item.row_no))
  } else {
    pushableItems.value.forEach(item => selectedRowNos.value.add(item.row_no))
  }
}

const toggleItem = (rowNo: number) => {
  if (selectedRowNos.value.has(rowNo)) {
    selectedRowNos.value.delete(rowNo)
  } else {
    selectedRowNos.value.add(rowNo)
  }
}

const stockStatusMap: Record<string, { label: string; class: string }> = {
  normal: { label: '充足', class: 'stock-normal' },
  low_stock: { label: '偏低', class: 'stock-low' },
  out_of_stock: { label: '缺货', class: 'stock-out' },
  overstock: { label: '积压', class: 'stock-over' }
}

const getStockStatus = (item: OrderItem) => {
  return stockStatusMap[item.stock_status || ''] || { label: '-', class: '' }
}

// 获取下推状态
const getPushStatus = (item: OrderItem): { label: string; class: string } => {
  const purchaseQty = item.purchase_qty ?? 0
  const pushedQty = item.pushed_qty ?? 0
  const pendingQty = purchaseQty - pushedQty

  if (purchaseQty === 0) {
    return { label: '无需下推', class: 'skip' }
  }
  if (pendingQty === 0) {
    return { label: '已下推', class: 'pushed' }
  }
  if (pushedQty > 0) {
    return { label: '部分下推', class: 'partial' }
  }
  return { label: '待下推', class: 'pending' }
}

const getPushReason = (item: OrderItem): string => {
  const purchaseQty = item.purchase_qty ?? 0
  const pushedQty = item.pushed_qty ?? 0
  const pendingQty = purchaseQty - pushedQty

  if (purchaseQty === 0) {
    return '库存充足，无需采购'
  }
  if (pendingQty === 0) {
    return `已下推 ${pushedQty}/${purchaseQty}`
  }
  if (pushedQty > 0) {
    return `待下推 ${pendingQty}（已下推 ${pushedQty}/${purchaseQty}）`
  }
  return `待下推 ${pendingQty}`
}

const formatPrice = (val: number) => {
  return val?.toFixed(2) || '0.00'
}

const handleSubmit = () => {
  if (selectedCount.value === 0) {
    window.showToast('请至少选择一件商品', 'warning')
    return
  }
  loading.value = true
  const selected = Array.from(selectedRowNos.value)
  emit('submit', selected)
}

const handleClose = () => {
  emit('close')
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="handleClose">
    <div class="modal item-select-modal">
      <div class="modal-header">
        <h3>下推采购 — 选择商品</h3>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div v-if="items.length === 0" class="empty-state">
          暂无商品数据
        </div>
        <div v-else class="table-wrapper">
          <table class="items-table">
            <thead>
              <tr>
                <th class="col-checkbox">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    @change="toggleAll"
                    :disabled="pushableItems.length === 0"
                  />
                </th>
                <th>商品名</th>
                <th>品牌</th>
                <th>规格编号</th>
                <th class="col-num">数量</th>
                <th class="col-num">库存</th>
                <th>库存状态</th>
                <th class="col-num">单价</th>
                <th class="col-num">金额</th>
                <th>采购人</th>
                <th>下推状态</th>
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.row_no" :class="{ 'row-disabled': !isPushable(item) }">
                <td class="col-checkbox">
                  <input
                    type="checkbox"
                    :checked="selectedRowNos.has(item.row_no)"
                    :disabled="!isPushable(item)"
                    @change="toggleItem(item.row_no)"
                  />
                </td>
                <td>{{ item.product_name || item.product_id }}</td>
                <td>{{ item.brand_name || '-' }}</td>
                <td>{{ item.spec_code || item.spec_id || '-' }}</td>
                <td class="col-num">{{ item.qty }}</td>
                <td class="col-num">{{ item.stock_quantity ?? '-' }}</td>
                <td>
                  <span v-if="item.shipping_method !== '直运' && item.stock_status" class="stock-tag" :class="getStockStatus(item).class">
                    {{ getStockStatus(item).label }}
                  </span>
                  <span v-else class="col-empty">-</span>
                </td>
                <td class="col-num">{{ formatPrice(item.price) }}</td>
                <td class="col-num">{{ formatPrice(item.amt) }}</td>
                <td class="col-empty">{{ item.purchaser_name || '-' }}</td>
                <td>
                  <span class="status-tag" :class="getPushStatus(item).class">
                    {{ getPushStatus(item).label }}
                  </span>
                </td>
                <td class="col-reason">{{ getPushReason(item) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="modal-footer">
        <div class="selected-info" v-if="pushableItems.length > 0">
          已选 <strong>{{ selectedCount }}</strong> / {{ pushableItems.length }} 件商品
        </div>
        <div class="footer-actions">
          <button class="btn-secondary" @click="handleClose">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="loading || selectedCount === 0">
            {{ loading ? '提交中...' : '确认下推采购' }}
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

.item-select-modal {
  background: var(--bg-primary);
  border-radius: 8px;
  width: 850px;
  max-width: 95vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.table-wrapper {
  overflow-x: auto;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.items-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

.items-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.items-table tbody tr:last-child td {
  border-bottom: none;
}

.items-table tbody tr.row-disabled {
  opacity: 0.5;
}

.col-reason {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-num {
  text-align: right;
  white-space: nowrap;
}

.col-empty {
  color: var(--text-muted);
}

.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-tag.pushed {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-tag.pending {
  background: rgba(255, 152, 0, 0.15);
  color: #ff9800;
}

.status-tag.partial {
  background: rgba(33, 150, 243, 0.15);
  color: #2196f3;
}

.status-tag.skip {
  background: rgba(128, 128, 128, 0.15);
  color: var(--text-muted);
}

.stock-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.stock-tag.stock-normal {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.stock-tag.stock-low {
  background: rgba(255, 152, 0, 0.15);
  color: #ff9800;
}

.stock-tag.stock-out {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

.stock-tag.stock-over {
  background: rgba(33, 150, 243, 0.15);
  color: #2196f3;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}

.selected-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.selected-info strong {
  color: var(--accent-blue);
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 13px;
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: var(--accent-blue);
  color: #fff;
  cursor: pointer;
  font-size: 13px;
}

.btn-primary:hover {
  background: #0066b3;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
