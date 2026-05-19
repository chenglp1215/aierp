<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { purchaseOrderApi, productApi, warehouseApi, brandApi, supplierApi } from '../../services/api'

const emit = defineEmits<{
  navigate: [id: string, extra?: Record<string, any>]
}>()

// ============ 导航方法 ============
const navigateToDetail = (purchaseNo: string) => {
  emit('navigate', 'purchase-order-detail', { purchaseNo })
}

// ============ 接口定义 ============

interface PurchaseOrderItem {
  row_no: number
  product_id: string
  spec_id?: string
  brand_id?: string
  brand_name?: string
  purchase_qty: number
  in_qty: number
  return_qty: number
  purchase_price: number
  discount: number
  amt: number
  shipping_method?: string
  source_sale_row_no?: number
  warehouse_id?: string
  product_name?: string
  product_code?: string
  spec_code?: string
  warehouse_name?: string
}

interface ReceiveInfo {
  type?: string
  warehouse_id?: string
  warehouse_name?: string
  customer_addr?: string
  province?: string
  city?: string
  contact_person?: string
  contact_tel?: string
}

interface PurchaseStatusInfo {
  purchase_status: string
  in_status: string
  pay_status: string
}

interface PurchaseOrder {
  id: string
  purchase_no: string
  purchase_type: string
  source_sale_order_no?: string
  brand_id?: string
  brand_name?: string
  supplier_id: string
  supplier_name?: string
  purchase_user_id?: string
  receive_info?: ReceiveInfo
  expect_arrive_date?: string
  settle_type: string
  total_amt: number
  freight_amt: number
  status: PurchaseStatusInfo
  creator_id?: string
  create_time?: string
  remark?: string
  items: PurchaseOrderItem[]
}

interface StatusFlowRecord {
  id: string
  order_no: string
  field: string
  old_value?: string
  new_value: string
  operator: string
  operate_time: string
  remark?: string
}

interface Warehouse {
  id: string
  name: string
}

interface Brand {
  id: string
  name: string
}

interface SupplierBrand {
  brand_id: string
  discount: number
  is_priority: boolean
}

interface Supplier {
  id: string
  name: string
  supplied_brands?: SupplierBrand[]
}

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
  full: { label: '全部结清', class: 'full' }
}

const purchaseTypeMap: Record<string, { label: string; class: string }> = {
  direct: { label: '直运采购', class: 'direct' },
  warehouse: { label: '仓库采购', class: 'warehouse' }
}

const settleTypeOptions = ['月结', '货到付款', '款到发货']
const purchaseTypeOptions = [
  { value: 'direct', label: '直运采购' },
  { value: 'warehouse', label: '仓库采购' }
]
const purchaseStatusOptions = Object.entries(purchaseStatusMap).map(([value, item]) => ({ value, label: item.label }))

// ============ 列表状态 ============

const loading = ref(false)
const orders = ref<PurchaseOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterPurchaseNo = ref('')
const filterStatus = ref('')
const filterPurchaseType = ref('')
const filterBrandId = ref('')
const filterSupplierId = ref('')

// ============ 弹窗状态 ============

const showPurchaseModal = ref(false)
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const showAuditConfirm = ref(false)
const showCloseConfirm = ref(false)
const showCancelConfirm = ref(false)
const showRecallConfirm = ref(false)
const showReauditConfirm = ref(false)
const showVoidConfirm = ref(false)

// ============ 选中状态 ============

const editingOrder = ref<PurchaseOrder | null>(null)
const selectedOrder = ref<PurchaseOrder | null>(null)
const selectedOrderFlows = ref<StatusFlowRecord[]>([])
const deleteTargetPurchaseNo = ref('')
const actionTargetPurchaseNo = ref('')

// ============ 加载状态 ============

const formLoading = ref(false)
const deleteLoading = ref(false)
const actionLoading = ref(false)
const detailLoading = ref(false)

// ============ 下拉数据 ============

const brandList = ref<Brand[]>([])
const warehouseList = ref<Warehouse[]>([])
const specSearchResults = ref<any[]>([])
const supplierList = ref<Supplier[]>([])

// ============ 表单数据 ============

const form = ref<{
  purchase_type: string
  supplier_id: string
  brand_id: string
  purchase_user_id: string
  settle_type: string
  expect_arrive_date: string
  freight_amt: number
  remark: string
  receive_info: {
    type: string
    warehouse_id: string
    customer_addr: string
    province: string
    city: string
    contact_person: string
    contact_tel: string
  }
  items: PurchaseOrderItem[]
}>({
  purchase_type: 'direct',
  supplier_id: '',
  brand_id: '',
  purchase_user_id: '',
  settle_type: '月结',
  expect_arrive_date: '',
  freight_amt: 0,
  remark: '',
  receive_info: {
    type: 'customer',
    warehouse_id: '',
    customer_addr: '',
    province: '',
    city: '',
    contact_person: '',
    contact_tel: ''
  },
  items: []
})

// ============ 商品搜索 ============

const showProductTree = ref(false)
const productSearchKeyword = ref('')
let productSearchTimer: ReturnType<typeof setTimeout> | null = null

// ============ 计算属性 ============

const hasActiveFilters = computed(() => {
  return filterPurchaseNo.value || filterStatus.value || filterPurchaseType.value || filterBrandId.value || filterSupplierId.value
})

const totalAmount = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (item.amt || 0), 0)
})

const totalTaxAmt = computed(() => {
  return Math.round(totalAmount.value * 0.13 * 100) / 100
})

const totalTaxInclAmount = computed(() => {
  return Math.round((totalAmount.value + totalTaxAmt.value) * 100) / 100
})

