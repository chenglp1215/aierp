<script setup lang="ts">
defineOptions({ name: 'PendingOutboundWorkspace' })

import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
import { pendingOutboundApi, warehouseApi } from '../../services/api'

// ============ 接口定义 ============

interface PendingOutbound {
  id: number
  pending_no: string
  sales_order_no: string
  row_no: number
  warehouse_id: number
  warehouse_name: string
  spec_id: number
  product_code: string
  spec_code: string
  locked_qty: number
  out_qty: number
  status: string
  outbound_type: string
  delivery_type: string
  province: string | null
  city: string | null
  address: string | null
  recipient_name: string | null
  recipient_phone: string | null
  shipped_at: string | null
  shipping_company: string | null
  tracking_no: string | null
  logistics_status: string | null
  created_at: string
}

interface Warehouse {
  id: string
  name: string
}

// ============ 状态变量 ============

const loading = ref(false)
const pendingOutbounds = ref<PendingOutbound[]>([])
const warehouses = ref<Warehouse[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  warehouse_id: '',
  sales_order_no: '',
  status: ''
})

// ============ 多选状态 ============

const selectedRows = ref<any[]>([])
const isAllSelected = ref(false)
const excludedIds = ref<number[]>([])
const showBatchDropdown = ref(false)
const tableRef = ref<any>(null)

const selectedCount = computed(() => {
  if (isAllSelected.value) {
    return total.value - excludedIds.value.length
  }
  return selectedRows.value.length
})

const hasSelected = computed(() => selectedCount.value > 0)

const showSelectAllBanner = computed(() => {
  if (isAllSelected.value) return true
  const currentPageSelectedCount = pendingOutbounds.value.filter((r: any) =>
    selectedRows.value.some((sr: any) => sr.id === r.id)
  ).length
  return currentPageSelectedCount === pendingOutbounds.value.length
    && pendingOutbounds.value.length > 0
    && total.value > pendingOutbounds.value.length
})

// ============ 状态映射 ============

const statusMap: Record<string, { label: string; class: string }> = {
  pending: { label: '未出库', class: 'pending' },
  outbound: { label: '已出库', class: 'full' },
  shipped: { label: '已发货', class: 'shipped' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '未出库' },
  { value: 'outbound', label: '已出库' },
  { value: 'shipped', label: '已发货' },
  { value: 'cancelled', label: '已取消' }
]

// 出库类型映射
const outboundTypeMap: Record<string, string> = {
  order_outbound: '订单出库',
  transfer_outbound: '调拨出库'
}

const getOutboundTypeLabel = (type: string) => outboundTypeMap[type] || type

// 配送方式映射
const deliveryTypeMap: Record<string, string> = {
  logistics: '物流发货',
  pickup: '等待自提'
}

const getDeliveryTypeLabel = (type: string) => deliveryTypeMap[type] || type

// 物流状态映射
const logisticsStatusMap: Record<string, { label: string; class: string }> = {
  pending: { label: '待取件', class: 'logistics-pending' },
  picked_up: { label: '已取件', class: 'logistics-picked-up' },
  in_transit: { label: '运输中', class: 'logistics-in-transit' },
  delivered: { label: '已签收', class: 'logistics-delivered' },
  exception: { label: '异常', class: 'logistics-exception' }
}

const getLogisticsStatusLabel = (status: string) => logisticsStatusMap[status]?.label || status
const getLogisticsStatusClass = (status: string) => logisticsStatusMap[status]?.class || ''

// ============ 弹窗状态 ============

const showOutboundModal = ref(false)
const selectedPending = ref<PendingOutbound | null>(null)
const outboundQty = ref(0)
const outboundLoading = ref(false)

// 发货弹窗状态
const showShipModal = ref(false)
const shipLoading = ref(false)

// 撤销弹窗状态
const showRevokeModal = ref(false)
const revokeLoading = ref(false)

// 批次选择相关
interface AvailableBatch {
  id: number
  batch_no?: string | null
  location_code: string | null
  expiry_date: string | null
  current_quantity: number
  out_quantity: number
}
const availableBatches = ref<AvailableBatch[]>([])
const batchLoading = ref(false)

