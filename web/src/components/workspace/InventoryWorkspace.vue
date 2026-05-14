<script setup lang="ts">
defineOptions({ name: 'InventoryWorkspace' })

import { ref, computed, onMounted, watch } from 'vue'
import { stockApi, warehouseApi, productApi, inboundBatchApi, outboundBatchApi } from '../../services/api'

interface InboundBatch {
  id: string
  inventory_id: string
  batch_code: string
  quantity: number
  user_id?: string
  user_name?: string
  remarks?: string
  created_at: string
}

interface OutboundBatch {
  id: string
  inventory_id: string
  batch_code: string
  quantity: number
  user_id?: string
  user_name?: string
  remarks?: string
  created_at: string
}

interface StockCheckRecord {
  id: string
  batch_id: string
  stock_id: string
  warehouse_id: string
  product_id: string
  product_code: string
  product_name: string
  spec_id: string
  spec_code: string
  before_quantity: number
  check_quantity: number
  difference: number
  is_new_stock: boolean
  user_id: string
  user_name: string
  remarks?: string
  created_at: string
}

interface StockSpecInfo {
  id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price?: number
}

interface StockProductInfo {
  id: string
  product_code: string
  name: string
  brand_id?: string
  category_id?: string
  category_name?: string
}

interface StockWarehouseInfo {
  id: string
  warehouse_code: string
  name: string
}

interface Stock {
  id: string
  warehouse_id: string
  product_id: string
  product_code: string
  product_name: string
  spec_id: string
  spec_code: string
  quantity: number
  min_stock: number
  max_stock: number
  status: string
  product_info?: StockProductInfo
  spec_info?: StockSpecInfo
  warehouse_info?: StockWarehouseInfo
  created_at: string
  updated_at: string
}