const isFormDisabled = computed(() => {
  // 采购中、采购完成、已关闭、已取消状态不可编辑
  const status = editingOrder.value?.status?.purchase_status
  return status === 'purchasing' || status === 'completed' || status === 'closed' || status === 'cancelled'
})

// ============ 方法 ============

const loadOrders = async () => {
  loading.value = true
  try {
    const res = await purchaseOrderApi.list({
      page: page.value,
      page_size: pageSize.value,
      purchase_status: filterStatus.value || undefined,
      purchase_type: filterPurchaseType.value || undefined,
      brand_id: filterBrandId.value || undefined,
      supplier_id: filterSupplierId.value || undefined,
      purchase_no: filterPurchaseNo.value || undefined,
    })
    // 数据在 result 字段里
    const data = res?.result || res
    orders.value = data?.items || []
    total.value = data?.total || 0
  } catch (error: any) {
    window.showToast(error.message || '加载采购单列表失败', 'error')
  } finally {
    loading.value = false
  }
}

const loadBrands = async () => {
  try {
    const res = await brandApi.getAll()
    brandList.value = res || []
  } catch (error) {
    console.error('加载品牌列表失败:', error)
  }
}

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page: 1, page_size: 100 })
    warehouseList.value = res?.items || []
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  }
}

const loadSuppliersByBrand = async (brandId: string) => {
  if (!brandId) {
    supplierList.value = []
    return
  }
  try {
    const res = await supplierApi.getByBrandId(brandId)
    supplierList.value = res || []
    // 如果只有一个供应商，自动选择
    if (supplierList.value.length === 1) {
      form.value.supplier_id = supplierList.value[0].id
    }
  } catch (error) {
    console.error('加载供应商列表失败:', error)
    supplierList.value = []
  }
}

const getSupplierDiscount = (supplier: Supplier, brandId: string) => {
  if (!supplier.supplied_brands || supplier.supplied_brands.length === 0) {
    return 100
  }
  const brandDiscount = supplier.supplied_brands.find((sb: SupplierBrand) => sb.brand_id === brandId)
  return brandDiscount ? Math.round(brandDiscount.discount * 100) : 100
}

// 监听品牌变化，加载供应商列表
watch(() => form.value.brand_id, (newBrandId) => {
  loadSuppliersByBrand(newBrandId)
})

// 监听供应商变化，自动更新商品明细中的采购价格
watch(() => form.value.supplier_id, (newSupplierId) => {
  if (!newSupplierId || supplierList.value.length === 0) return

  // 找到选中的供应商
  const selectedSupplier = supplierList.value.find(s => s.id === newSupplierId)
  if (!selectedSupplier) return

  // 找到该供应商对当前品牌的折扣
  const brandDiscount = selectedSupplier.supplied_brands?.find(
    (sb: SupplierBrand) => sb.brand_id === form.value.brand_id
  )
  const discount = brandDiscount?.discount ?? 1.0

  // 更新每个商品的采购价格和金额
  // 注意：这里基于当前价格进行相对调整
  // 如果需要更精确的价格计算，需要后端提供商品规格的原始价格接口
  form.value.items.forEach(item => {
    if (item.purchase_price > 0) {
      // 基于当前价格应用新折扣（相对调整）
      item.purchase_price = Math.round(item.purchase_price * discount * 100) / 100
      item.amt = Math.round(item.purchase_qty * item.purchase_price * item.discount * 100) / 100
    }
  })
})

const handleSearch = () => {
  page.value = 1
  loadOrders()
}