const loadAvailableBatches = async (pendingId: number) => {
  batchLoading.value = true
  try {
    const res = await pendingOutboundApi.getAvailableBatches(pendingId)
    const batches = res?.items || res || []
    availableBatches.value = batches.map((b: any) => ({
      ...b,
      out_quantity: 0
    }))
    // 先进先出自动填充
    autoFillBatches()
  } catch (e) {
    console.error('加载可出库批次失败:', e)
    availableBatches.value = []
  } finally {
    batchLoading.value = false
  }
}

const autoFillBatches = () => {
  let remaining = outboundQty.value
  for (const batch of availableBatches.value) {
    if (remaining <= 0) {
      batch.out_quantity = 0
      continue
    }
    const take = Math.min(remaining, batch.current_quantity)
    batch.out_quantity = take
    remaining -= take
  }
}

const totalBatchQuantity = computed(() => {
  return availableBatches.value.reduce((sum, b) => sum + b.out_quantity, 0)
})

const isBatchExpired = (batch: AvailableBatch) => {
  if (!batch.expiry_date) return false
  return new Date(batch.expiry_date) < new Date()
}

const isBatchExpiring = (batch: AvailableBatch) => {
  if (!batch.expiry_date) return false
  const d = new Date(batch.expiry_date)
  return d >= new Date() && d < new Date(Date.now() + 30 * 24 * 3600 * 1000)
}


// ============ 计算属性 ============

const filteredWarehouses = computed(() => {
  return warehouses.value
})

const hasActiveFilters = computed(() => {
  return filters.value.warehouse_id || filters.value.sales_order_no || filters.value.status
})

// ============ 多选方法 ============

const handleCheckboxChange = ({ records }: { records: any[] }) => {
  if (isAllSelected.value) {
    const currentPageIds = new Set(pendingOutbounds.value.map((r: any) => r.id))
    const currentSelectedIds = new Set(records.map((r: any) => r.id))
    const newExcluded = [...excludedIds.value]
    for (const id of currentPageIds) {
      if (!currentSelectedIds.has(id)) {
        if (!newExcluded.includes(id)) newExcluded.push(id)
      } else {
        const idx = newExcluded.indexOf(id)
        if (idx !== -1) newExcluded.splice(idx, 1)
      }
    }
    excludedIds.value = newExcluded
  } else {
    selectedRows.value = records
  }
}

const handleCheckboxAll = ({ records }: { records: any[] }) => {
  if (isAllSelected.value) {
    const currentPageIds = pendingOutbounds.value.map((r: any) => r.id)
    const allChecked = records.length === pendingOutbounds.value.length
    const newExcluded = [...excludedIds.value]
    for (const id of currentPageIds) {
      const idx = newExcluded.indexOf(id)
      if (allChecked) {
        if (idx !== -1) newExcluded.splice(idx, 1)
      } else {
        if (idx === -1) newExcluded.push(id)
      }
    }
    excludedIds.value = newExcluded
  } else {
    selectedRows.value = records
  }
}

const handleSelectAll = () => {
  isAllSelected.value = true
}

const clearSelection = () => {
  selectedRows.value = []
  isAllSelected.value = false
  excludedIds.value = []
}

const toggleBatchDropdown = () => {
  if (hasSelected.value) {
    showBatchDropdown.value = !showBatchDropdown.value
  }
}

const closeBatchDropdown = () => {
  showBatchDropdown.value = false
}

const handleExportOutbound = async () => {
  closeBatchDropdown()
  try {
    const params: any = {}
    if (isAllSelected.value) {
      params.select_all = true
      params.warehouse_id = filters.value.warehouse_id || undefined
      params.sales_order_no = filters.value.sales_order_no || undefined
      params.status = filters.value.status || undefined
      params.excluded_ids = excludedIds.value
    } else {
      params.select_all = false
      params.selected_ids = selectedRows.value.map((r: any) => r.id)
    }
    await pendingOutboundApi.export(params)
  } catch (error: any) {
    window.showToast('功能开发中', 'info')
  }
}

const handleDocumentClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.batch-action-container')) {
    showBatchDropdown.value = false
  }
}

// ============ 方法 ============

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page_size: 100 })
    warehouses.value = res?.items || []
  } catch (e) {
    console.error('加载仓库列表失败:', e)
  }
}