interface ProductGroup {
  product_id: string
  warehouse_id: string
  specs: Stock[]
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
const productGroups = ref<ProductGroup[]>([])
const verticalTableData = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterWarehouse = ref(props.warehouseId || '')
const filterStatus = ref('')
const filterSpecId = ref('')
const filterSpecName = ref('')
const warehouses = ref<Warehouse[]>([])
const stockDetail = ref<(Stock & {
  inbound_batches?: InboundBatch[]
  outbound_batches?: OutboundBatch[]
}) | null>(null)
const detailLoading = ref(false)

const showBatchCheckModal = ref(false)
const showCheckResultModal = ref(false)
const showSingleCheckModal = ref(false)
const batchCheckForm = ref({
  warehouse_id: '',
  remarks: ''
})
const batchCheckFile = ref<File | null>(null)
const batchCheckLoading = ref(false)
const batchCheckResult = ref<{
  batch_code: string
  total_count: number
  success_count: number
  fail_count: number
  failed_items: Array<{ row: number; reason: string }>
} | null>(null)
const singleCheckStock = ref<Stock | null>(null)
const singleCheckForm = ref({
  check_quantity: 0,
  remarks: ''
})
const singleCheckLoading = ref(false)
const checkRecords = ref<StockCheckRecord[]>([])
const detailActiveTab = ref<'inbound' | 'outbound' | 'check'>('inbound')

const showInboundModal = ref(false)
const showOutboundModal = ref(false)
const showDetailModal = ref(false)
const inboundTargetStock = ref<Stock | null>(null)
const outboundTargetStock = ref<Stock | null>(null)
const formLoading = ref(false)

const filterKeyword = ref('')
const filterSearchResults = ref<ProductSpec[]>([])
const showFilterDropdown = ref(false)
const selectedFilterSpec = ref<ProductSpec | null>(null)

const filterSpecInput = computed({
  get: () => selectedFilterSpec.value ? filterSpecName.value : filterKeyword.value,
  set: (val) => { filterKeyword.value = val }
})

const productKeyword = ref('')
const productSearchResults = ref<any[]>([])
const showProductDropdown = ref(false)
const selectedProduct = ref<any | null>(null)
const filterProductId = ref('')

const specKeyword = ref('')
const specSearchResults = ref<ProductSpec[]>([])
const showSpecDropdown = ref(false)
const selectedSpec = ref<ProductSpec | null>(null)

const inboundForm = ref({
  warehouse_id: '',
  product_id: '',
  product_code: '',
  product_name: '',
  spec_id: '',
  spec_code: '',
  quantity: 0,
  remarks: ''
})

const outboundForm = ref({
  warehouse_id: '',
  product_id: '',
  product_code: '',
  product_name: '',
  spec_id: '',
  spec_code: '',
  quantity: 0,
  remarks: ''
})

const stockStatuses = [
  { value: 'normal', label: '正常' },
  { value: 'low_stock', label: '库存不足' },
  { value: 'out_of_stock', label: '缺货' },
  { value: 'overstock', label: '超额库存' }
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

const groupStocksByProduct = (stockList: Stock[]): ProductGroup[] => {
  const groupMap = new Map<string, ProductGroup>()
  for (const stock of stockList) {
    const key = `${stock.product_id}-${stock.warehouse_id}`
    if (!groupMap.has(key)) {
      groupMap.set(key, {
        product_id: stock.product_id,
        warehouse_id: stock.warehouse_id,
        specs: []
      })
    }
    groupMap.get(key)!.specs.push(stock)
  }
  return Array.from(groupMap.values())
}

const buildVerticalTableData = () => {
  const data: any[] = []
  for (const group of productGroups.value) {
    const specs = group.specs || []
    for (let i = 0; i < specs.length; i++) {
      const stock = specs[i]
      data.push({
        _id: `${group.product_id}_${group.warehouse_id}_${stock.spec_id}`,
        product_id: group.product_id,
        product_code: stock.product_code || stock.product_info?.product_code || '',
        product_name: stock.product_name || stock.product_info?.name || '',
        category: stock.product_info?.category_name || '',
        warehouse_id: group.warehouse_id,
        warehouse_name: stock.warehouse_info?.name || '',
        spec_id: stock.spec_id,
        spec_code: stock.spec_code || stock.spec_info?.spec_code || '',
        packaging: stock.spec_info?.packaging || '-',
        quantity: stock.quantity,
        min_stock: stock.min_stock,
        max_stock: stock.max_stock,
        status: stock.status,
        status_class: getStatusClass(stock.status),
        stockId: stock.id,
        isFirst: i === 0,
        rowspan: i === 0 ? specs.length : 0,
        group_rowspan: i === 0 ? specs.length : 0,
        specs_length: specs.length
      })
    }
  }
  verticalTableData.value = data
}

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
    const items = res.items ?? []
    stocks.value = items.map((item: Stock) => ({
      ...item,
      status: formatStatus(item.status)
    }))
    productGroups.value = groupStocksByProduct(stocks.value)
    total.value = res.total || 0
    buildVerticalTableData()
  } catch (error) {
    console.error('加载库存列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page: 1, page_size: 100 })
    warehouses.value = res.items ?? []
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  }
}

const loadStockDetail = async (stockId: string) => {
  detailLoading.value = true
  try {
    const [stockRes, inboundRes, outboundRes] = await Promise.all([
      stockApi.getById(stockId),
      inboundBatchApi.list({ stock_id: stockId, page_size: 50 }),
      outboundBatchApi.list({ stock_id: stockId, page_size: 50 })
    ])
    stockDetail.value = {
      ...stockRes,
      inbound_batches: inboundRes.items || [],
      outbound_batches: outboundRes.items || []
    }
    // 加载盘库记录
    await loadCheckRecords(stockId)
    detailActiveTab.value = 'inbound'
  } catch (error) {
    console.error('加载库存详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

const updateStockInList = async (stockId: string) => {
  try {
    const res = await stockApi.getById(stockId)
    const updatedStock = res
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

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
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
    filterSearchResults.value = res.items || []
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
  filterSearchResults.value = []
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
  filterKeyword.value = ''
  filterSearchResults.value = []
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
    const res = await productApi.list({
      page: 1,
      page_size: 20,
      keyword: productKeyword.value
    })
    productSearchResults.value = res.items || []
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

const searchSpecs = async () => {
  if (!specKeyword.value.trim()) {
    specSearchResults.value = []
    return
  }
  try {
    const res = await productApi.searchSpecs(specKeyword.value, 20)
    specSearchResults.value = res.items || []
    showSpecDropdown.value = true
  } catch (error) {
    console.error('搜索规格失败:', error)
    specSearchResults.value = []
  }
}

const hideSpecDropdown = () => {
  setTimeout(() => { showSpecDropdown.value = false }, 200)
}

const openCreateInbound = () => {
  inboundTargetStock.value = null
  inboundForm.value = {
    warehouse_id: filterWarehouse.value || '',
    product_id: '',
    product_code: '',
    product_name: '',
    spec_id: '',
    spec_code: '',
    quantity: 0,
    remarks: ''
  }
  selectedSpec.value = null
  specKeyword.value = ''
  specSearchResults.value = []
  showInboundModal.value = true
}

const openInboundModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  inboundTargetStock.value = stock
  inboundForm.value = {
    warehouse_id: stock.warehouse_id,
    product_id: stock.product_id,
    product_code: stock.product_code || stock.product_info?.product_code || '',
    product_name: stock.product_name || stock.product_info?.name || '',
    spec_id: stock.spec_id,
    spec_code: stock.spec_code || stock.spec_info?.spec_code || '',
    quantity: 0,
    remarks: ''
  }
  showInboundModal.value = true
}

const openOutboundModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  outboundTargetStock.value = stock
  outboundForm.value = {
    warehouse_id: stock.warehouse_id,
    product_id: stock.product_id,
    product_code: stock.product_code || stock.product_info?.product_code || '',
    product_name: stock.product_name || stock.product_info?.name || '',
    spec_id: stock.spec_id,
    spec_code: stock.spec_code || stock.spec_info?.spec_code || '',
    quantity: 0,
    remarks: ''
  }
  showOutboundModal.value = true
}

const openDetailModal = async (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  await loadStockDetail(stock.id)
  showDetailModal.value = true
}

const handleInbound = async () => {
  if (!inboundForm.value.warehouse_id) {
    window.showToast('请选择仓库', 'warning')
    return
  }
  if (!inboundForm.value.spec_id) {
    window.showToast('请选择规格', 'warning')
    return
  }
  if (inboundForm.value.quantity <= 0) {
    window.showToast('请输入有效的入库数量', 'warning')
    return
  }

  const userInfo = localStorage.getItem('user')
  const user = userInfo ? JSON.parse(userInfo) : { id: '', name: '未知用户' }

  formLoading.value = true
  try {
    await inboundBatchApi.create({
      warehouse_id: inboundForm.value.warehouse_id,
      product_id: inboundForm.value.product_id,
      product_code: inboundForm.value.product_code,
      product_name: inboundForm.value.product_name,
      spec_id: inboundForm.value.spec_id,
      spec_code: inboundForm.value.spec_code,
      stock_id: inboundTargetStock.value?.id || '',
      quantity: inboundForm.value.quantity,
      user_id: user.id,
      user_name: user.name || user.username || '未知用户'
    })
    window.showToast('入库成功', 'success')
    showInboundModal.value = false
    if (inboundTargetStock.value) {
      await updateStockInList(inboundTargetStock.value.id)
    }
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '入库失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleOutbound = async () => {
  if (!outboundTargetStock.value) {
    window.showToast('请先从列表选择库存记录进行出库', 'warning')
    return
  }
  if (outboundForm.value.quantity <= 0) {
    window.showToast('请输入有效的出库数量', 'warning')
    return
  }
  if (outboundForm.value.quantity > outboundTargetStock.value.quantity) {
    window.showToast('出库数量不能超过当前库存', 'warning')
    return
  }

  const userInfo = localStorage.getItem('user')
  const user = userInfo ? JSON.parse(userInfo) : { id: '', name: '未知用户' }

  formLoading.value = true
  try {
    await outboundBatchApi.create({
      warehouse_id: outboundForm.value.warehouse_id,
      product_id: outboundForm.value.product_id,
      product_code: outboundForm.value.product_code,
      product_name: outboundForm.value.product_name,
      spec_id: outboundForm.value.spec_id,
      spec_code: outboundForm.value.spec_code,
      stock_id: outboundTargetStock.value.id,
      quantity: outboundForm.value.quantity,
      user_id: user.id,
      user_name: user.name || user.username || '未知用户'
    })
    window.showToast('出库成功', 'success')
    showOutboundModal.value = false
    await updateStockInList(outboundTargetStock.value.id)
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '出库失败', 'error')
  } finally {
    formLoading.value = false
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

const openBatchCheckModal = () => {
  batchCheckForm.value = {
    warehouse_id: filterWarehouse.value || '',
    remarks: ''
  }
  batchCheckFile.value = null
  showBatchCheckModal.value = true
}

const handleBatchCheckFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    batchCheckFile.value = target.files[0]
  }
}

const handleDownloadTemplate = async () => {
  try {
    const { stockCheckApi } = await import('../../services/api')
    await stockCheckApi.downloadTemplate()
    window.showToast('模板下载成功', 'success')
  } catch (error: any) {
    window.showToast(error.message || '下载模板失败', 'error')
  }
}

const handleBatchCheck = async () => {
  if (!batchCheckForm.value.warehouse_id) {
    window.showToast('请选择仓库', 'warning')
    return
  }
  if (!batchCheckFile.value) {
    window.showToast('请上传盘库文件', 'warning')
    return
  }

  batchCheckLoading.value = true
  try {
    const { stockCheckApi } = await import('../../services/api')
    const result = await stockCheckApi.createBatch(
      batchCheckForm.value.warehouse_id,
      batchCheckFile.value,
      batchCheckForm.value.remarks
    )
    batchCheckResult.value = result.result || result
    showBatchCheckModal.value = false
    showCheckResultModal.value = true
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '批量盘库失败', 'error')
  } finally {
    batchCheckLoading.value = false
  }
}

const openSingleCheckModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  singleCheckStock.value = stock
  singleCheckForm.value = {
    check_quantity: stock.quantity,
    remarks: ''
  }
  showSingleCheckModal.value = true
}

const singleCheckDifference = computed(() => {
  if (!singleCheckStock.value) return 0
  return singleCheckForm.value.check_quantity - singleCheckStock.value.quantity
})

const handleSingleCheck = async () => {
  if (!singleCheckStock.value) return
  if (singleCheckForm.value.check_quantity < 0) {
    window.showToast('盘点数量不能为负数', 'warning')
    return
  }

  singleCheckLoading.value = true
  try {
    const { stockCheckApi } = await import('../../services/api')
    await stockCheckApi.createSingle({
      stock_id: singleCheckStock.value.id,
      check_quantity: singleCheckForm.value.check_quantity,
      remarks: singleCheckForm.value.remarks
    })
    window.showToast('盘库成功', 'success')
    showSingleCheckModal.value = false
    await updateStockInList(singleCheckStock.value.id)
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '盘库失败', 'error')
  } finally {
    singleCheckLoading.value = false
  }
}

const loadCheckRecords = async (stockId: string) => {
  try {
    const { stockCheckApi } = await import('../../services/api')
    const res = await stockCheckApi.listRecords({ stock_id: stockId, page_size: 50 })
    checkRecords.value = res.items || []
  } catch (error) {
    console.error('加载盘库记录失败:', error)
    checkRecords.value = []
  }
}

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
      <div class="header-actions">
        <button class="primary-btn" @click="openCreateInbound">新增入库</button>
        <button class="primary-btn" @click="openBatchCheckModal">批量盘库</button>
      </div>
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
              v-model="filterSpecInput"
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