const handlePageChange = ({ currentPage, pageSize: newSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newSize
  loadOrders()
}

const resetFilters = () => {
  filterPurchaseNo.value = ''
  filterStatus.value = ''
  filterPurchaseType.value = ''
  filterBrandId.value = ''
  filterSupplierId.value = ''
  page.value = 1
  loadOrders()
}

const openCreateOrder = () => {
  editingOrder.value = null
  form.value = {
    purchase_type: 'direct',
    supplier_id: '',
    brand_id: '',
    purchase_user_id: '',
    settle_type: '月结',
    expect_arrive_date: '',
    freight_amt: 0,
    remark: '',
    receive_info: {
      type: 'customer',
      warehouse_id: '',
      customer_addr: '',
      province: '',
      city: '',
      contact_person: '',
      contact_tel: ''
    },
    items: []
  }
  showPurchaseModal.value = true
}

const openEditOrder = (order: PurchaseOrder) => {
  editingOrder.value = order
  form.value = {
    purchase_type: order.purchase_type,
    supplier_id: order.supplier_id,
    brand_id: order.brand_id || '',
    purchase_user_id: order.purchase_user_id || '',
    settle_type: order.settle_type,
    expect_arrive_date: order.expect_arrive_date || '',
    freight_amt: order.freight_amt || 0,
    remark: order.remark || '',
    receive_info: {
      type: order.receive_info?.type || 'customer',
      warehouse_id: order.receive_info?.warehouse_id || '',
      customer_addr: order.receive_info?.customer_addr || '',
      province: order.receive_info?.province || '',
      city: order.receive_info?.city || '',
      contact_person: order.receive_info?.contact_person || '',
      contact_tel: order.receive_info?.contact_tel || ''
    },
    items: (order.items || []).map(item => ({ ...item }))
  }
  // 加载供应商列表
  if (order.brand_id) {
    loadSuppliersByBrand(order.brand_id)
  }
  showPurchaseModal.value = true
}


const handleSaveOrder = async () => {
  if (isFormDisabled.value) {
    window.showToast('已审核的采购单不可编辑', 'warning')
    return
  }
  if (!form.value.supplier_id) {
    window.showToast('请选择供应商', 'warning')
    return
  }
  if (form.value.items.length === 0) {
    window.showToast('请添加商品明细', 'warning')
    return
  }
  formLoading.value = true
  try {
    const data = {
      ...form.value,
      items: form.value.items.map((item, idx) => ({
        ...item,
        row_no: idx + 1
      }))
    }
    if (editingOrder.value) {
      await purchaseOrderApi.update(editingOrder.value.purchase_no, data)
      window.showToast('采购单更新成功', 'success')
    } else {
      await purchaseOrderApi.create(data)
      window.showToast('采购单创建成功', 'success')
    }
    showPurchaseModal.value = false
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '保存失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = (order: PurchaseOrder) => {
  deleteTargetPurchaseNo.value = order.purchase_no
  showDeleteConfirm.value = true
}

const handleDeleteOrder = async () => {
  deleteLoading.value = true
  try {
    await purchaseOrderApi.delete(deleteTargetPurchaseNo.value)
    window.showToast('采购单删除成功', 'success')
    showDeleteConfirm.value = false
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const confirmAudit = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showAuditConfirm.value = true
}

const handleAuditOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.approve(actionTargetPurchaseNo.value)
    window.showToast('采购单审核成功', 'success')
    showAuditConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      navigateToDetail(selectedOrder.value.purchase_no)
    }
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmClose = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showCloseConfirm.value = true
}

const handleCloseOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.close(actionTargetPurchaseNo.value)
    window.showToast('采购单已结案', 'success')
    showCloseConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      navigateToDetail(selectedOrder.value.purchase_no)
    }
  } catch (error: any) {
    window.showToast(error.message || '结案失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmCancel = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showCancelConfirm.value = true
}

const handleCancelOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.void(actionTargetPurchaseNo.value)
    window.showToast('采购单已作废', 'success')
    showCancelConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      navigateToDetail(selectedOrder.value.purchase_no)
    }
  } catch (error: any) {
    window.showToast(error.message || '作废失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmRecall = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showRecallConfirm.value = true
}

const handleRecallOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.recall(actionTargetPurchaseNo.value)
    window.showToast('采购单撤回成功', 'success')
    showRecallConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      showDetailModal.value = false
      selectedOrder.value = null
    }
  } catch (error: any) {
    window.showToast(error.message || '撤回失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmReaudit = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showReauditConfirm.value = true
}

const handleReauditOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.reaudit(actionTargetPurchaseNo.value)
    window.showToast('采购单重审成功（已撤回到草稿）', 'success')
    showReauditConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      navigateToDetail(selectedOrder.value.purchase_no)
    }
  } catch (error: any) {
    window.showToast(error.message || '重审失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmVoid = (order: PurchaseOrder) => {
  actionTargetPurchaseNo.value = order.purchase_no
  showVoidConfirm.value = true
}

const handleVoidOrder = async () => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.void(actionTargetPurchaseNo.value)
    window.showToast('采购单已作废', 'success')
    showVoidConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.purchase_no === actionTargetPurchaseNo.value) {
      navigateToDetail(selectedOrder.value.purchase_no)
    }
  } catch (error: any) {
    window.showToast(error.message || '作废失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

// ============ 新状态操作方法 ============

const confirmStartPurchase = (order: PurchaseOrder) => {
  if (!confirm(`确定要开始采购采购单 ${order.purchase_no} 吗？`)) return
  handleStartPurchase(order.purchase_no)
}

const handleStartPurchase = async (purchaseNo: string) => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.startPurchase(purchaseNo)
    window.showToast('开始采购成功', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmComplete = (order: PurchaseOrder) => {
  if (!confirm(`确定采购单 ${order.purchase_no} 已完成采购吗？`)) return
  handleComplete(order.purchase_no)
}

const handleComplete = async (purchaseNo: string) => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.complete(purchaseNo)
    window.showToast('采购完成', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const confirmRollback = (order: PurchaseOrder) => {
  const targetStatus = order.status?.purchase_status === 'ready_purchase' ? '待审核' : '准备采购'
  if (!confirm(`确定要回退到${targetStatus}状态吗？`)) return
  handleRollback(order.purchase_no)
}

const handleRollback = async (purchaseNo: string) => {
  actionLoading.value = true
  try {
    await purchaseOrderApi.rollback(purchaseNo)
    window.showToast('状态回退成功', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '回退失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

// ============ 商品明细操作 ============

const addOrderItem = () => {
  const rowNo = form.value.items.length + 1
  form.value.items.push({
    row_no: rowNo,
    product_id: '',
    spec_id: '',
    brand_id: form.value.brand_id,
    purchase_qty: 1,
    in_qty: 0,
    return_qty: 0,
    purchase_price: 0,
    discount: 1.0,
    amt: 0
  })
}

const removeOrderItem = (index: number) => {
  form.value.items.splice(index, 1)
  form.value.items.forEach((item, idx) => {
    item.row_no = idx + 1
  })
}

const updateItemAmount = (index: number) => {
  const item = form.value.items[index]
  item.amt = Math.round(item.purchase_qty * item.purchase_price * item.discount * 100) / 100
}

// ============ 商品搜索 ============

const handleProductSearch = (keyword: string) => {
  if (productSearchTimer) clearTimeout(productSearchTimer)
  if (!keyword || keyword.trim() === '') {
    specSearchResults.value = []
    return
  }
  productSearchTimer = setTimeout(async () => {
    try {
      const res = await productApi.searchSpecs(keyword, 20)
      specSearchResults.value = res || []
    } catch (error) {
      console.error('搜索商品失败:', error)
    }
  }, 300)
}

const selectSpecFromSearch = (spec: any) => {
  const lastIdx = form.value.items.length - 1
  const targetIdx = lastIdx >= 0 && !form.value.items[lastIdx].product_id ? lastIdx : -1
  const newItem: PurchaseOrderItem = {
    row_no: targetIdx >= 0 ? form.value.items[lastIdx].row_no : form.value.items.length + 1,
    product_id: spec.product_id || '',
    spec_id: spec.id,
    brand_id: spec.brand_id || '',
    purchase_qty: 1,
    in_qty: 0,
    return_qty: 0,
    purchase_price: spec.price || 0,
    discount: 1.0,
    amt: spec.price || 0,
    product_name: spec.product_name || '',
    product_code: spec.product_code || '',
    spec_code: spec.spec_code || ''
  }
  if (targetIdx >= 0) {
    form.value.items[lastIdx] = newItem
  } else {
    form.value.items.push(newItem)
  }
  specSearchResults.value = []
  productSearchKeyword.value = ''
  showProductTree.value = false
}

const handleclickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.search-select')) {
    showProductTree.value = false
  }
}

// ============ 格式化 ============

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const formatAmount = (amount?: number) => {
  if (amount === undefined || amount === null) return '0.00'
  return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getPurchaseStatusInfo = (status: string) => purchaseStatusMap[status] || { label: status, class: '' }
const getInStatusInfo = (status: string) => inStatusMap[status] || { label: status, class: '' }
const getPayStatusInfo = (status: string) => payStatusMap[status] || { label: status, class: '' }
const getPurchaseTypeInfo = (type: string) => purchaseTypeMap[type] || { label: type, class: '' }

const getFlowFieldName = (field: string) => {
  const map: Record<string, string> = {
    purchase_status: '采购状态',
    in_status: '入库状态',
    pay_status: '付款状态'
  }
  return map[field] || field
}

// ============ 生命周期 ============

onMounted(async () => {
  loadOrders()
  loadBrands()
  loadWarehouses()
  document.addEventListener('click', handleclickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleclickOutside)
})
</script>

<template>
  <div class="purchase-order-workspace">
    <!-- 列表头部 -->
    <div class="workspace-header">
      <h2 class="workspace-title">采购单管理</h2>
      <button class="primary-btn" @click="openCreateOrder">新建采购单</button>
    </div>

    <!-- 筛选区 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item" style="flex: 1; min-width: 200px;">
          <input
            v-model="filterPurchaseNo"
            class="filter-input"
            placeholder="采购单号"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select v-model="filterStatus" class="filter-select">
            <option value="">全部状态</option>
            <option v-for="opt in purchaseStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select v-model="filterPurchaseType" class="filter-select">
            <option value="">全部类型</option>
            <option v-for="opt in purchaseTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select v-model="filterBrandId" class="filter-select">
            <option value="">全部品牌</option>
            <option v-for="brand in brandList" :key="brand.id" :value="brand.id">{{ brand.name }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button v-if="hasActiveFilters" class="filter-btn reset-btn" @click="resetFilters">重置</button>
      </div>
    </div>

    <!-- 表格区 -->
    <div class="table-section">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="orders"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: ({ rowIndex }) => rowIndex + 1 + (page - 1) * pageSize }"
        :row-config="{ isHover: true }"
        :expand-config="{}"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column type="expand" width="50" class-name="col--center">
          <template #content="{ row }">
            <div class="expand-items-panel">
              <table class="expand-items-table">
                <thead>
                  <tr>
                    <th>行号</th>
                    <th>商品名称</th>
                    <th>规格编码</th>
                    <th>采购数量</th>
                    <th>采购单价</th>
                    <th>折扣</th>
                    <th>金额</th>
                    <th>已入库</th>
                    <th>发货方式</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in row.items" :key="item.row_no">
                    <td>{{ item.row_no }}</td>
                    <td>{{ item.product_name || item.product_id }}</td>
                    <td>{{ item.spec_code || '-' }}</td>
                    <td>{{ item.purchase_qty }}</td>
                    <td>{{ formatAmount(item.purchase_price) }}</td>
                    <td>{{ item.discount }}</td>
                    <td>{{ formatAmount(item.amt) }}</td>
                    <td>{{ item.in_qty }}</td>
                    <td>{{ item.shipping_method || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </vxe-column>
        <vxe-column field="purchase_no" title="采购单号" width="160" fixed="left" class-name="col--center">
          <template #default="{ row }">
            <span class="order-link" @click="navigateToDetail(row.purchase_no)">{{ row.purchase_no }}</span>
          </template>
        </vxe-column>
        <vxe-column field="purchase_type" title="采购类型" width="110" class-name="col--center">
          <template #default="{ row }">
            <span class="type-tag" :class="getPurchaseTypeInfo(row.purchase_type).class">
              {{ getPurchaseTypeInfo(row.purchase_type).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="supplier_name" title="供应商" width="140" class-name="col--left" />
        <vxe-column field="brand_name" title="品牌" width="120" class-name="col--left" />
        <vxe-column field="settle_type" title="结算方式" width="100" class-name="col--center" />
        <vxe-column field="total_amt" title="物料金额" width="120" class-name="col--right">
          <template #default="{ row }">{{ formatAmount(row.total_amt) }}</template>
        </vxe-column>
        <vxe-column field="freight_amt" title="运费金额" width="100" class-name="col--right">
          <template #default="{ row }">{{ formatAmount(row.freight_amt) }}</template>
        </vxe-column>
        <vxe-column field="purchase_status" title="采购状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getPurchaseStatusInfo(row.purchase_status).class">
              {{ getPurchaseStatusInfo(row.purchase_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="in_status" title="入库状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getInStatusInfo(row.in_status).class">
              {{ getInStatusInfo(row.in_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="pay_status" title="付款状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getPayStatusInfo(row.pay_status).class">
              {{ getPayStatusInfo(row.pay_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="create_time" title="创建时间" width="160" class-name="col--center">
          <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
        </vxe-column>
        <vxe-column title="操作" width="280" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="navigateToDetail(row.purchase_no)">详情</button>
              <!-- 待审核状态操作 -->
              <button class="btn-link success" @click="confirmAudit(row)" v-if="row.purchase_status === 'pending_review'">审核</button>
              <button class="btn-link danger" @click="confirmRecall(row)" v-if="row.purchase_status === 'pending_review'">撤回</button>
              <!-- 准备采购状态操作 -->
              <button class="btn-link success" @click="confirmStartPurchase(row)" v-if="row.purchase_status === 'ready_purchase'">开始采购</button>
              <button class="btn-link warning" @click="confirmRollback(row)" v-if="row.purchase_status === 'ready_purchase'">回退</button>
              <!-- 采购中状态操作 -->
              <button class="btn-link success" @click="confirmComplete(row)" v-if="row.purchase_status === 'purchasing'">采购完成</button>
              <button class="btn-link warning" @click="confirmRollback(row)" v-if="row.purchase_status === 'purchasing'">回退</button>
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

    <!-- 创建/编辑弹窗 -->
    <div class="modal-overlay" v-if="showPurchaseModal">
      <div class="modal purchase-modal">
        <div class="modal-header">
          <h3>{{ editingOrder ? '编辑采购单' : '新建采购单' }}</h3>
          <button class="modal-close" @click="showPurchaseModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <!-- 基本信息 -->
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>采购类型 <span class="required">*</span></label>
                <select v-model="form.purchase_type" class="form-control" :disabled="isFormDisabled">
                  <option v-for="opt in purchaseTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>供应商 <span class="required">*</span></label>
                <select v-model="form.supplier_id" class="form-control" :disabled="!form.brand_id || isFormDisabled">
                  <option value="">请选择供应商</option>
                  <option v-for="supplier in supplierList" :key="supplier.id" :value="supplier.id">
                    {{ supplier.name }}
                    <template v-if="supplier.supplied_brands && supplier.supplied_brands.length > 0">
                      (折扣: {{ getSupplierDiscount(supplier, form.brand_id) }}%)
                    </template>
                  </option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>品牌</label>
                <select v-model="form.brand_id" class="form-control" :disabled="isFormDisabled">
                  <option value="">请选择品牌</option>
                  <option v-for="brand in brandList" :key="brand.id" :value="brand.id">{{ brand.name }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>采购员</label>
                <input v-model="form.purchase_user_id" class="form-control" placeholder="采购员ID" :disabled="isFormDisabled" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>结算方式 <span class="required">*</span></label>
                <select v-model="form.settle_type" class="form-control" :disabled="isFormDisabled">
                  <option v-for="st in settleTypeOptions" :key="st" :value="st">{{ st }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>预计到货日</label>
                <input v-model="form.expect_arrive_date" type="date" class="form-control" :disabled="isFormDisabled" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>运费金额</label>
                <input v-model.number="form.freight_amt" type="number" step="0.01" min="0" class="form-control" placeholder="0.00" :disabled="isFormDisabled" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group full-width">
                <label>备注</label>
                <input v-model="form.remark" class="form-control" placeholder="备注" :disabled="isFormDisabled" />
              </div>
            </div>
          </div>

          <!-- 收货信息 -->
          <div class="form-section">
            <div class="section-title">收货信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>收货类型</label>
                <select v-model="form.receive_info.type" class="form-control" :disabled="isFormDisabled">
                  <option value="customer">直运发给客户</option>
                  <option value="warehouse">入库到仓库</option>
                </select>
              </div>
              <div class="form-group" v-if="form.receive_info.type === 'warehouse'">
                <label>目标仓库</label>
                <select v-model="form.receive_info.warehouse_id" class="form-control" :disabled="isFormDisabled">
                  <option value="">请选择仓库</option>
                  <option v-for="wh in warehouseList" :key="wh.id" :value="wh.id">{{ wh.name }}</option>
                </select>
              </div>
              <div class="form-group" v-if="form.receive_info.type === 'customer'">
                <label>收货地址</label>
                <input v-model="form.receive_info.customer_addr" class="form-control" placeholder="详细地址" :disabled="isFormDisabled" />
              </div>
            </div>
            <div class="form-row" v-if="form.receive_info.type === 'customer'">
              <div class="form-group">
                <label>收货人</label>
                <input v-model="form.receive_info.contact_person" class="form-control" placeholder="收货人" :disabled="isFormDisabled" />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input v-model="form.receive_info.contact_tel" class="form-control" placeholder="联系电话" :disabled="isFormDisabled" />
              </div>
            </div>
          </div>

          <!-- 商品明细 -->
          <div class="form-section">
            <div class="section-title">
              商品明细
              <div class="search-select" style="margin-left: auto; position: relative;">
                <input
                  v-model="productSearchKeyword"
                  class="form-control"
                  placeholder="搜索商品/规格..."
                  style="width: 250px; font-size: 13px;"
                  :disabled="isFormDisabled"
                  @input="handleProductSearch(productSearchKeyword)"
                  @focus="showProductTree = true"
                />
                <div v-if="showProductTree && specSearchResults.length > 0" class="search-dropdown" style="max-height: 300px;">
                  <div
                    v-for="spec in specSearchResults"
                    :key="spec.id"
                    class="search-option"
                    @click="selectSpecFromSearch(spec)"
                  >
                    <span class="product-name-small">{{ spec.product_name || '' }}</span>
                    <span class="spec-code">{{ spec.spec_code }}</span>
                    <span class="spec-price">¥{{ spec.price }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="items-table">
              <table>
                <thead>
                  <tr>
                    <th style="width: 60px;">行号</th>
                    <th>商品名称</th>
                    <th>规格编码</th>
                    <th style="width: 100px;">采购数量</th>
                    <th style="width: 120px;">采购单价</th>
                    <th style="width: 80px;">折扣</th>
                    <th style="width: 120px;">金额</th>
                    <th style="width: 60px;">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in form.items" :key="index">
                    <td>{{ item.row_no }}</td>
                    <td>{{ item.product_name || item.product_id || '-' }}</td>
                    <td>{{ item.spec_code || '-' }}</td>
                    <td>
                      <input
                        v-model.number="item.purchase_qty"
                        type="number"
                        min="1"
                        class="table-input"
                        :disabled="isFormDisabled"
                        @input="updateItemAmount(index)"
                      />
                    </td>
                    <td>
                      <input
                        v-model.number="item.purchase_price"
                        type="number"
                        min="0"
                        step="0.01"
                        class="table-input"
                        :disabled="isFormDisabled"
                        @input="updateItemAmount(index)"
                      />
                    </td>
                    <td>
                      <input
                        v-model.number="item.discount"
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        class="table-input"
                        :disabled="isFormDisabled"
                        @input="updateItemAmount(index)"
                      />
                    </td>
                    <td>{{ formatAmount(item.amt) }}</td>
                    <td>
                      <button class="btn-link danger" @click="removeOrderItem(index)" :disabled="isFormDisabled">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <button class="add-item-btn" @click="addOrderItem" :disabled="isFormDisabled">+ 添加商品</button>
            </div>
          </div>

          <!-- 金额汇总 -->
          <div class="amount-summary">
            <div class="summary-row">
              <span>物料总额（未税）:</span>
              <span>{{ formatAmount(totalAmount) }}</span>
            </div>
            <div class="summary-row">
              <span>税额（13%）:</span>
              <span>{{ formatAmount(totalTaxAmt) }}</span>
            </div>
            <div class="summary-row total">
              <span>含税总额:</span>
              <span>{{ formatAmount(totalTaxInclAmount) }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showPurchaseModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveOrder" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal-overlay" v-if="showDetailModal">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>采购单详情</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="detailLoading" class="detail-loading">加载中...</div>
          <template v-else-if="selectedOrder">
            <!-- 基本信息 -->
            <div class="detail-section">
              <div class="section-title">基本信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>采购单号</label>
                  <span>{{ selectedOrder.purchase_no }}</span>
                </div>
                <div class="detail-item">
                  <label>采购类型</label>
                  <span class="type-tag" :class="getPurchaseTypeInfo(selectedOrder.purchase_type).class">
                    {{ getPurchaseTypeInfo(selectedOrder.purchase_type).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>供应商</label>
                  <span>{{ selectedOrder.supplier_name || selectedOrder.supplier_id }}</span>
                </div>
                <div class="detail-item">
                  <label>品牌</label>
                  <span>{{ selectedOrder.brand_name || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>结算方式</label>
                  <span>{{ selectedOrder.settle_type }}</span>
                </div>
                <div class="detail-item">
                  <label>预计到货日</label>
                  <span>{{ formatDate(selectedOrder.expect_arrive_date) }}</span>
                </div>
                <div class="detail-item">
                  <label>创建时间</label>
                  <span>{{ selectedOrder.create_time }}</span>
                </div>
                <div class="detail-item">
                  <label>关联销售单</label>
                  <span>{{ selectedOrder.source_sale_order_no || '-' }}</span>
                </div>
                <div class="detail-item full-width" v-if="selectedOrder.remark">
                  <label>备注</label>
                  <span>{{ selectedOrder.remark }}</span>
                </div>
              </div>
            </div>

            <!-- 收货信息 -->
            <div class="detail-section" v-if="selectedOrder.receive_info">
              <div class="section-title">收货信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>收货类型</label>
                  <span>{{ selectedOrder.receive_info.type === 'customer' ? '直运发给客户' : '入库到仓库' }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder.receive_info.customer_addr">
                  <label>收货地址</label>
                  <span>{{ selectedOrder.receive_info.customer_addr }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder.receive_info.contact_person">
                  <label>收货人</label>
                  <span>{{ selectedOrder.receive_info.contact_person }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder.receive_info.contact_tel">
                  <label>联系电话</label>
                  <span>{{ selectedOrder.receive_info.contact_tel }}</span>
                </div>
              </div>
            </div>

            <!-- 金额信息 -->
            <div class="detail-section">
              <div class="section-title">金额信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>物料金额</label>
                  <span>{{ formatAmount(selectedOrder.total_amt) }}</span>
                </div>
                <div class="detail-item">
                  <label>运费金额</label>
                  <span>{{ formatAmount(selectedOrder.freight_amt) }}</span>
                </div>
              </div>
            </div>

            <!-- 状态信息 -->
            <div class="detail-section">
              <div class="section-title">状态信息</div>
              <div class="status-actions">
                <div class="status-group">
                  <label>采购状态</label>
                  <div class="status-action-row">
                    <span class="status-tag" :class="getPurchaseStatusInfo(selectedOrder.status?.purchase_status).class">
                      {{ getPurchaseStatusInfo(selectedOrder.status?.purchase_status).label }}
                    </span>
                    <!-- 草稿状态操作 -->
                    <template v-if="selectedOrder.status?.purchase_status === 'draft'">
                      <button class="btn-sm btn-success" @click="confirmAudit(selectedOrder)">
                        审核通过
                      </button>
                      <button class="btn-sm btn-danger" @click="confirmRecall(selectedOrder)">
                        撤回
                      </button>
                    </template>
                    <!-- 已审核状态操作 -->
                    <template v-else-if="selectedOrder.status?.purchase_status === 'audited'">
                      <button class="btn-sm btn-warning" @click="confirmClose(selectedOrder)">
                        结案
                      </button>
                      <button class="btn-sm btn-info" @click="confirmReaudit(selectedOrder)">
                        重审
                      </button>
                      <button class="btn-sm btn-danger" @click="confirmRecall(selectedOrder)">
                        撤回
                      </button>
                      <button class="btn-sm btn-danger" @click="confirmVoid(selectedOrder)">
                        作废
                      </button>
                    </template>
                  </div>
                </div>
                <div class="status-group">
                  <label>入库状态</label>
                  <span class="status-tag" :class="getInStatusInfo(selectedOrder.status?.in_status).class">
                    {{ getInStatusInfo(selectedOrder.status?.in_status).label }}
                  </span>
                </div>
                <div class="status-group">
                  <label>付款状态</label>
                  <span class="status-tag" :class="getPayStatusInfo(selectedOrder.status?.pay_status).class">
                    {{ getPayStatusInfo(selectedOrder.status?.pay_status).label }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 商品明细 -->
            <div class="detail-section">
              <div class="section-title">商品明细</div>
              <div class="detail-table">
                <table>
                  <thead>
                    <tr>
                      <th>行号</th>
                      <th>商品名称</th>
                      <th>规格编码</th>
                      <th>采购数量</th>
                      <th>采购单价</th>
                      <th>折扣</th>
                      <th>金额</th>
                      <th>已入库</th>
                      <th>退货数量</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in selectedOrder.items" :key="item.row_no">
                      <td>{{ item.row_no }}</td>
                      <td>{{ item.product_name || item.product_id }}</td>
                      <td>{{ item.spec_code || '-' }}</td>
                      <td>{{ item.purchase_qty }}</td>
                      <td>{{ formatAmount(item.purchase_price) }}</td>
                      <td>{{ item.discount }}</td>
                      <td>{{ formatAmount(item.amt) }}</td>
                      <td>{{ item.in_qty }}</td>
                      <td>{{ item.return_qty }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 状态流转记录 -->
            <div class="detail-section" v-if="selectedOrderFlows.length > 0">
              <div class="section-title">状态流转记录</div>
              <div class="flow-timeline">
                <div class="flow-item" v-for="flow in selectedOrderFlows" :key="flow.id">
                  <div class="flow-dot"></div>
                  <div class="flow-content">
                    <div class="flow-time">{{ flow.operate_time }}</div>
                    <div class="flow-detail">
                      <span class="flow-field">{{ getFlowFieldName(flow.field) }}</span>
                      <span class="flow-old" v-if="flow.old_value">{{ flow.old_value }}</span>
                      <span class="flow-arrow" v-if="flow.old_value">→</span>
                      <span class="flow-new">{{ flow.new_value }}</span>
                      <span class="flow-operator">by {{ flow.operator }}</span>
                    </div>
                    <div class="flow-remark" v-if="flow.remark">{{ flow.remark }}</div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div class="modal-overlay" v-if="showDeleteConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="modal-close" @click="showDeleteConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要删除采购单 <strong>{{ deleteTargetPurchaseNo }}</strong> 吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDeleteOrder" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 审核确认弹窗 -->
    <div class="modal-overlay" v-if="showAuditConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认审核</h3>
          <button class="modal-close" @click="showAuditConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要审核通过采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAuditConfirm = false">取消</button>
          <button class="btn-success" @click="handleAuditOrder" :disabled="actionLoading">
            {{ actionLoading ? '审核中...' : '确认审核' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 结案确认弹窗 -->
    <div class="modal-overlay" v-if="showCloseConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认结案</h3>
          <button class="modal-close" @click="showCloseConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要结案采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCloseConfirm = false">取消</button>
          <button class="btn-warning" @click="handleCloseOrder" :disabled="actionLoading">
            {{ actionLoading ? '处理中...' : '确认结案' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 作废确认弹窗 -->
    <div class="modal-overlay" v-if="showCancelConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认作废</h3>
          <button class="modal-close" @click="showCancelConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要作废采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCancelConfirm = false">取消</button>
          <button class="btn-danger" @click="handleCancelOrder" :disabled="actionLoading">
            {{ actionLoading ? '处理中...' : '确认作废' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 撤回确认弹窗 -->
    <div class="modal-overlay" v-if="showRecallConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认撤回</h3>
          <button class="modal-close" @click="showRecallConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要撤回采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
          <p class="text-muted">撤回操作将删除采购单，并将对应的销售单商品设为未下推。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showRecallConfirm = false">取消</button>
          <button class="btn-danger" @click="handleRecallOrder" :disabled="actionLoading">
            {{ actionLoading ? '处理中...' : '确认撤回' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 重审确认弹窗 -->
    <div class="modal-overlay" v-if="showReauditConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认重审</h3>
          <button class="modal-close" @click="showReauditConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要重审采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
          <p class="text-muted">重审操作将采购单状态撤回到草稿状态。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showReauditConfirm = false">取消</button>
          <button class="btn-info" @click="handleReauditOrder" :disabled="actionLoading">
            {{ actionLoading ? '处理中...' : '确认重审' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 作废确认弹窗（已审核状态） -->
    <div class="modal-overlay" v-if="showVoidConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认作废</h3>
          <button class="modal-close" @click="showVoidConfirm = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要作废采购单 <strong>{{ actionTargetPurchaseNo }}</strong> 吗？</p>
          <p class="text-muted">作废操作将采购单状态更新为已作废。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showVoidConfirm = false">取消</button>
          <button class="btn-danger" @click="handleVoidOrder" :disabled="actionLoading">
            {{ actionLoading ? '处理中...' : '确认作废' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.purchase-order-workspace {
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
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.primary-btn {
  padding: 10px 20px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
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
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  overflow-x: auto;
}

.table-loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.table-loading-content {
  padding: 12px 24px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.order-link {
  color: var(--accent-blue);
  cursor: pointer;
  text-decoration: none;
}

.order-link:hover {
  text-decoration: underline;
}

/* ============ 状态标签 ============ */

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.draft { background-color: rgba(128,128,128,0.1); color: var(--text-muted); }
.status-tag.audited { background-color: rgba(59,130,246,0.1); color: var(--accent-blue); }
.status-tag.closed { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239,68,68,0.1); color: var(--accent-red); }
.status-tag.none { background-color: rgba(128,128,128,0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245,158,11,0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }

.type-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag.direct { background-color: rgba(59,130,246,0.1); color: var(--accent-blue); }
.type-tag.warehouse { background-color: rgba(16,185,129,0.1); color: var(--accent-green); }

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

.btn-link.danger { color: var(--accent-red); }
.btn-link.danger:hover { background-color: rgba(239,68,68,0.1); }
.btn-link.success { color: var(--accent-green); }
.btn-link.success:hover { background-color: rgba(16,185,129,0.1); }
.btn-link.warning { color: var(--accent-yellow); }
.btn-link.warning:hover { background-color: rgba(245,158,11,0.1); }

/* ============ 展开行 ============ */

.expand-items-panel {
  padding: 12px 20px;
  background-color: var(--bg-secondary);
}

.expand-items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.expand-items-table th {
  padding: 8px 12px;
  text-align: left;
  color: var(--text-muted);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
}

.expand-items-table td {
  padding: 8px 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

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

.purchase-modal {
  width: 90%;
  max-width: 1200px;
}

.detail-modal {
  width: 90%;
  max-width: 900px;
}

.confirm-modal {
  width: 400px;
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

/* ============ 表单 ============ */

.form-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
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

.required {
  color: var(--accent-red);
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

.form-control:disabled,
.table-input:disabled,
.add-item-btn:disabled {
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  cursor: not-allowed;
  opacity: 0.7;
}

/* ============ 商品明细表 ============ */

.items-table {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.items-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.items-table th {
  padding: 10px 12px;
  text-align: left;
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
}

.items-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.table-input {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.table-input:focus {
  border-color: var(--accent-blue);
}

.add-item-btn {
  width: 100%;
  padding: 10px;
  background: none;
  border: 1px dashed var(--border-color);
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.add-item-btn:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

/* ============ 金额汇总 ============ */

.amount-summary {
  margin-top: 16px;
  padding: 16px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.summary-row.total {
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
  padding-top: 12px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ============ 详情 ============ */

.detail-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 14px;
}

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

.amount-highlight {
  font-weight: 600;
  color: var(--accent-blue) !important;
}

.detail-table {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.detail-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.detail-table th {
  padding: 10px 12px;
  text-align: left;
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.detail-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
  white-space: nowrap;
}

/* ============ 状态操作 ============ */

.status-actions {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.status-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-group label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.status-action-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-sm {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.btn-sm:hover { opacity: 0.8; }
.btn-sm.btn-success { background-color: var(--accent-green); color: white; }
.btn-sm.btn-warning { background-color: var(--accent-yellow); color: white; }
.btn-sm.btn-danger { background-color: var(--accent-red); color: white; }

/* ============ 状态流转 ============ */

.flow-timeline {
  position: relative;
  padding-left: 24px;
}

.flow-timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: var(--border-color);
}

.flow-item {
  position: relative;
  padding-bottom: 20px;
}

.flow-dot {
  position: absolute;
  left: -20px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--accent-blue);
  border: 2px solid var(--bg-card);
}

.flow-content {
  padding-left: 8px;
}

.flow-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.flow-detail {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.flow-field {
  font-weight: 500;
  color: var(--text-primary);
}

.flow-old {
  color: var(--text-muted);
}

.flow-arrow {
  color: var(--text-muted);
}

.flow-new {
  color: var(--accent-blue);
}

.flow-operator {
  color: var(--text-muted);
  font-size: 12px;
}

.flow-remark {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  font-style: italic;
}

/* ============ 搜索下拉 ============ */

.search-select {
  position: relative;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  z-index: 100;
  max-height: 250px;
  overflow-y: auto;
}

.search-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  font-size: 13px;
}

.search-option:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.product-name-small {
  color: var(--text-primary);
}

.spec-code {
  color: var(--text-muted);
}

.spec-price {
  margin-left: auto;
  color: var(--accent-blue);
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

.btn-success {
  padding: 8px 16px;
  background-color: var(--accent-green);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
}

.btn-warning {
  padding: 8px 16px;
  background-color: var(--accent-yellow);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
}

.btn-danger {
  padding: 8px 16px;
  background-color: var(--accent-red);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ============ vxe-table 深度样式 ============ */

:deep(.vxe-body--column) {
  &.expand--cell, &.col--actived {
    background-color: var(--bg-card) !important;
  }
}

:deep(.vxe-body--row.expand--row > td) {
  background-color: var(--bg-card) !important;
}

:deep(.vxe-body--row.expand--row:hover > td) {
  background-color: var(--bg-secondary) !important;
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
</style>
