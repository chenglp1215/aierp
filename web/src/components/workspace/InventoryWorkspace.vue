<script setup lang="ts">
defineOptions({ name: 'InventoryWorkspace' })

import { ref, computed, onMounted, watch } from 'vue'
import { stockApi, warehouseApi, productApi } from '../../services/api'

interface InboundBatch {
  id: string
  inventory_id: string
  batch_code: string
  quantity: number
  operator_name?: string
  remarks?: string
  created_at: string
}

interface OutboundBatch {
  id: string
  inventory_id: string
  batch_code: string
  quantity: number
  operator_name?: string
  remarks?: string
  created_at: string
}

interface InboundOutboundSummary {
  total_inbound: number
  total_outbound: number
  inbound_count: number
  outbound_count: number
}

interface StockSpecInfo {
  spec_id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price?: number
}

interface StockProductInfo {
  product_id: string
  product_code: string
  product_name: string
  category?: string
}

interface StockWarehouseInfo {
  warehouse_id: string
  warehouse_code: string
  warehouse_name: string
}

interface Stock {
  id: string
  spec_id: string
  warehouse_id: string
  product_id: string
  spec?: StockSpecInfo
  product?: StockProductInfo
  warehouse?: StockWarehouseInfo
  quantity: number
  min_stock: number
  max_stock: number
  status: string
  inbound_outbound_summary?: InboundOutboundSummary
  created_at: string
  updated_at: string
}

interface Warehouse {
  id: string
  warehouse_code: string
  name: string
}

interface ProductSpec {
  id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price?: number
  product_id: string
  product_name?: string
  product_code?: string
}

const props = defineProps<{
  warehouseId?: string
  warehouseName?: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
}>()