    <div class="table-section" style="position: relative;">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="verticalTableData"
        :column-config="{ resizable: true }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column field="product_code" title="商品编码" min-width="100" class-name="col--center" />
        <vxe-column field="product_name" title="商品名称" min-width="150">
          <template #default="{ row }">
            <div class="product-name-info">
              <span class="product-name">{{ row.product_name }}</span>
              <span class="product-category" v-if="row.category">{{ row.category }}</span>
            </div>
          </template>
        </vxe-column>
        <vxe-column field="warehouse_name" title="仓库" min-width="80" class-name="col--center" />
        <vxe-column field="spec_code" title="规格编码" min-width="100" class-name="col--center" />
        <vxe-column field="packaging" title="包装规格" min-width="80" />
        <vxe-column field="quantity" title="当前库存" min-width="70" class-name="col--center">
          <template #default="{ row }">
            <span class="number-cell">{{ row.quantity }}</span>
          </template>
        </vxe-column>
        <vxe-column field="min_stock" title="最低库存" min-width="60" class-name="col--center" />
        <vxe-column field="max_stock" title="最高库存" min-width="60" class-name="col--center" />
        <vxe-column field="status" title="状态" min-width="60" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status_class">{{ row.status }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="200" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="openSingleCheckModal(row)">盘库</button>
              <button class="btn-link" @click="openInboundModal(row)">入库</button>
              <button class="btn-link" @click="openOutboundModal(row)">出库</button>
              <button class="btn-link" @click="openDetailModal(row)">详情</button>
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