const loadPendingOutbounds = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }
    if (filters.value.warehouse_id) {
      params.warehouse_id = filters.value.warehouse_id
    }
    if (filters.value.sales_order_no) {
      params.sales_order_no = filters.value.sales_order_no
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    const res = await pendingOutboundApi.list(params)
    pendingOutbounds.value = res?.items || []
    total.value = res?.total || 0
    // 全选模式下，自动勾选当前页未被排除的行
    if (isAllSelected.value && tableRef.value) {
      await nextTick()
      const rowsToCheck = pendingOutbounds.value.filter((r: any) => !excludedIds.value.includes(r.id))
      tableRef.value.setCheckboxRow(rowsToCheck, true)
    }
  } catch (e) {
    console.error('加载待出库单失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  clearSelection()
  loadPendingOutbounds()
}

const handleReset = () => {
  filters.value = {
    warehouse_id: '',
    sales_order_no: '',
    status: ''
  }
  page.value = 1
  clearSelection()
  loadPendingOutbounds()
}

// vxe-pager 分页处理函数
const handlePageChange = ({ currentPage, pageSize: newSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newSize
  loadPendingOutbounds()
}

const openOutboundModal = (item: PendingOutbound) => {
  selectedPending.value = item
  outboundQty.value = item.locked_qty - item.out_qty
  availableBatches.value = []
  loadAvailableBatches(item.id)
  showOutboundModal.value = true
}

const handleOutbound = async () => {
  if (!selectedPending.value || outboundQty.value <= 0) return

  outboundLoading.value = true
  try {
    const batchItems = availableBatches.value
      .filter(b => b.out_quantity > 0)
      .map(b => ({ inbound_batch_id: b.id, quantity: b.out_quantity }))
    await pendingOutboundApi.execute(selectedPending.value.id, outboundQty.value, batchItems.length > 0 ? batchItems : undefined)
    window.showToast('出库成功', 'success')
    showOutboundModal.value = false
    selectedPending.value = null
    outboundQty.value = 0
    await loadPendingOutbounds()
  } catch (error: any) {
    window.showToast(error.message || '出库失败', 'error')
  } finally {
    outboundLoading.value = false
  }
}

const openShipModal = (item: PendingOutbound) => {
  selectedPending.value = item
  showShipModal.value = true
}

const handleShip = async () => {
  if (!selectedPending.value) return
  shipLoading.value = true
  try {
    await pendingOutboundApi.ship(selectedPending.value.id)
    window.showToast('发货成功', 'success')
    showShipModal.value = false
    selectedPending.value = null
    await loadPendingOutbounds()
  } catch (error: any) {
    window.showToast(error.message || '发货失败', 'error')
  } finally {
    shipLoading.value = false
  }
}

const openRevokeModal = (item: PendingOutbound) => {
  selectedPending.value = item
  showRevokeModal.value = true
}

const handleRevoke = async () => {
  if (!selectedPending.value) return
  revokeLoading.value = true
  try {
    await pendingOutboundApi.revoke(selectedPending.value.id)
    window.showToast('撤销成功', 'success')
    showRevokeModal.value = false
    selectedPending.value = null
    await loadPendingOutbounds()
  } catch (error: any) {
    window.showToast(error.message || '撤销失败', 'error')
  } finally {
    revokeLoading.value = false
  }
}

const getStatusLabel = (status: string) => statusMap[status]?.label || status
const getStatusClass = (status: string) => statusMap[status]?.class || ''

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

onMounted(async () => {
  await loadWarehouses()
  await loadPendingOutbounds()

  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="pending-outbound-workspace">
    <!-- 列表头部 -->
    <div class="workspace-header">
      <h2 class="workspace-title">出库管理</h2>
      <div class="batch-action-container">
        <button
          class="batch-action-btn"
          :class="{ active: hasSelected, disabled: !hasSelected }"
          @click="toggleBatchDropdown"
        >
          <span>批量操作</span>
          <span v-if="hasSelected" class="batch-count">({{ selectedCount }})</span>
          <svg class="dropdown-arrow" :class="{ rotated: showBatchDropdown }" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 10l5 5 5-5z"/>
          </svg>
        </button>
        <div v-if="showBatchDropdown && hasSelected" class="batch-dropdown">
          <button class="batch-dropdown-item" @click="handleExportOutbound">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
            <span>导出出库单</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <select v-model="filters.warehouse_id" class="filter-select">
            <option value="">全部仓库</option>
            <option v-for="wh in filteredWarehouses" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
          </select>
        </div>
        <div class="filter-item" style="flex: 1; min-width: 200px;">
          <input
            v-model="filters.sales_order_no"
            class="filter-input"
            placeholder="销售订单号"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select v-model="filters.status" class="filter-select">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button v-if="hasActiveFilters" class="filter-btn reset-btn" @click="handleReset">重置</button>
      </div>
    </div>

    <!-- 表格区 -->
    <div class="table-section">
      <!-- 全选提示条 -->
      <div class="select-all-banner" v-if="showSelectAllBanner">
        <div class="banner-content" v-if="!isAllSelected">
          <svg class="banner-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
          <span>已选中当前页 {{ pendingOutbounds.length }} 条</span>
          <button class="banner-link" @click="handleSelectAll">选择全部筛选结果（共 {{ total }} 条）</button>
          <button class="banner-close" @click="clearSelection">&times;</button>
        </div>
        <div class="banner-content" v-else>
          <svg class="banner-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          <span>已选择全部 {{ total }} 条数据<span v-if="excludedIds.length > 0">（已排除 {{ excludedIds.length }} 条）</span></span>
          <button class="banner-link" @click="clearSelection">取消全选</button>
        </div>
      </div>
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        ref="tableRef"
        :data="pendingOutbounds"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: ({ rowIndex }) => rowIndex + 1 + (page - 1) * pageSize }"
        :row-config="{ isHover: true }"
        :checkbox-config="{ reserve: true }"
        @checkbox-change="handleCheckboxChange"
        @checkbox-all="handleCheckboxAll"
      >
        <vxe-column type="checkbox" width="50" fixed="left" class-name="col--center" />
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column field="pending_no" title="待出库单号" width="160" class-name="col--center" />
        <vxe-column field="sales_order_no" title="销售订单号" width="160" class-name="col--center" />
        <vxe-column field="row_no" title="行号" width="60" class-name="col--center" />
        <vxe-column field="warehouse_name" title="仓库" width="120" class-name="col--left" />
        <vxe-column field="product_code" title="商品编码" width="140" class-name="col--left" />
        <vxe-column field="spec_code" title="规格编码" width="140" class-name="col--left" />
        <vxe-column title="数量" width="180" class-name="col--left">
          <template #default="{ row }">
            <div class="qty-cell">
              <div class="qty-row"><span class="qty-label">锁定:</span><span class="qty-value">{{ row.locked_qty }}</span></div>
              <div class="qty-row"><span class="qty-label">已出:</span><span class="qty-value">{{ row.out_qty }}</span></div>
              <div class="qty-row"><span class="qty-label">待出:</span><span class="qty-value">{{ row.locked_qty - row.out_qty }}</span></div>
            </div>
          </template>
        </vxe-column>
        <vxe-column field="status" title="状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getStatusClass(row.status)">
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="outbound_type" title="出库类型" width="100" class-name="col--center">
          <template #default="{ row }">
            {{ getOutboundTypeLabel(row.outbound_type) }}
          </template>
        </vxe-column>
        <vxe-column field="delivery_type" title="配送方式" width="100" class-name="col--center">
          <template #default="{ row }">
            {{ getDeliveryTypeLabel(row.delivery_type) }}
          </template>
        </vxe-column>
        <vxe-column title="收货信息" width="160" class-name="col--left">
          <template #default="{ row }">
            <span v-if="row.recipient_name || row.recipient_phone">
              {{ [row.recipient_name, row.recipient_phone].filter(Boolean).join(' ') }}
            </span>
            <span v-else>-</span>
          </template>
        </vxe-column>
        <vxe-column field="tracking_no" title="物流单号" width="140" class-name="col--center">
          <template #default="{ row }">
            {{ row.tracking_no || '-' }}
          </template>
        </vxe-column>
        <vxe-column field="logistics_status" title="物流状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span v-if="row.logistics_status" class="status-tag" :class="getLogisticsStatusClass(row.logistics_status)">
              {{ getLogisticsStatusLabel(row.logistics_status) }}
            </span>
            <span v-else>-</span>
          </template>
        </vxe-column>
        <vxe-column field="created_at" title="创建时间" width="160" class-name="col--center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </vxe-column>
        <vxe-column title="操作" width="160" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button
                v-if="row.status === 'pending'"
                class="btn-link success"
                @click="openOutboundModal(row)"
              >
                出库
              </button>
              <button
                v-if="row.status === 'outbound'"
                class="btn-link primary"
                @click="openShipModal(row)"
              >
                发货
              </button>
              <button
                v-if="row.status === 'outbound'"
                class="btn-link warning"
                @click="openRevokeModal(row)"
              >
                撤销
              </button>
              <span v-if="row.status === 'shipped' || row.status === 'cancelled'" class="text-muted">-</span>
            </span>
          </template>
        </vxe-column>
      </vxe-table>
      <vxe-pager
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :layouts="['PrevPage', 'JumpNumber', 'NextPage', 'FullJump', 'Sizes', 'Total']"
        @page-change="handlePageChange"
      />
    </div>

    <!-- 出库确认弹窗 -->
    <div class="modal-overlay" v-if="showOutboundModal">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认出库</h3>
          <button class="modal-close" @click="showOutboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-grid">
              <div class="detail-item">
                <label>待出库单号</label>
                <span>{{ selectedPending?.pending_no }}</span>
              </div>
              <div class="detail-item">
                <label>商品编码</label>
                <span>{{ selectedPending?.product_code }}</span>
              </div>
              <div class="detail-item">
                <label>规格编码</label>
                <span>{{ selectedPending?.spec_code }}</span>
              </div>
              <div class="detail-item">
                <label>仓库</label>
                <span>{{ selectedPending?.warehouse_name }}</span>
              </div>
              <div class="detail-item">
                <label>待出库数量</label>
                <span>{{ selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0 }}</span>
              </div>
              <div class="detail-item">
                <label>收货人</label>
                <span>{{ selectedPending?.recipient_name || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>收货电话</label>
                <span>{{ selectedPending?.recipient_phone || '-' }}</span>
              </div>
              <div class="detail-item full-width">
                <label>收货地址</label>
                <span>{{ [selectedPending?.province, selectedPending?.city, selectedPending?.address].filter(Boolean).join(' ') || '-' }}</span>
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-row">
              <div class="form-group full-width">
                <label>出库数量</label>
                <span class="readonly-value">{{ outboundQty }}</span>
              </div>
            </div>
          </div>
          <div class="batch-select-section" v-if="availableBatches.length > 0">
            <h4>批次选择（按有效期排序，优先出库即将过期的批次）</h4>
            <div class="batch-loading" v-if="batchLoading">加载批次中...</div>
            <table class="batch-table" v-else>
              <thead>
                <tr>
                  <th>批次编号</th>
                  <th>库位</th>
                  <th>有效期</th>
                  <th>剩余数量</th>
                  <th>出库数量</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="batch in availableBatches" :key="batch.id" :class="{ 'batch-expired': isBatchExpired(batch), 'batch-expiring': isBatchExpiring(batch) }">
                  <td>{{ batch.batch_no || '-' }}</td>
                  <td>{{ batch.location_code || '-' }}</td>
                  <td>{{ batch.expiry_date ? batch.expiry_date.substring(0, 10) : '-' }}</td>
                  <td>{{ batch.current_quantity }}</td>
                  <td>
                    <span v-if="isBatchExpired(batch)">0</span>
                    <span v-else>{{ batch.out_quantity || 0 }}</span>
                  </td>
                  <td>
                    <span v-if="isBatchExpired(batch)" class="batch-status expired">已过期</span>
                    <span v-else-if="isBatchExpiring(batch)" class="batch-status expiring">即将过期</span>
                    <span v-else class="batch-status normal">正常</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="batch-summary" v-if="availableBatches.length > 0">
              <span>批次出库合计: {{ totalBatchQuantity }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showOutboundModal = false">取消</button>
          <button class="btn-primary" @click="handleOutbound" :disabled="outboundLoading || outboundQty <= 0">
            {{ outboundLoading ? '处理中...' : '确认出库' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 发货确认弹窗 -->
    <div class="modal-overlay" v-if="showShipModal">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>{{ selectedPending?.delivery_type === 'pickup' ? '确认自提发货' : '确认发货' }}</h3>
          <button class="modal-close" @click="showShipModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-grid">
              <div class="detail-item">
                <label>出库单号</label>
                <span>{{ selectedPending?.pending_no }}</span>
              </div>
              <div class="detail-item">
                <label>商品编码</label>
                <span>{{ selectedPending?.product_code }}</span>
              </div>
              <div class="detail-item">
                <label>规格编码</label>
                <span>{{ selectedPending?.spec_code }}</span>
              </div>
              <div class="detail-item">
                <label>仓库</label>
                <span>{{ selectedPending?.warehouse_name }}</span>
              </div>
              <div class="detail-item">
                <label>收货人</label>
                <span>{{ selectedPending?.recipient_name || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>收货电话</label>
                <span>{{ selectedPending?.recipient_phone || '-' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showShipModal = false">取消</button>
          <button class="btn-primary" @click="handleShip" :disabled="shipLoading">
            {{ shipLoading ? '处理中...' : (selectedPending?.delivery_type === 'pickup' ? '确认自提发货' : '确认发货') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 撤销确认弹窗 -->
    <div class="modal-overlay" v-if="showRevokeModal">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认撤销出库</h3>
          <button class="modal-close" @click="showRevokeModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="warning-text">
            撤销后，出库单将回退为"未出库"状态，对应入库批次的剩余数量将恢复，锁定数量不变。确定要撤销吗？
          </div>
          <div class="detail-section">
            <div class="detail-grid">
              <div class="detail-item">
                <label>出库单号</label>
                <span>{{ selectedPending?.pending_no }}</span>
              </div>
              <div class="detail-item">
                <label>商品编码</label>
                <span>{{ selectedPending?.product_code }}</span>
              </div>
              <div class="detail-item">
                <label>规格编码</label>
                <span>{{ selectedPending?.spec_code }}</span>
              </div>
              <div class="detail-item">
                <label>出库数量</label>
                <span>{{ selectedPending?.out_qty }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showRevokeModal = false">取消</button>
          <button class="btn-danger" @click="handleRevoke" :disabled="revokeLoading">
            {{ revokeLoading ? '处理中...' : '确认撤销' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pending-outbound-workspace {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ============ 头部 ============ */

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* ============ 筛选区 ============ */

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
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

.filter-input,
.filter-select {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.filter-input:focus,
.filter-select:focus {
  border-color: var(--accent-blue);
}

.filter-input {
  width: 100%;
}

.filter-select {
  min-width: 120px;
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

/* ============ 表格区 ============ */

.table-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  position: relative;
}

.table-loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: var(--radius-lg);
}

.table-loading-content {
  padding: 12px 24px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

/* ============ 状态标签 ============ */

.readonly-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 4px 0;
}
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.pending { background-color: rgba(245,158,11,0.1); color: var(--accent-yellow); }
.status-tag.partial { background-color: rgba(59,130,246,0.1); color: var(--accent-blue); }
.status-tag.full { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(128,128,128,0.1); color: var(--text-muted); }

.text-muted {
  color: var(--text-muted);
}

/* ============ 操作按钮 ============ */

.action-btns {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

.btn-link {
  padding: 4px 8px;
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color var(--transition-fast);
}

.btn-link:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.btn-link.success { color: var(--accent-green); }
.btn-link.success:hover { background-color: rgba(16,185,129,0.1); }

/* ============ 弹窗 ============ */

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
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.confirm-modal {
  width: 560px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

/* ============ 详情展示 ============ */

.detail-section {
  margin-bottom: 24px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-item label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
}

/* ============ 表单 ============ */

.form-section {
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-control {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.form-control:focus {
  border-color: var(--accent-blue);
}

/* ============ 按钮 ============ */

.btn-secondary {
  padding: 8px 16px;
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.btn-primary {
  padding: 8px 16px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-primary:hover {
  background-color: var(--accent-blue-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ============ 批次选择 ============ */

.batch-select-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.batch-select-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.batch-loading {
  text-align: center;
  padding: 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.batch-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 12px;
}

.batch-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--text-secondary);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.batch-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.batch-table tr.batch-expired {
  opacity: 0.5;
}

.batch-table tr.batch-expired td {
  color: var(--text-muted);
}

.batch-table tr.batch-expiring td {
  color: var(--accent-yellow);
}

.batch-qty-input {
  width: 80px;
  padding: 4px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  text-align: right;
  outline: none;
}

.batch-qty-input:focus {
  border-color: var(--accent-blue);
}

.batch-qty-input:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.batch-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.batch-status.expired {
  background-color: rgba(245, 108, 108, 0.15);
  color: var(--accent-red);
}

.batch-status.expiring {
  background-color: rgba(230, 162, 60, 0.15);
  color: var(--accent-yellow);
}

.batch-status.normal {
  background-color: rgba(103, 194, 58, 0.15);
  color: var(--accent-green);
}

.batch-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 0;
}

.batch-error {
  color: var(--accent-red);
  font-weight: 500;
}

/* ============ 全选提示条 ============ */

.select-all-banner {
  margin-bottom: 12px;
  padding: 10px 16px;
  background-color: rgba(0, 120, 212, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(0, 120, 212, 0.2);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--accent-blue);
}

.banner-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.banner-link {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.banner-link:hover {
  opacity: 0.8;
}

.banner-close {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.banner-close:hover {
  color: var(--text-primary);
}

/* ============ 批量操作下拉菜单 ============ */

.batch-action-container {
  position: relative;
}

.batch-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: not-allowed;
  transition: all var(--transition-fast);
  user-select: none;
}

.batch-action-btn.active {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
  cursor: pointer;
}

.batch-action-btn.active:hover {
  background-color: var(--accent-blue-hover);
}

.batch-count {
  font-weight: 600;
}

.dropdown-arrow {
  width: 14px;
  height: 14px;
  transition: transform var(--transition-fast);
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.batch-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 160px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-hover);
  z-index: 200;
  overflow: hidden;
}

.batch-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  text-align: left;
}

.batch-dropdown-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.batch-dropdown-item svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

/* ============ 响应式 ============ */

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-input,
  .filter-select {
    width: 100%;
  }
}

.warning-text {
  color: var(--accent-yellow);
  font-size: 14px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 4px;
}
.btn-link.primary {
  color: var(--accent-blue);
}
.btn-link.warning {
  color: var(--accent-yellow);
}
.btn-danger {
  padding: 8px 20px;
  background: var(--accent-red);
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-danger:hover {
  background: var(--accent-red);
  filter: brightness(1.15);
}
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.status-tag.shipped {
  background: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

/* 数量合并列样式 */
.qty-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.4;
}

.qty-row {
  display: flex;
  align-items: center;
  gap: 2px;
}

.qty-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 28px;
}

.qty-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

/* 收货信息合并列样式 */
.receiver-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.receiver-phone {
  color: var(--text-muted);
  font-size: 12px;
}

/* 物流状态标签样式 */
.status-tag.logistics-pending { background-color: rgba(245,158,11,0.1); color: var(--accent-yellow); }
.status-tag.logistics-picked-up { background-color: rgba(59,130,246,0.1); color: var(--accent-blue); }
.status-tag.logistics-in-transit { background-color: rgba(99,102,241,0.1); color: #6366f1; }
.status-tag.logistics-delivered { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }
.status-tag.logistics-exception { background-color: rgba(245,108,108,0.15); color: var(--accent-red); }

/* ============ vxe-table 行 hover/焦点覆盖 ============ */

:deep(.vxe-body--column) {
  &.expand--cell,
  &.col--actived {
    background-color: var(--bg-card) !important;
  }
}

:deep(.vxe-body--row) > td {
  background-color: var(--bg-card) !important;
}

:deep(.vxe-body--row:hover) > td {
  background-color: var(--bg-secondary) !important;
}

/* ============ 亮色主题覆盖 ============ */

[data-theme="light"] .table-loading-overlay {
  background-color: rgba(255, 255, 255, 0.8);
}

[data-theme="light"] .filter-btn.reset-btn:hover,
[data-theme="light"] .batch-dropdown-item:hover,
[data-theme="light"] .btn-secondary:hover,
[data-theme="light"] .modal-close:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

[data-theme="light"] .warning-text {
  background: rgba(245, 158, 11, 0.1);
}

[data-theme="light"] .batch-action-btn:not(.active) {
  border-color: #e5e7eb;
}
</style>