const loading = ref(false)
const stocks = ref<Stock[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterWarehouse = ref(props.warehouseId || '')
const filterStatus = ref('')
const filterSpecId = ref('')
const filterSpecName = ref('')
const warehouses = ref<Warehouse[]>([])
const expandedStockId = ref<string | null>(null)
const stockDetail = ref<{
  stock: Stock
  inbound_batches: InboundBatch[]
  outbound_batches: OutboundBatch[]
} | null>(null)
const detailLoading = ref(false)

const showStockModal = ref(false)
const showInboundModal = ref(false)
const showOutboundModal = ref(false)
const showDetailModal = ref(false)
const editingStock = ref<Stock | null>(null)
const inboundTargetStock = ref<Stock | null>(null)
const outboundTargetStock = ref<Stock | null>(null)
const formLoading = ref(false)

const filterKeyword = ref('')
const filterSearchResults = ref<ProductSpec[]>([])
const showFilterDropdown = ref(false)
const selectedFilterSpec = ref<ProductSpec | null>(null)

const productKeyword = ref('')
const productSearchResults = ref<any[]>([])
const showProductDropdown = ref(false)
const selectedProduct = ref<any | null>(null)
const filterProductId = ref('')

const specKeyword = ref('')
const specSearchResults = ref<ProductSpec[]>([])
const showSpecDropdown = ref(false)
const selectedSpec = ref<ProductSpec | null>(null)

const stockForm = ref<Partial<Stock & { spec_id: string; warehouse_id: string }>>({
  spec_id: '',
  warehouse_id: '',
  quantity: 0,
  min_stock: 0,
  max_stock: 0
})

const inboundForm = ref({
  quantity: 0,
  remarks: ''
})

const outboundForm = ref({
  quantity: 0,
  remarks: ''
})

const stockStatuses = [
  { value: 'normal', label: '正常' },
  { value: 'low_stock', label: '库存不足' },
  { value: 'out_of_stock', label: '缺货' },
  { value: 'overstock', label: '超额库存' }
]

const columns = [
  { key: 'product_code', label: '商品编码', width: '120px' },
  { key: 'product_name', label: '商品名称' },
  { key: 'spec_code', label: '规格编码', width: '120px' },
  { key: 'packaging', label: '包装规格', width: '100px' },
  { key: 'warehouse_name', label: '仓库', width: '100px' },
  { key: 'quantity', label: '当前库存', width: '90px', align: 'right' as const },
  { key: 'inbound_count', label: '入库批次', width: '80px', align: 'center' as const },
  { key: 'outbound_count', label: '出库批次', width: '80px', align: 'center' as const },
  { key: 'status', label: '状态', width: '80px' }
]

const statusMap: Record<string, string> = {
  normal: '正常',
  low_stock: '不足',
  out_of_stock: '缺货',
  overstock: '超额'
}

const statusClassMap: Record<string, string> = {
  normal: 'normal',
  low_stock: 'warning',
  out_of_stock: 'danger',
  overstock: 'info'
}

const formatStatus = (status: string) => statusMap[status] || status
const getStatusClass = (status: string) => statusClassMap[status] || ''

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadStocks = async () => {
  loading.value = true
  try {
    const res = await stockApi.list({
      page: page.value,
      page_size: pageSize.value,
      warehouse_id: filterWarehouse.value || undefined,
      product_id: filterProductId.value || undefined,
      spec_id: filterSpecId.value || undefined,
      status: filterStatus.value || undefined
    })
    stocks.value = res.items.map((item: Stock) => ({
      ...item,
      status: formatStatus(item.status)
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载库存列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page: 1, page_size: 100 })
    warehouses.value = res.items
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  }
}

const loadStockDetail = async (stockId: string) => {
  detailLoading.value = true
  try {
    const res = await stockApi.getDetail(stockId)
    stockDetail.value = res
  } catch (error) {
    console.error('加载库存详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const updateStockInList = async (stockId: string) => {
  try {
    const updatedStock = await stockApi.getById(stockId)
    const index = stocks.value.findIndex(s => s.id === stockId)
    if (index !== -1) {
      stocks.value[index] = updatedStock
    }
    return updatedStock
  } catch (error) {
    console.error('更新库存数据失败:', error)
    return null
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadStocks()
}

const handleSearch = () => {
  page.value = 1
  loadStocks()
}

const searchFilterSpecs = async () => {
  if (!filterKeyword.value.trim()) {
    filterSearchResults.value = []
    return
  }
  try {
    const res = await productApi.searchSpecs(filterKeyword.value, 20)
    filterSearchResults.value = res.result || []
    showFilterDropdown.value = true
  } catch (error) {
    console.error('搜索规格失败:', error)
    filterSearchResults.value = []
  }
}

const selectFilterSpec = (spec: ProductSpec) => {
  selectedFilterSpec.value = spec
  filterSpecId.value = spec.id
  filterSpecName.value = `${spec.product_name || ''} ${spec.spec_code} ${spec.packaging || ''}`.trim()
  filterKeyword.value = filterSpecName.value
  showFilterDropdown.value = false
  handleSearch()
}

const clearFilterSelection = () => {
  selectedFilterSpec.value = null
  filterSpecId.value = ''
  filterSpecName.value = ''
  filterKeyword.value = ''
  filterSearchResults.value = []
  showFilterDropdown.value = false
}

const hideFilterDropdown = () => {
  setTimeout(() => { showFilterDropdown.value = false }, 200)
}

const handleFilterInput = () => {
  filterSpecId.value = ''
  selectedFilterSpec.value = null
  if (filterKeyword.value.length >= 2) {
    searchFilterSpecs()
  }
}

const hasActiveFilters = computed(() => {
  return !!(filterProductId.value || filterSpecId.value || filterWarehouse.value || filterStatus.value)
})

const resetFilters = () => {
  filterProductId.value = ''
  selectedProduct.value = null
  productKeyword.value = ''
  filterSpecId.value = ''
  filterSpecName.value = ''
  selectedFilterSpec.value = null
  if (!props.warehouseId) {
    filterWarehouse.value = ''
  }
  filterStatus.value = ''
  page.value = 1
  loadStocks()
}

const searchProducts = async () => {
  if (!productKeyword.value.trim()) {
    productSearchResults.value = []
    return
  }
  try {
    const res = await productApi.search(productKeyword.value, 20)
    productSearchResults.value = res.result || []
    showProductDropdown.value = true
  } catch (error) {
    console.error('搜索商品失败:', error)
    productSearchResults.value = []
  }
}

const selectProduct = (product: any) => {
  selectedProduct.value = product
  filterProductId.value = product.id
  productKeyword.value = product.name
  showProductDropdown.value = false
  filterSpecId.value = ''
  filterSpecName.value = ''
  filterKeyword.value = ''
  selectedFilterSpec.value = null
  handleSearch()
}

const clearProductSelection = () => {
  selectedProduct.value = null
  filterProductId.value = ''
  productKeyword.value = ''
  productSearchResults.value = []
  showProductDropdown.value = false
}

const handleProductInput = () => {
  filterProductId.value = ''
  selectedProduct.value = null
  if (productKeyword.value.length >= 2) {
    searchProducts()
  }
}

const hideProductDropdown = () => {
  setTimeout(() => { showProductDropdown.value = false }, 200)
}

const toggleExpand = async (stock: Stock) => {
  if (expandedStockId.value === stock.id) {
    expandedStockId.value = null
    stockDetail.value = null
  } else {
    expandedStockId.value = stock.id
    await loadStockDetail(stock.id)
  }
}

const searchSpecs = async () => {
  if (!specKeyword.value.trim()) {
    specSearchResults.value = []
    return
  }
  try {
    const res = await productApi.searchSpecs(specKeyword.value, 20)
    specSearchResults.value = res.result || []
    showSpecDropdown.value = true
  } catch (error) {
    console.error('搜索规格失败:', error)
    specSearchResults.value = []
  }
}

const selectSpec = (spec: ProductSpec) => {
  selectedSpec.value = spec
  stockForm.value.spec_id = spec.id
  specKeyword.value = `${spec.product_name} - ${spec.spec_code} (${spec.packaging || '-'})`
  showSpecDropdown.value = false
}

const clearSpecSelection = () => {
  selectedSpec.value = null
  stockForm.value.spec_id = ''
  specKeyword.value = ''
  specSearchResults.value = []
}

const hideSpecDropdown = () => {
  setTimeout(() => { showSpecDropdown.value = false }, 200)
}

const handleSpecInput = () => {
  stockForm.value.spec_id = ''
  selectedSpec.value = null
  searchSpecs()
}

const resetStockForm = () => {
  stockForm.value = {
    spec_id: '',
    warehouse_id: filterWarehouse.value || '',
    quantity: 0,
    min_stock: 0,
    max_stock: 0
  }
  editingStock.value = null
  selectedSpec.value = null
  specKeyword.value = ''
  specSearchResults.value = []
}

const openCreateStock = () => {
  resetStockForm()
  showStockModal.value = true
}

const _openEditStock = (stock: Stock) => {
  editingStock.value = stock
  selectedSpec.value = {
    id: stock.spec_id,
    spec_code: stock.spec?.spec_code || '',
    packaging: stock.spec?.packaging,
    sales_spec: stock.spec?.sales_spec,
    price: stock.spec?.price,
    product_id: stock.product?.product_id || stock.product_id,
    product_name: stock.product?.product_name,
    product_code: stock.product?.product_code
  }
  specKeyword.value = `${stock.product?.product_name} - ${stock.spec?.spec_code} (${stock.spec?.packaging || '-'})`
  stockForm.value = {
    spec_id: stock.spec_id,
    warehouse_id: stock.warehouse_id,
    quantity: stock.quantity,
    min_stock: stock.min_stock,
    max_stock: stock.max_stock
  }
  showStockModal.value = true
}

const openInboundModal = (stock: Stock) => {
  inboundTargetStock.value = stock
  inboundForm.value = { quantity: 0, remarks: '' }
  showInboundModal.value = true
}

const openOutboundModal = (stock: Stock) => {
  outboundTargetStock.value = stock
  outboundForm.value = { quantity: 0, remarks: '' }
  showOutboundModal.value = true
}

const openDetailModal = async (stock: Stock) => {
  await loadStockDetail(stock.id)
  showDetailModal.value = true
}

const handleSaveStock = async () => {
  if (!stockForm.value.spec_id) {
    window.showToast('请选择规格', 'warning')
    return
  }
  if (!stockForm.value.warehouse_id) {
    window.showToast('请选择仓库', 'warning')
    return
  }

  formLoading.value = true
  try {
    if (editingStock.value) {
      await stockApi.update(editingStock.value.id, stockForm.value)
      window.showToast('库存更新成功', 'success')
      showStockModal.value = false
      await updateStockInList(editingStock.value.id)
      if (expandedStockId.value === editingStock.value.id) {
        await loadStockDetail(editingStock.value.id)
      }
    } else {
      const res = await stockApi.create(stockForm.value)
      if (res.status === 'duplicate') {
        const existingId = res.result.existing_id
        const confirmInbound = confirm('该仓库中已存在此规格的库存记录，是否跳转到入库操作？')
        if (confirmInbound) {
          showStockModal.value = false
          const existingStock = stocks.value.find(s => s.id === existingId)
          if (existingStock) {
            await loadStockDetail(existingId)
            inboundTargetStock.value = stockDetail.value?.stock || existingStock
            showInboundModal.value = true
          }
        }
      } else {
        window.showToast('库存创建成功', 'success')
        showStockModal.value = false
        loadStocks()
      }
    }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleInbound = async () => {
  if (!inboundTargetStock.value) return
  if (inboundForm.value.quantity <= 0) {
    window.showToast('请输入有效的入库数量', 'warning')
    return
  }

  formLoading.value = true
  try {
    await stockApi.inbound(
      inboundTargetStock.value.id,
      inboundForm.value.quantity,
      inboundForm.value.remarks || undefined
    )
    window.showToast('入库成功', 'success')
    showInboundModal.value = false
    await updateStockInList(inboundTargetStock.value.id)
    if (expandedStockId.value === inboundTargetStock.value.id) {
      await loadStockDetail(inboundTargetStock.value.id)
    }
  } catch (error: any) {
    window.showToast(error.message || '入库失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleOutbound = async () => {
  if (!outboundTargetStock.value) return
  if (outboundForm.value.quantity <= 0) {
    window.showToast('请输入有效的出库数量', 'warning')
    return
  }
  if (outboundForm.value.quantity > outboundTargetStock.value.quantity) {
    window.showToast('出库数量不能超过当前库存', 'warning')
    return
  }

  formLoading.value = true
  try {
    await stockApi.outbound(
      outboundTargetStock.value.id,
      outboundForm.value.quantity,
      outboundForm.value.remarks || undefined
    )
    window.showToast('出库成功', 'success')
    showOutboundModal.value = false
    await updateStockInList(outboundTargetStock.value.id)
    if (expandedStockId.value === outboundTargetStock.value.id) {
      await loadStockDetail(outboundTargetStock.value.id)
    }
  } catch (error: any) {
    window.showToast(error.message || '出库失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const _handleDelete = async (stockId: string) => {
  if (!confirm('确定要删除该库存记录吗？此操作不可恢复。')) return

  try {
    await stockApi.delete(stockId)
    window.showToast('库存删除成功', 'success')
    const index = stocks.value.findIndex(s => s.id === stockId)
    if (index !== -1) {
      stocks.value.splice(index, 1)
    }
    if (expandedStockId.value === stockId) {
      expandedStockId.value = null
      stockDetail.value = null
    }
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

const handleBack = () => {
  emit('back')
}

watch(() => props.warehouseId, (newVal) => {
  if (newVal) {
    filterWarehouse.value = newVal
  }
}, { immediate: true })

onMounted(() => {
  loadStocks()
  if (!props.warehouseId) {
    loadWarehouses()
  }
})
</script>

<template>
  <div class="inventory-workspace">
    <div class="workspace-header">
      <div class="header-left">
        <button v-if="warehouseId" class="back-btn" @click="handleBack">
          <span class="back-icon">←</span> 返回仓库列表
        </button>
        <h2 class="workspace-title">
          {{ warehouseName ? `${warehouseName} - 库存管理` : '库存管理' }}
        </h2>
      </div>
      <button class="primary-btn" @click="openCreateStock">新增库存</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item" v-if="!warehouseId">
          <select class="filter-select" v-model="filterWarehouse" @change="handleSearch">
            <option value="">全部仓库</option>
            <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </div>
        <div class="filter-item product-filter">
          <div class="product-search-container small">
            <input
              type="text"
              v-model="productKeyword"
              placeholder="搜索商品..."
              @input="handleProductInput"
              @focus="showProductDropdown = productSearchResults.length > 0"
              @blur="hideProductDropdown"
            />
            <button v-if="selectedProduct" class="clear-btn" @click="clearProductSelection" type="button">×</button>
            <div class="product-dropdown" v-if="showProductDropdown">
              <div
                v-for="p in productSearchResults"
                :key="p.id"
                class="product-option"
                @mousedown="selectProduct(p)"
              >
                <span class="product-name">{{ p.name }}</span>
                <span class="product-code">{{ p.product_code }}</span>
              </div>
              <div v-if="productSearchResults.length === 0" class="no-results">
                未找到商品
              </div>
            </div>
          </div>
        </div>
        <div class="filter-item spec-filter">
          <div class="spec-search-container small">
            <input
              type="text"
              v-model="filterKeyword"
              placeholder="搜索规格..."
              @input="handleFilterInput"
              @focus="showFilterDropdown = filterSearchResults.length > 0"
              @blur="hideFilterDropdown"
            />
            <button v-if="selectedFilterSpec" class="clear-btn" @click="clearFilterSelection" type="button">×</button>
            <div class="spec-dropdown" v-if="showFilterDropdown">
              <div
                v-for="spec in filterSearchResults"
                :key="spec.id"
                class="spec-option"
                @mousedown="selectFilterSpec(spec)"
              >
                <span class="spec-product">{{ spec.product_name }}</span>
                <span class="spec-code">{{ spec.spec_code }}</span>
                <span class="spec-packaging">{{ spec.packaging || '-' }}</span>
              </div>
              <div v-if="filterSearchResults.length === 0" class="no-results">
                未找到规格
              </div>
            </div>
          </div>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in stockStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div class="filter-buttons">
          <button class="filter-btn" @click="handleSearch">搜索</button>
          <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
        </div>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 40px"></th>
            <th v-for="col in columns" :key="col.key" :style="{ width: col.width, textAlign: col.align || 'left' }">
              {{ col.label }}
            </th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr>
              <td :colspan="columns.length + 2" class="loading-cell">加载中...</td>
            </tr>
          </template>
          <template v-else-if="stocks.length === 0">
            <tr>
              <td :colspan="columns.length + 2" class="empty-cell">暂无数据</td>
            </tr>
          </template>
          <template v-else>
            <template v-for="stock in stocks" :key="stock.id">
              <tr :class="{ 'expanded-row': expandedStockId === stock.id }">
                <td class="expand-cell">
                  <button class="expand-btn" @click="toggleExpand(stock)">
                    {{ expandedStockId === stock.id ? '▼' : '▶' }}
                  </button>
                </td>
                <td>{{ stock.product?.product_code }}</td>
                <td>{{ stock.product?.product_name }}</td>
                <td>{{ stock.spec?.spec_code }}</td>
                <td>{{ stock.spec?.packaging || '-' }}</td>
                <td>{{ stock.warehouse?.warehouse_name }}</td>
                <td class="number-cell">{{ stock.quantity }}</td>
                <td class="center-cell">
                  <span class="batch-count" :class="{ 'has-data': (stock.inbound_outbound_summary?.inbound_count ?? 0) > 0 }">
                    {{ stock.inbound_outbound_summary?.inbound_count || 0 }}
                  </span>
                </td>
                <td class="center-cell">
                  <span class="batch-count" :class="{ 'has-data': (stock.inbound_outbound_summary?.outbound_count ?? 0) > 0 }">
                    {{ stock.inbound_outbound_summary?.outbound_count || 0 }}
                  </span>
                </td>
                <td>
                  <span class="status-tag" :class="getStatusClass(stock.status)">
                    {{ stock.status }}
                  </span>
                </td>
                <td>
                  <div class="action-buttons">
                    <button class="btn-link" @click="openInboundModal(stock)">入库</button>
                    <button class="btn-link" @click="openOutboundModal(stock)">出库</button>
                    <button class="btn-link" @click="openDetailModal(stock)">详情</button>
                    <button class="btn-link" @click="_openEditStock(stock)">编辑</button>
                    <button class="btn-link danger" @click="_handleDelete(stock.id)">删除</button>
                  </div>
                </td>
              </tr>
              <tr v-if="expandedStockId === stock.id" class="detail-row">
                <td :colspan="columns.length + 2">
                  <div class="stock-detail" v-if="stockDetail && detailLoading === false">
                    <div class="detail-summary">
                      <div class="summary-item">
                        <span class="summary-label">入库总计:</span>
                        <span class="summary-value success">{{ stockDetail.stock.inbound_outbound_summary?.total_inbound || 0 }}</span>
                      </div>
                      <div class="summary-item">
                        <span class="summary-label">出库总计:</span>
                        <span class="summary-value danger">{{ stockDetail.stock.inbound_outbound_summary?.total_outbound || 0 }}</span>
                      </div>
                    </div>
                    <div class="batches-container">
                      <div class="batches-section">
                        <h4 class="batches-title">入库批次记录</h4>
                        <div class="batches-list" v-if="stockDetail.inbound_batches.length > 0">
                          <div class="batch-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
                            <span class="batch-code">{{ batch.batch_code }}</span>
                            <span class="batch-qty success">+{{ batch.quantity }}</span>
                            <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
                            <span class="batch-operator">{{ batch.operator_name || '-' }}</span>
                            <span class="batch-remarks">{{ batch.remarks || '-' }}</span>
                          </div>
                        </div>
                        <div class="batches-empty" v-else>暂无入库记录</div>
                      </div>
                      <div class="batches-section">
                        <h4 class="batches-title">出库批次记录</h4>
                        <div class="batches-list" v-if="stockDetail.outbound_batches.length > 0">
                          <div class="batch-item" v-for="batch in stockDetail.outbound_batches" :key="batch.id">
                            <span class="batch-code">{{ batch.batch_code }}</span>
                            <span class="batch-qty danger">-{{ batch.quantity }}</span>
                            <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
                            <span class="batch-operator">{{ batch.operator_name || '-' }}</span>
                            <span class="batch-remarks">{{ batch.remarks || '-' }}</span>
                          </div>
                        </div>
                        <div class="batches-empty" v-else>暂无出库记录</div>
                      </div>
                    </div>
                  </div>
                  <div class="detail-loading" v-else-if="detailLoading">
                    加载中...
                  </div>
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="stocks.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showStockModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingStock ? '编辑库存' : '新增库存' }}</h3>
          <button class="modal-close" @click="showStockModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>商品规格 *</label>
            <div class="spec-search-container">
              <input
                type="text"
                v-model="specKeyword"
                placeholder="搜索商品规格..."
                @input="handleSpecInput"
                @focus="showSpecDropdown = specSearchResults.length > 0"
                @blur="hideSpecDropdown"
              />
              <button v-if="selectedSpec" class="clear-btn" @click="clearSpecSelection" type="button">×</button>
              <div class="spec-dropdown" v-if="showSpecDropdown">
                <div
                  v-for="spec in specSearchResults"
                  :key="spec.id"
                  class="spec-option"
                  @mousedown="selectSpec(spec)"
                >
                  <span class="spec-product">{{ spec.product_name }}</span>
                  <span class="spec-code">{{ spec.spec_code }}</span>
                  <span class="spec-packaging">{{ spec.packaging || '-' }}</span>
                </div>
                <div v-if="specSearchResults.length === 0" class="no-results">
                  未找到规格
                </div>
              </div>
            </div>
          </div>
          <div class="form-group" v-if="!warehouseId">
            <label>仓库 *</label>
            <select v-model="stockForm.warehouse_id">
              <option value="">请选择仓库</option>
              <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>初始库存数量</label>
              <input type="number" v-model="stockForm.quantity" min="0" placeholder="数量" />
            </div>
            <div class="form-group">
              <label>最低库存预警</label>
              <input type="number" v-model="stockForm.min_stock" min="0" placeholder="预警阈值" />
            </div>
          </div>
          <div class="form-group">
            <label>最高库存预警</label>
            <input type="number" v-model="stockForm.max_stock" min="0" placeholder="预警阈值" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showStockModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveStock" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showInboundModal">
      <div class="modal">
        <div class="modal-header">
          <h3>入库操作</h3>
          <button class="modal-close" @click="showInboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="operate-info" v-if="inboundTargetStock">
            <p>商品: {{ inboundTargetStock.product?.product_name }}</p>
            <p>规格: {{ inboundTargetStock.spec?.spec_code }} ({{ inboundTargetStock.spec?.packaging || '-' }})</p>
            <p>仓库: {{ inboundTargetStock.warehouse?.warehouse_name }}</p>
            <p>当前库存: <strong>{{ inboundTargetStock.quantity }}</strong></p>
          </div>
          <div class="form-group">
            <label>入库数量 *</label>
            <input type="number" v-model="inboundForm.quantity" min="1" placeholder="请输入入库数量" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="inboundForm.remarks" placeholder="可选填写备注信息" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showInboundModal = false">取消</button>
          <button class="btn-primary" @click="handleInbound" :disabled="formLoading">
            {{ formLoading ? '处理中...' : '确认入库' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showOutboundModal">
      <div class="modal">
        <div class="modal-header">
          <h3>出库操作</h3>
          <button class="modal-close" @click="showOutboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="operate-info" v-if="outboundTargetStock">
            <p>商品: {{ outboundTargetStock.product?.product_name }}</p>
            <p>规格: {{ outboundTargetStock.spec?.spec_code }} ({{ outboundTargetStock.spec?.packaging || '-' }})</p>
            <p>仓库: {{ outboundTargetStock.warehouse?.warehouse_name }}</p>
            <p>当前库存: <strong>{{ outboundTargetStock.quantity }}</strong></p>
          </div>
          <div class="form-group">
            <label>出库数量 *</label>
            <input type="number" v-model="outboundForm.quantity" min="1" :max="outboundTargetStock?.quantity || 0" placeholder="请输入出库数量" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="outboundForm.remarks" placeholder="可选填写备注信息" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showOutboundModal = false">取消</button>
          <button class="btn-primary" @click="handleOutbound" :disabled="formLoading">
            {{ formLoading ? '处理中...' : '确认出库' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDetailModal" @click.self="showDetailModal = false">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>库存详情</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="stockDetail">
          <div class="detail-header-info">
            <div class="info-row">
              <span class="info-label">商品:</span>
              <span class="info-value">{{ stockDetail.stock.product?.product_name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">规格:</span>
              <span class="info-value">{{ stockDetail.stock.spec?.spec_code }} ({{ stockDetail.stock.spec?.packaging || '-' }})</span>
            </div>
            <div class="info-row">
              <span class="info-label">仓库:</span>
              <span class="info-value">{{ stockDetail.stock.warehouse?.warehouse_name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前库存:</span>
              <span class="info-value highlight">{{ stockDetail.stock.quantity }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">状态:</span>
              <span class="status-tag" :class="getStatusClass(stockDetail.stock.status)">
                {{ formatStatus(stockDetail.stock.status) }}
              </span>
            </div>
          </div>
          <div class="detail-batches">
            <div class="detail-batch-section">
              <h4>入库记录 ({{ stockDetail.stock.inbound_outbound_summary?.total_inbound || 0 }})</h4>
              <div class="batch-scroll-list">
                <div class="batch-scroll-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
                  <span class="batch-code">{{ batch.batch_code }}</span>
                  <span class="batch-qty success">+{{ batch.quantity }}</span>
                  <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
                </div>
                <div v-if="stockDetail.inbound_batches.length === 0" class="batches-empty">暂无入库记录</div>
              </div>
            </div>
            <div class="detail-batch-section">
              <h4>出库记录 ({{ stockDetail.stock.inbound_outbound_summary?.total_outbound || 0 }})</h4>
              <div class="batch-scroll-list">
                <div class="batch-scroll-item" v-for="batch in stockDetail.outbound_batches" :key="batch.id">
                  <span class="batch-code">{{ batch.batch_code }}</span>
                  <span class="batch-qty danger">-{{ batch.quantity }}</span>
                  <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
                </div>
                <div v-if="stockDetail.outbound_batches.length === 0" class="batches-empty">暂无出库记录</div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-workspace {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.back-icon {
  font-size: 16px;
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

.filter-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.filter-item.product-filter,
.filter-item.spec-filter {
  position: relative;
  flex: 0 0 240px;
}

.product-search-container,
.spec-search-container {
  position: relative;
  width: 100%;
}

.product-search-container.small,
.spec-search-container.small {
  width: 100%;
}

.product-search-container.small input,
.spec-search-container.small input {
  width: 100%;
  padding: 6px 10px;
  padding-right: 24px;
  font-size: 13px;
  box-sizing: border-box;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.product-search-container.small input:focus,
.spec-search-container.small input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.product-search-container.small .clear-btn,
.spec-search-container.small .clear-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  font-size: 12px;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-dropdown,
.spec-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 320px;
  max-height: 240px;
  overflow-y: auto;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-hover);
  z-index: 100;
  margin-top: 4px;
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

.filter-input::placeholder {
  color: var(--text-muted);
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
  min-width: 100px;
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

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
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

.expanded-row {
  background-color: rgba(0, 120, 212, 0.05);
}

.expand-cell {
  width: 40px;
  text-align: center;
}

.expand-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  padding: 4px;
}

.expand-btn:hover {
  color: var(--accent-blue);
}

.number-cell {
  text-align: right !important;
  font-family: monospace;
}

.center-cell {
  text-align: center !important;
}

.batch-count {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  background-color: var(--bg-secondary);
  color: var(--text-muted);
}

.batch-count.has-data {
  background-color: rgba(0, 120, 212, 0.1);
  color: var(--accent-blue);
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.warning {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

.status-tag.danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.status-tag.info {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--accent-blue);
}

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

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.detail-row td {
  padding: 0;
  background-color: var(--bg-secondary);
}

.stock-detail {
  padding: 16px 20px;
}

.detail-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-label {
  font-size: 13px;
  color: var(--text-muted);
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
}

.summary-value.success {
  color: var(--accent-green);
}

.summary-value.danger {
  color: var(--accent-red);
}

.batches-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.batches-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 12px;
}

.batches-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.batches-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.batch-item {
  display: grid;
  grid-template-columns: 120px 60px 140px 80px 1fr;
  gap: 8px;
  align-items: center;
  padding: 8px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.batch-code {
  color: var(--accent-blue);
  font-weight: 500;
}

.batch-qty {
  font-weight: 600;
}

.batch-qty.success {
  color: var(--accent-green);
}

.batch-qty.danger {
  color: var(--accent-red);
}

.batch-time {
  color: var(--text-muted);
}

.batch-operator {
  color: var(--text-secondary);
}

.batch-remarks {
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batches-empty {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.detail-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
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
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.detail-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
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
  gap: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.operate-info {
  background-color: var(--bg-secondary);
  padding: 12px;
  border-radius: var(--radius-sm);
}

.operate-info p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--text-primary);
}

.operate-info strong {
  color: var(--accent-blue);
  font-size: 16px;
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.radio-label input {
  width: 16px;
  height: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
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
.form-group select {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.spec-search-container {
  position: relative;
}

.spec-search-container input {
  width: 100%;
  padding: 10px 12px;
  padding-right: 32px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.spec-search-container input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  background-color: var(--accent-red);
  color: white;
}

.spec-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 240px;
  overflow-y: auto;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-hover);
  z-index: 100;
  margin-top: 4px;
}

.spec-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.spec-option:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.product-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.product-option:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.product-name {
  font-size: 14px;
  color: var(--text-primary);
}

.product-code {
  font-size: 12px;
  color: var(--text-muted);
}

.spec-product {
  font-size: 14px;
  color: var(--text-primary);
}

.spec-code {
  font-size: 12px;
  color: var(--accent-blue);
}

.spec-packaging {
  font-size: 12px;
  color: var(--text-muted);
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.detail-header-info {
  background-color: var(--bg-secondary);
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 13px;
  color: var(--text-muted);
  min-width: 60px;
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
}

.info-value.highlight {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent-blue);
}

.detail-batches {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-batch-section h4 {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.batch-scroll-list {
  max-height: 250px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.batch-scroll-item {
  display: grid;
  grid-template-columns: 1fr 80px 140px;
  gap: 8px;
  align-items: center;
  padding: 10px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.batch-scroll-item .batch-code {
  color: var(--accent-blue);
  font-weight: 500;
}

.batch-scroll-item .batch-qty {
  font-weight: 600;
  text-align: right;
}

.batch-scroll-item .batch-time {
  color: var(--text-muted);
  text-align: right;
}

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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }

  .batches-container {
    grid-template-columns: 1fr;
  }

  .detail-batches {
    grid-template-columns: 1fr;
  }

  .batch-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