    <div class="modal-overlay" v-if="showInboundModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ inboundTargetStock ? '入库操作' : '新增入库' }}</h3>
          <button class="modal-close" @click="showInboundModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="operate-info" v-if="inboundTargetStock">
            <p>商品: {{ inboundTargetStock.product_name || inboundTargetStock.product_info?.name }}</p>
            <p>规格: {{ inboundTargetStock.spec_code || inboundTargetStock.spec_info?.spec_code }} ({{ inboundTargetStock.spec_info?.packaging || '-' }})</p>
            <p>仓库: {{ inboundTargetStock.warehouse_info?.name }}</p>
            <p>当前库存: <strong>{{ inboundTargetStock.quantity }}</strong></p>
          </div>
          <template v-else>
            <div class="form-group">
              <label>仓库 *</label>
              <select v-model="inboundForm.warehouse_id">
                <option value="">请选择仓库</option>
                <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>商品规格 *</label>
              <div class="spec-search-container">
                <input
                  type="text"
                  v-model="specKeyword"
                  placeholder="搜索商品规格..."
                  @input="() => { if (specKeyword.length >= 2) searchSpecs() }"
                  @focus="() => { if (specKeyword.length >= 2) showSpecDropdown = true }"
                  @blur="hideSpecDropdown"
                />
                <div class="spec-dropdown" v-if="showSpecDropdown">
                  <div
                    v-for="spec in specSearchResults"
                    :key="spec.id"
                    class="spec-option"
                    @mousedown="() => {
                      selectedSpec = spec
                      inboundForm.spec_id = spec.id
                      inboundForm.spec_code = spec.spec_code
                      inboundForm.product_id = spec.product_id
                      inboundForm.product_name = spec.product_name || ''
                      inboundForm.product_code = spec.product_code || ''
                      specKeyword = `${spec.product_name || ''} - ${spec.spec_code} (${spec.packaging || '-'})`
                      showSpecDropdown = false
                    }"
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
          </template>
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
            <p>商品: {{ outboundTargetStock.product_name || outboundTargetStock.product_info?.name }}</p>
            <p>规格: {{ outboundTargetStock.spec_code || outboundTargetStock.spec_info?.spec_code }} ({{ outboundTargetStock.spec_info?.packaging || '-' }})</p>
            <p>仓库: {{ outboundTargetStock.warehouse_info?.name }}</p>
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
              <span class="info-value">{{ stockDetail.product_name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">规格:</span>
              <span class="info-value">{{ stockDetail.spec_code }} ({{ stockDetail.spec_info?.packaging || '-' }})</span>
            </div>
            <div class="info-row">
              <span class="info-label">仓库:</span>
              <span class="info-value">{{ stockDetail.warehouse_info?.name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前库存:</span>
              <span class="info-value highlight">{{ stockDetail.quantity }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">状态:</span>
              <span class="status-tag" :class="getStatusClass(stockDetail.status)">
                {{ formatStatus(stockDetail.status) }}
              </span>
            </div>
          </div>
          <div class="detail-tabs">
            <button
              class="detail-tab-btn"
              :class="{ active: detailActiveTab === 'inbound' }"
              @click="detailActiveTab = 'inbound'"
            >
              入库记录 ({{ stockDetail.inbound_batches?.length || 0 }})
            </button>
            <button
              class="detail-tab-btn"
              :class="{ active: detailActiveTab === 'outbound' }"
              @click="detailActiveTab = 'outbound'"
            >
              出库记录 ({{ stockDetail.outbound_batches?.length || 0 }})
            </button>
            <button
              class="detail-tab-btn"
              :class="{ active: detailActiveTab === 'check' }"
              @click="detailActiveTab = 'check'"
            >
              盘库记录 ({{ checkRecords.length }})
            </button>
          </div>
          <div class="detail-tab-content">
            <div v-show="detailActiveTab === 'inbound'" class="batch-scroll-list">
              <div class="batch-scroll-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
                <span class="batch-user">{{ batch.user_name || '-' }}</span>
                <span class="batch-qty success">+{{ batch.quantity }}</span>
                <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
              </div>
              <div v-if="!stockDetail.inbound_batches?.length" class="batches-empty">暂无入库记录</div>
            </div>
            <div v-show="detailActiveTab === 'outbound'" class="batch-scroll-list">
              <div class="batch-scroll-item" v-for="batch in stockDetail.outbound_batches" :key="batch.id">
                <span class="batch-user">{{ batch.user_name || '-' }}</span>
                <span class="batch-qty danger">-{{ batch.quantity }}</span>
                <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
              </div>
              <div v-if="!stockDetail.outbound_batches?.length" class="batches-empty">暂无出库记录</div>
            </div>
            <div v-show="detailActiveTab === 'check'" class="batch-scroll-list">
              <div class="batch-scroll-item check-record" v-for="record in checkRecords" :key="record.id">
                <span class="batch-user">{{ record.user_name || '-' }}</span>
                <span class="batch-qty" :class="record.difference >= 0 ? 'success' : 'danger'">
                  {{ record.difference >= 0 ? '+' : '' }}{{ record.difference }}
                </span>
                <span class="batch-time">{{ formatDate(record.created_at) }}</span>
              </div>
              <div v-if="!checkRecords.length" class="batches-empty">暂无盘库记录</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 批量盘库弹窗 -->
    <div class="modal-overlay" v-if="showBatchCheckModal" @click.self="showBatchCheckModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>批量盘库</h3>
          <button class="modal-close" @click="showBatchCheckModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>仓库 *</label>
            <select v-model="batchCheckForm.warehouse_id">
              <option value="">请选择仓库</option>
              <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>盘库文件 *</label>
            <div class="file-upload-area">
              <input
                type="file"
                accept=".xlsx,.xls"
                @change="handleBatchCheckFileChange"
                ref="batchCheckFileInput"
              />
              <div class="file-upload-hint">
                <span v-if="batchCheckFile">{{ batchCheckFile.name }}</span>
                <span v-else>点击上传或拖拽文件到此处（支持 .xlsx, .xls）</span>
              </div>
            </div>
            <button class="btn-link template-btn" @click="handleDownloadTemplate" type="button">
              下载盘库模板
            </button>
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="batchCheckForm.remarks" placeholder="可选填写备注信息" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showBatchCheckModal = false">取消</button>
          <button class="btn-primary" @click="handleBatchCheck" :disabled="batchCheckLoading">
            {{ batchCheckLoading ? '处理中...' : '开始盘库' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 盘库结果弹窗 -->
    <div class="modal-overlay" v-if="showCheckResultModal" @click.self="showCheckResultModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>盘库结果</h3>
          <button class="modal-close" @click="showCheckResultModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="batchCheckResult">
          <div class="result-summary">
            <div class="result-item">
              <span class="result-label">批次编号:</span>
              <span class="result-value">{{ batchCheckResult.batch_code }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">总记录数:</span>
              <span class="result-value">{{ batchCheckResult.total_count }}</span>
            </div>
            <div class="result-item success">
              <span class="result-label">成功:</span>
              <span class="result-value">{{ batchCheckResult.success_count }}</span>
            </div>
            <div class="result-item" :class="{ danger: batchCheckResult.fail_count > 0 }">
              <span class="result-label">失败:</span>
              <span class="result-value">{{ batchCheckResult.fail_count }}</span>
            </div>
          </div>
          <div v-if="batchCheckResult.failed_items && batchCheckResult.failed_items.length > 0" class="failed-items">
            <h4>失败记录:</h4>
            <div class="failed-list">
              <div class="failed-item" v-for="(item, index) in batchCheckResult.failed_items" :key="index">
                <span class="failed-row">第 {{ item.row }} 行</span>
                <span class="failed-reason">{{ item.reason }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCheckResultModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 单个盘库弹窗 -->
    <div class="modal-overlay" v-if="showSingleCheckModal" @click.self="showSingleCheckModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>盘库操作</h3>
          <button class="modal-close" @click="showSingleCheckModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="singleCheckStock">
          <div class="operate-info">
            <p>商品: {{ singleCheckStock.product_name || singleCheckStock.product_info?.name }}</p>
            <p>规格: {{ singleCheckStock.spec_code || singleCheckStock.spec_info?.spec_code }} ({{ singleCheckStock.spec_info?.packaging || '-' }})</p>
            <p>仓库: {{ singleCheckStock.warehouse_info?.name }}</p>
            <p>当前库存: <strong>{{ singleCheckStock.quantity }}</strong></p>
          </div>
          <div class="form-group">
            <label>盘点数量 *</label>
            <input type="number" v-model="singleCheckForm.check_quantity" min="0" placeholder="请输入盘点数量" />
          </div>
          <div class="form-group">
            <label>差异</label>
            <div class="difference-display" :class="singleCheckDifference >= 0 ? 'positive' : 'negative'">
              {{ singleCheckDifference >= 0 ? '+' : '' }}{{ singleCheckDifference }}
            </div>
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="singleCheckForm.remarks" placeholder="可选填写备注信息" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showSingleCheckModal = false">取消</button>
          <button class="btn-primary" @click="handleSingleCheck" :disabled="singleCheckLoading">
            {{ singleCheckLoading ? '处理中...' : '确认盘库' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  margin: 0;
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
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
  padding: 12px 16px;
  box-shadow: var(--shadow-card);
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

.product-name-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.product-name {
  color: var(--text-primary);
  font-weight: 500;
}

.product-category {
  font-size: 11px;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 2px;
}

.number-cell {
  font-family: monospace;
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

.action-btns {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
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

.table-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

[data-theme="dark"] .table-loading-overlay {
  background-color: rgba(0, 0, 0, 0.8);
}

.table-loading-content {
  padding: 20px 40px;
  background-color: var(--bg-card);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: var(--text-primary);
  font-size: 14px;
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

.batch-scroll-item .batch-user {
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

  .detail-batches {
    grid-template-columns: 1fr;
  }
}

.detail-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-tab-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.detail-tab-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.detail-tab-btn.active {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.detail-tab-content {
  min-height: 200px;
}

.file-upload-area {
  position: relative;
  padding: 20px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  text-align: center;
}

.file-upload-area input[type="file"] {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-upload-hint {
  color: var(--text-muted);
  font-size: 13px;
}

.file-upload-hint span {
  color: var(--accent-blue);
}

.template-btn {
  margin-top: 8px;
  font-size: 12px;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 16px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-label {
  font-size: 13px;
  color: var(--text-muted);
}

.result-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.result-item.success .result-value {
  color: var(--accent-green);
}

.result-item.danger .result-value {
  color: var(--accent-red);
}

.failed-items {
  margin-top: 16px;
}

.failed-items h4 {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.failed-list {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.failed-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
}

.failed-row {
  font-size: 13px;
  color: var(--accent-red);
  font-weight: 500;
}

.failed-reason {
  font-size: 12px;
  color: var(--text-muted);
}

.difference-display {
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-size: 18px;
  font-weight: 600;
  text-align: center;
}

.difference-display.positive {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.difference-display.negative {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.batch-scroll-item.check-record {
  grid-template-columns: 1fr 80px 140px;
}
</style>
