<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch, onBeforeUnmount, nextTick } from 'vue'
import { salesOrderApi, customerApi, productApi, warehouseApi, customerDiscountApi, brandApi, userApi, type Customer } from '../../services/api'
import { useProvinceCity } from '../../hooks/useProvinceCity'
import { usePermission } from '../../hooks/usePermission'
import PushPurchaseItemSelectModal from './PushPurchaseItemSelectModal.vue'

const emit = defineEmits<{
  navigate: [id: string, extra?: Record<string, any>]
}>()

// Types
interface SalesOrderItem {
  row_no: number
  product_id: string
  product_name?: string
  product_code?: string
  brand_id?: string
  brand_name?: string
  spec_id: string | number
  spec_code?: string
  packaging?: string
  sales_spec?: string
  qty: number
  price: number
  discount: number
  discounted_price: number
  amt: number
  warehouse_id: string | number
  warehouse_name?: string
  shipping_method: 'direct' | 'warehouse' | 'warehouse_pickup'
  out_qty: number
  return_qty: number
  remain_out_qty: number
  item_remark?: string  // 商品备注
}

interface DeliverInfo {
  addr: string
  province: string
  city: string
  person_name: string
  person_tel: string
}

interface InvoiceInfo {
  invoice_title: string
  invoice_type: string
  tax_number: string
  bank_name: string
  bank_account: string
  address_phone?: string
  address?: string
  phone?: string
}

interface StatusFlowRecord {
  field: string
  old_value?: string | null
  new_value: string
  operator: string
  operate_time: string
  remark?: string
}

interface SalesOrder {
  id: string
  order_no: string
  order_date: string
  customer_id: string
  customer_name?: string
  sale_user_id?: string
  sale_user_name?: string
  deliver_info: DeliverInfo
  expect_deliver_date?: string
  settle_type: string
  total_amt: number
  tax_rate: number
  tax_amt: number
  total_tax_amt: number
  total_discount_amt: number
  freight_amt?: number
  order_status: string
  delivery_status: string
  push_status?: string
  invoice_status: string
  finance_status?: string
  cost_amt?: number
  profit_amt?: number
  invoice_info: InvoiceInfo
  creator_id: string
  creator_name?: string
  create_time: string
  remark: string
  total_out_qty: number
  total_received_amt: number
  total_invoice_amt: number
  total_return_qty: number
  total_return_amt: number
  items: SalesOrderItem[]
}

interface SpecSearchResult {
  id: string | number
  spec_code: string
  packaging?: string
  sales_spec?: string
  price: number
  is_active: boolean
  product_id: string | number
  product_name: string
  product_code: string
  brand_id?: string | number
  brand_name: string
}

interface Warehouse {
  id: number
  name: string
}

// Constants
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
  full: { label: '全部发货', class: 'full' },
  no_need: { label: '无需发货', class: 'reconciled' },
  has_return: { label: '有退货', class: 'partial' }
}

const pushStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未下推', class: 'none' },
  partial: { label: '部分下推', class: 'partial' },
  full: { label: '已下推', class: 'full' },
  not_needed: { label: '无需下推', class: 'reconciled' }
}

const invoiceStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未开票', class: 'none' },
  partial: { label: '部分开票', class: 'partial' },
  full: { label: '全部开票', class: 'full' },
  no_need: { label: '无需开票', class: 'reconciled' }
}

const financeStatusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'none' },
  partial_paid: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'full' },
  reconciled: { label: '已对账', class: 'reconciled' },
  no_need: { label: '无需付款', class: 'reconciled' }
}

const settleTypeOptions = [
  { value: '月结', label: '月结' },
  { value: '货到付款', label: '货到付款' },
  { value: '款到发货', label: '款到发货' }
]

// 第三方平台选项
const thirdPartyPlatformOptions = [
  { value: '博赛乐-锐竞采购平台', label: '博赛乐-锐竞采购平台' },
  { value: '博赛乐-虫洞空间', label: '博赛乐-虫洞空间' },
  { value: '睿沃特-供应室', label: '睿沃特-供应室' },
  { value: '兹罗-喀斯玛', label: '兹罗-喀斯玛' },
  { value: '智达康-库巴扎', label: '智达康-库巴扎' },
  { value: '兹罗-库巴扎', label: '兹罗-库巴扎' }
]

const shippingMethodOptions = [
  { value: 'direct', label: '直运' },
  { value: 'warehouse', label: '仓库发货' },
  { value: 'warehouse_pickup', label: '仓库自提' },
  { value: 'logistics', label: '物流' },
  { value: 'delivery', label: '送货' }
]

const orderStatusOptions = Object.entries(orderStatusMap).map(([value, { label }]) => ({ value, label }))

const invoiceStatusOptions = Object.entries(invoiceStatusMap).map(([value, { label }]) => ({ value, label }))

const deliveryStatusOptions = Object.entries(deliveryStatusMap).map(([value, { label }]) => ({ value, label }))

// State
const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')
const filterCustomerId = ref('')
const filterKeyword = ref('')
const filterInvoiceStatus = ref('')
const filterDeliveryStatus = ref('')
const filterSaleUserId = ref('')
const filterOrderDateStart = ref('')
const filterOrderDateEnd = ref('')
const selectedRows = ref<SalesOrder[]>([])
const tableRef = ref<any>(null)
const topTableRef = ref<any>(null)
const topDummyData = ref([{}])

// 权限相关
const { userPermissions } = usePermission()
const isAdmin = computed(() => userPermissions.value.role_codes.includes('super_admin') || userPermissions.value.role_codes.includes('admin'))

// Modals
const showOrderModal = ref(false)
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const showAuditConfirm = ref(false)
const showCloseConfirm = ref(false)
const showCancelConfirm = ref(false)
const showRejectConfirm = ref(false)
const showAllDirectConfirm = ref(false)
const showPushItemSelect = ref(false)
const pushableItems = ref<any[]>([])
const editingOrder = ref<SalesOrder | null>(null)
const selectedOrder = ref<SalesOrder | null>(null)
const selectedOrderFlows = ref<StatusFlowRecord[]>([])
const deleteTargetOrderNo = ref<string | null>(null)
const actionTargetOrderNo = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)
const actionLoading = ref(false)
const detailLoading = ref(false)

// Dropdown data
const customerList = ref<Customer[]>([])
const specSearchResults = ref<SpecSearchResult[]>([])
const warehouseList = ref<Warehouse[]>([])
const userList = ref<{ id: string | number; name: string }[]>([])

// 仓库库存数据（按规格ID缓存）
const specStockMap = ref<Record<string, { warehouse_id: string; warehouse_name: string; quantity: number }[]>>({})
// 表头批量设置
const headerShippingMethod = ref('')
const headerWarehouseId = ref<number | string>('')
const customersLoading = ref(false)
const warehousesLoading = ref(false)
const usersLoading = ref(false)

// Search states
const customerSearchKeyword = ref('')
const showCustomerDropdown = ref(false)

// 规格编号搜索相关
const showSpecDropdown = ref<number | null>(null)
const specSearchKeywords = ref<Record<number, string>>({})
let specSearchTimer: ReturnType<typeof setTimeout> | null = null

const { loadProvinceCityData, getProvinces, getCities } = useProvinceCity()

// Province/City state
const provinceList = ref<{ code: string; name: string }[]>([])
const cityList = ref<{ code: string; name: string }[]>([])
const selectedProvince = ref('')
const selectedCity = ref('')

// Customer shipping addresses and invoice infos for dropdown
const customerShippingAddresses = ref<any[]>([])
const customerInvoiceInfos = ref<any[]>([])
const selectedShippingAddressId = ref('')
const selectedInvoiceInfoId = ref('')

// Quick add modal state
const showQuickAddShippingModal = ref(false)
const showQuickAddInvoiceModal = ref(false)
const quickAddShippingForm = ref({
  recipient_name: '',
  recipient_phone: '',
  province: '',
  city: '',
  address: '',
  is_default: false
})
const INVOICE_TYPE_OPTIONS = [
  { value: '增值税', label: '增值税' },
  { value: '普通发票', label: '普通发票' },
  { value: '增值税专用发票', label: '增值税专用发票' },
  { value: '不开票', label: '不开票' }
]

const quickAddInvoiceForm = ref({
  invoice_title: '',
  invoice_type: '',
  tax_number: '',
  bank_name: '',
  bank_account: '',
  is_default: false
})
const quickAddLoading = ref(false)
const quickAddSelectedProvince = ref('')
const quickAddSelectedCity = ref('')
const quickAddCityList = ref<any[]>([])

// 快速新增收货地址 AI 解析相关状态
const showShippingAiPanel = ref(false)
const shippingAiInputText = ref('')
const shippingAiImageFiles = ref<File[]>([])
const shippingAiImagePreviews = ref<string[]>([])
const shippingAiParsing = ref(false)

// 运费相关状态
const freightAmt = ref(0)
const isEditingFreight = ref(false)
const freightInputRef = ref<HTMLInputElement | null>(null)
const isFreightManuallyModified = ref(false)
const brandFreightCache = ref<Record<string, number>>({})
const isAddOrder = ref(false)

// AI 解析相关状态
const showAiPanel = ref(false)
const aiInputText = ref('')
const aiImageFiles = ref<File[]>([])
const aiImagePreviews = ref<string[]>([])
const aiParsing = ref(false)
const aiProgress = ref(0) // AI 解析进度 0-100
const aiProgressStep = ref('') // 当前步骤描述
// AI 解析结果中待确认项标记
const aiPendingCustomer = ref(false) // 客户待确认
const aiPendingItems = ref<Set<number>>(new Set()) // 商品行待确认索引集合

// Watch quick add province change -> load cities
watch(quickAddSelectedProvince, async (val) => {
  quickAddCityList.value = []
  quickAddSelectedCity.value = ''
  quickAddShippingForm.value.province = val
  quickAddShippingForm.value.city = ''
  if (val) {
    try {
      quickAddCityList.value = getCities(val)
    } catch (e) {
      console.error('加载城市列表失败:', e)
    }
  }
})

watch(quickAddSelectedCity, (val) => {
  quickAddShippingForm.value.city = val
})

// Click outside handler
const handleclickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.search-select')) {
    showCustomerDropdown.value = false
    showSpecDropdown.value = null
    showEditWarehouseDropdown.value = null
    specSearchResults.value = []
  }
}

// Watch province change -> load cities
watch(selectedProvince, async (val) => {
  cityList.value = []
  selectedCity.value = ''
  orderForm.value.deliver_info.province = val
  orderForm.value.deliver_info.city = ''
  if (val) {
    try {
      cityList.value = getCities(val)
    } catch (e) {
      console.error('加载城市失败:', e)
    }
  }
})

// Watch city change
watch(selectedCity, (val) => {
  orderForm.value.deliver_info.city = val
})

// Form
const orderForm = ref({
  order_date: new Date().toISOString().split('T')[0],
  customer_id: '',
  customer_name: '',
  sale_user_id: '',
  third_party_platform: '',
  platform_order_no: '',
  deliver_info: {
    addr: '',
    province: '',
    city: '',
    person_name: '',
    person_tel: ''
  },
  expect_deliver_date: '',
  settle_type: '月结',
  invoice_info: {
    invoice_title: '',
    invoice_type: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    address: '',
    phone: ''
  },
  remark: '',
  items: [] as SalesOrderItem[]
})

// Computed
const hasActiveFilters = computed(() => !!(filterStatus.value || filterCustomerId.value || filterKeyword.value || filterInvoiceStatus.value || filterDeliveryStatus.value || filterSaleUserId.value || filterOrderDateStart.value || filterOrderDateEnd.value))

// Methods
const loadOrders = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }

    if (filterStatus.value) params.status = filterStatus.value
    if (filterCustomerId.value) params.customer_id = filterCustomerId.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    if (filterInvoiceStatus.value) params.invoice_status = filterInvoiceStatus.value
    if (filterDeliveryStatus.value) params.delivery_status = filterDeliveryStatus.value
    if (filterSaleUserId.value && isAdmin.value) params.sale_user_id = filterSaleUserId.value
    if (filterOrderDateStart.value) params.order_date_start = filterOrderDateStart.value
    if (filterOrderDateEnd.value) params.order_date_end = filterOrderDateEnd.value

    const res = await salesOrderApi.list(params)
    orders.value = res?.items || []
    total.value = res?.total || 0
  } catch (error) {
    console.error('加载订单列表失败:', error)
    window.showToast('加载订单列表失败', 'error')
  } finally {
    loading.value = false
  }
}

const loadCustomers = async (keyword?: string) => {
  customersLoading.value = true
  try {
    const params: any = { page_size: 50 }
    if (keyword) params.keyword = keyword
    const res = await customerApi.list(params)
    customerList.value = res?.items || []
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    customersLoading.value = false
  }
}

// 规格编号搜索
const handleSpecSearch = (index: number, keyword: string) => {
  specSearchKeywords.value[index] = keyword

  if (specSearchTimer) clearTimeout(specSearchTimer)
  if (!keyword || keyword.length < 1) {
    specSearchResults.value = []
    return
  }
  specSearchTimer = setTimeout(async () => {
    try {
      const res = await productApi.searchSpecs(keyword, 20)
      specSearchResults.value = res?.items || []
    } catch (e) {
      console.error('搜索规格失败:', e)
      specSearchResults.value = []
    }
  }, 300)
}

// 清除规格选择
const clearSpecSelection = (index: number) => {
  const item = orderForm.value.items[index]
  // 重置所有商品相关字段
  item.spec_id = ''
  item.spec_code = ''
  item.product_id = ''
  item.product_name = ''
  item.product_code = ''
  item.brand_name = ''
  item.packaging = ''
  item.sales_spec = ''
  item.price = 0
  item.discount = 1
  item.discounted_price = 0
  item.amt = 0
  // 重置发货方式和仓库
  item.shipping_method = 'direct'
  item.warehouse_id = ''
  item.warehouse_name = ''
  specSearchKeywords.value[index] = ''
}

// 从规格搜索结果中选择规格（编辑模式）
const selectSpecFromSearchEdit = async (index: number, specResult: SpecSearchResult) => {
  showSpecDropdown.value = null
  specSearchResults.value = []
  specSearchKeywords.value[index] = ''
  // 清除该行的待确认标记
  aiPendingItems.value.delete(index)

  let discount = 1
  if (orderForm.value.customer_id && specResult.brand_id) {
    try {
      const discountRes = await customerDiscountApi.list({
        customer_id: orderForm.value.customer_id,
        brand_id: String(specResult.brand_id),
        is_active: true
      })
      const discountItem = discountRes?.items?.[0]
      if (discountItem) discount = discountItem.discount_value
    } catch (e) {
      console.error('获取客户折扣失败:', e)
    }
  }

  const discountedPrice = +(specResult.price * discount).toFixed(2)
  orderForm.value.items[index] = {
    ...orderForm.value.items[index],
    product_id: String(specResult.product_id),
    product_name: specResult.product_name,
    product_code: specResult.product_code || '',
    brand_id: specResult.brand_id ? String(specResult.brand_id) : '',
    brand_name: specResult.brand_name || '',
    spec_id: String(specResult.id),
    spec_code: specResult.spec_code,
    packaging: specResult.packaging || '',
    sales_spec: specResult.sales_spec || '',
    price: specResult.price,
    discount: discount,
    discounted_price: discountedPrice,
    amt: +(orderForm.value.items[index].qty * discountedPrice).toFixed(2)
  }

  // 自动加载库存
  await loadSpecStock(specResult.id)
}

const loadWarehouses = async () => {
  warehousesLoading.value = true
  try {
    const res = await warehouseApi.list({ page_size: 100 })
    warehouseList.value = res?.items || []
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  } finally {
    warehousesLoading.value = false
  }
}

// 加载用户列表（业务员下拉）
const loadUsers = async () => {
  if (!isAdmin.value) return
  usersLoading.value = true
  try {
    const res = await userApi.list({ page_size: 100 })
    userList.value = (res?.items || []).map((u: any) => ({ id: u.id, name: u.name || u.username }))
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    usersLoading.value = false
  }
}

// 加载规格的库存数据
const loadSpecStock = async (specId: string | number) => {
  if (!specId || specStockMap.value[String(specId)]) return
  try {
    const res = await productApi.getSpecStockDetail(String(specId))
    specStockMap.value[String(specId)] = res?.items || []
  } catch (e) {
    console.error('加载库存失败:', e)
    specStockMap.value[String(specId)] = []
  }
}

// 获取规格的库存仓库列表
const getSpecStockList = (specId: string | number) => {
  return specStockMap.value[String(specId)] || []
}

// 编辑弹窗仓库下拉状态
const showEditWarehouseDropdown = ref<number | null>(null)

// 从库存列表中选择仓库（编辑模式）
const selectWarehouseFromStockEdit = (index: number, stockItem: { warehouse_id: string | number; warehouse_name: string; quantity: number }) => {
  orderForm.value.items[index].warehouse_id = String(stockItem.warehouse_id)
  orderForm.value.items[index].warehouse_name = stockItem.warehouse_name
  showEditWarehouseDropdown.value = null
}

// 批量设置发货方式
const applyHeaderShippingMethod = () => {
  if (!headerShippingMethod.value) return
  orderForm.value.items.forEach(item => {
    if (item.product_id) {
      item.shipping_method = headerShippingMethod.value as 'direct' | 'warehouse' | 'warehouse_pickup'
      if (headerShippingMethod.value === 'direct') {
        item.warehouse_id = ''
        item.warehouse_name = ''
      }
    }
  })
}

// 批量设置仓库
const applyHeaderWarehouse = () => {
  if (!headerWarehouseId.value) return
  const warehouse = warehouseList.value.find((w: Warehouse) => w.id === Number(headerWarehouseId.value))
  orderForm.value.items.forEach(item => {
    if (item.product_id && item.shipping_method !== 'direct') {
      item.warehouse_id = Number(headerWarehouseId.value)
      item.warehouse_name = warehouse?.name || ''
    }
  })
}

const filteredCustomers = computed(() => {
  return customerList.value.slice(0, 10)
})

// Customer search debounce timer
let customerSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleCustomerSearch = () => {
  if (customerSearchTimer) clearTimeout(customerSearchTimer)
  customerSearchTimer = setTimeout(() => {
    loadCustomers(customerSearchKeyword.value || undefined)
  }, 300)
}

const handleSearch = () => {
  page.value = 1
  loadOrders()
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadOrders()
}

const handleCheckboxChange = ({ records }: { records: SalesOrder[] }) => {
  selectedRows.value = records
}

const handleBatchSubmit = async () => {
  const draftOrders = selectedRows.value.filter(o => o.order_status === 'draft')
  if (draftOrders.length === 0) {
    window.showToast('请选择草稿状态的订单', 'error')
    return
  }

  try {
    for (const order of draftOrders) {
      await salesOrderApi.submit(order.order_no)
    }
    window.showToast(`成功提交 ${draftOrders.length} 个订单`, 'success')
    selectedRows.value = []
    loadOrders()
  } catch (error) {
    console.error('批量提交失败:', error)
    window.showToast('批量提交失败', 'error')
  }
}

// 监听表格滚动，同步展开内容位置
const scrollLeft = ref(0)

const handleTableScroll = (params: any) => {
  // vxe-table scroll 事件参数
  const left = params.scrollLeft || 0
  scrollLeft.value = left

  // 同步顶部滚动条 - 使用 vxe-table 的 scrollTo 方法
  if (topTableRef.value) {
    topTableRef.value.scrollTo(left, 0)
  }

  // 使用 transform 移动展开内容
  const panels = document.querySelectorAll('.expand-items-panel')
  panels.forEach((panel: Element) => {
    (panel as HTMLElement).style.transform = `translateX(-${left}px)`
  })
}

// 顶部滚动条滚动时同步主表格
const handleTopScroll = (params: any) => {
  const left = params.scrollLeft || 0

  // 同步主表格 - 使用 vxe-table 的 scrollTo 方法
  if (tableRef.value) {
    tableRef.value.scrollTo(left, 0)
  }

  // 同步展开内容
  scrollLeft.value = left
  const panels = document.querySelectorAll('.expand-items-panel')
  panels.forEach((panel: Element) => {
    (panel as HTMLElement).style.transform = `translateX(-${left}px)`
  })
}

const resetFilters = () => {
  filterStatus.value = ''
  filterCustomerId.value = ''
  filterKeyword.value = ''
  filterInvoiceStatus.value = ''
  filterDeliveryStatus.value = ''
  filterSaleUserId.value = ''
  filterOrderDateStart.value = ''
  filterOrderDateEnd.value = ''
  page.value = 1
  loadOrders()
}

const resetOrderForm = () => {
  orderForm.value = {
    order_date: new Date().toISOString().split('T')[0],
    customer_id: '',
    customer_name: '',
    sale_user_id: '',
    third_party_platform: '',
    platform_order_no: '',
    deliver_info: {
      addr: '',
      province: '',
      city: '',
      person_name: '',
      person_tel: ''
    },
    expect_deliver_date: '',
    settle_type: '月结',
    invoice_info: {
      invoice_title: '',
      invoice_type: '',
      tax_number: '',
      bank_name: '',
      bank_account: '',
      address: '',
      phone: ''
    },
    remark: '',
    items: []
  }
  editingOrder.value = null
  customerSearchKeyword.value = ''
  selectedProvince.value = ''
  selectedCity.value = ''
  cityList.value = []
  customerShippingAddresses.value = []
  customerInvoiceInfos.value = []
  selectedShippingAddressId.value = ''
  selectedInvoiceInfoId.value = ''
  headerShippingMethod.value = ''
  headerWarehouseId.value = ''
  specStockMap.value = {}
  // 重置运费相关状态
  freightAmt.value = 0
  isEditingFreight.value = false
  isFreightManuallyModified.value = false
  brandFreightCache.value = {}
  isAddOrder.value = false
  // 重置 AI 解析相关状态
  showAiPanel.value = false
  aiInputText.value = ''
  aiImageFiles.value = []
  aiImagePreviews.value = []
  aiPendingCustomer.value = false
  aiPendingItems.value = new Set()
}

const openCreateOrder = () => {
  resetOrderForm()
  showOrderModal.value = true
}

// ========== AI 解析相关方法 ==========

// 切换 AI 面板显示
const toggleAiPanel = () => {
  showAiPanel.value = !showAiPanel.value
  if (showAiPanel.value) {
    aiInputText.value = ''
    aiImageFiles.value = []
    aiImagePreviews.value = []
  }
}

// 处理多图选择
const handleAiImageSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files) return

  const newFiles = Array.from(input.files)
  // 最多 3 张
  if (aiImageFiles.value.length + newFiles.length > 3) {
    window.showToast('最多支持3张图片', 'warning')
    return
  }

  for (const file of newFiles) {
    // 单图 5MB 限制
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`图片 ${file.name} 超过5MB限制`, 'warning')
      continue
    }
    aiImageFiles.value.push(file)
    // 生成预览
    const reader = new FileReader()
    reader.onload = (e) => {
      aiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  // 重置 input 以支持重复选择同一文件
  input.value = ''
}

// 删除图片
const removeAiImage = (index: number) => {
  aiImageFiles.value.splice(index, 1)
  aiImagePreviews.value.splice(index, 1)
}

// 处理粘贴图片
const handleAiPaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  const imageFiles: File[] = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) imageFiles.push(file)
    }
  }

  if (imageFiles.length === 0) return

  // 有图片时阻止默认粘贴行为
  event.preventDefault()

  if (aiImageFiles.value.length + imageFiles.length > 3) {
    window.showToast('最多支持3张图片', 'warning')
    return
  }

  for (const file of imageFiles) {
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`粘贴的图片超过5MB限制`, 'warning')
      continue
    }
    aiImageFiles.value.push(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      aiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  window.showToast(`已粘贴${imageFiles.length}张图片`, 'success')
}

// 将图片文件转为 base64（不含 data:image/...;base64, 前缀）
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      // 去除 data:image/xxx;base64, 前缀
      const base64 = dataUrl.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// 安全取字符串，排除 null/undefined/"null"
const safeStr = (v: any): string => {
  if (v === null || v === undefined) return ''
  const s = String(v).trim()
  return s === 'null' ? '' : s
}

// 安全取数值，支持范围限制
const safeNum = (v: any, min?: number, max?: number): number => {
  const n = Number(v)
  if (isNaN(n)) return 0
  let result = n
  if (min !== undefined && result < min) result = min
  if (max !== undefined && result > max) result = max
  return result
}

// 发货方式中文转英文
const safeShippingMethod = (v: any): 'direct' | 'warehouse' | 'warehouse_pickup' => {
  if (v === 'direct' || v === 'warehouse' || v === 'warehouse_pickup') return v
  const map: Record<string, 'direct' | 'warehouse' | 'warehouse_pickup'> = {
    '直运': 'direct', '快递': 'direct', '物流': 'direct',
    '仓库发货': 'warehouse', '仓库': 'warehouse',
    '仓库自提': 'warehouse_pickup', '自提': 'warehouse_pickup'
  }
  return map[String(v)] || 'direct'
}

// 结算方式映射
const safeSettleType = (v: any): string => {
  const validTypes = ['月结', '货到付款', '款到发货']
  if (v && validTypes.includes(String(v))) return String(v)
  // 常见映射
  const map: Record<string, string> = {
    '月结30天': '月结', '月结60天': '月结', '月结90天': '月结',
    '现结': '货到付款', '预付': '款到发货'
  }
  return map[String(v)] || '月结'
}

// AI 解析结果填充到表单
const fillFormWithAiResult = async (result: any) => {
  if (!result) return

  const { customer, order_info, items, deliver_info, invoice_info } = result

  // 清空待确认标记
  aiPendingCustomer.value = false
  aiPendingItems.value = new Set()

  // 1. 填充客户信息
  if (customer) {
    if (customer.matched && customer.matched.length > 0) {
      // 有匹配结果，自动选中第一个
      // 注意：AI返回的是 {id, name, code}，需要映射为 selectCustomer 期望的格式
      const matchedCustomer = customer.matched[0]
      await selectCustomer({
        id: matchedCustomer.id,
        customer_name: matchedCustomer.name
      })
    } else {
      // 无匹配，标记待确认
      aiPendingCustomer.value = true
      // 将提取的客户名称填入搜索框，方便用户搜索
      customerSearchKeyword.value = safeStr(customer.extracted_name)
    }
  }

  // 2. 填充订单元数据
  if (order_info) {
    if (order_info.order_date) {
      orderForm.value.order_date = safeStr(order_info.order_date)
    }
    if (order_info.settle_type) {
      orderForm.value.settle_type = safeSettleType(order_info.settle_type)
    }
    if (order_info.expect_deliver_date) {
      orderForm.value.expect_deliver_date = safeStr(order_info.expect_deliver_date)
    }
    if (order_info.remark) {
      orderForm.value.remark = safeStr(order_info.remark)
    }
    if (order_info.freight_amt !== undefined && order_info.freight_amt !== null) {
      freightAmt.value = safeNum(order_info.freight_amt, 0)
      isFreightManuallyModified.value = true
    }
  }

  // 3. 填充商品明细
  if (items && Array.isArray(items) && items.length > 0) {
    orderForm.value.items = []
    for (let i = 0; i < items.length; i++) {
      const aiItem = items[i]
      const rowNo = i + 1

      // 基础行数据
      const newItem: SalesOrderItem = {
        row_no: rowNo,
        product_id: '',
        product_name: '',
        product_code: '',
        brand_id: '',
        brand_name: '',
        spec_id: '',
        spec_code: '',
        packaging: '',
        sales_spec: '',
        qty: safeNum(aiItem.qty, 1),
        price: safeNum(aiItem.price, 0),
        discount: safeNum(aiItem.discount, 0, 1) || 1,
        discounted_price: 0,
        amt: 0,
        warehouse_id: '',
        warehouse_name: '',
        shipping_method: safeShippingMethod(aiItem.shipping_method),
        out_qty: 0,
        return_qty: 0,
        remain_out_qty: 0
      }

      // 如果有匹配的规格
      if (aiItem.matched && aiItem.matched.length > 0) {
        const matchedSpec = aiItem.matched[0]
        newItem.spec_id = String(matchedSpec.spec_id || matchedSpec.id)
        newItem.spec_code = safeStr(matchedSpec.spec_code)
        newItem.product_name = safeStr(matchedSpec.product_name)
        newItem.product_id = String(matchedSpec.product_id || '')
        newItem.brand_name = safeStr(matchedSpec.brand_name)
        newItem.packaging = safeStr(matchedSpec.packaging)
        newItem.sales_spec = safeStr(matchedSpec.spec_attrs || matchedSpec.sales_spec)

        // 如果匹配结果包含价格，使用匹配的价格
        if (matchedSpec.price !== undefined) {
          newItem.price = safeNum(matchedSpec.price, 0)
        }

        // 加载库存信息
        await loadSpecStock(newItem.spec_id)
      } else {
        // 无匹配，标记待确认
        aiPendingItems.value.add(i)
        // 将提取的信息暂存到 spec_code 字段供用户参考
        newItem.spec_code = safeStr(aiItem.extracted_name)
        if (aiItem.extracted_spec) {
          newItem.packaging = safeStr(aiItem.extracted_spec)
        }
      }

      // 计算折后价和金额
      newItem.discounted_price = +(newItem.price * newItem.discount).toFixed(2)
      newItem.amt = +(newItem.qty * newItem.discounted_price).toFixed(2)

      orderForm.value.items.push(newItem)
    }
  }

  // 4. 填充发货信息
  if (deliver_info) {
    orderForm.value.deliver_info = {
      addr: safeStr(deliver_info.addr),
      province: safeStr(deliver_info.province),
      city: safeStr(deliver_info.city),
      person_name: safeStr(deliver_info.person_name),
      person_tel: safeStr(deliver_info.person_tel)
    }
    // 尝试匹配省份城市
    if (deliver_info.province) {
      selectedProvince.value = safeStr(deliver_info.province)
      if (deliver_info.city) {
        await nextTick()
        selectedCity.value = safeStr(deliver_info.city)
      }
    }
  }

  // 5. 填充开票信息
  if (invoice_info) {
    orderForm.value.invoice_info = {
      invoice_title: safeStr(invoice_info.invoice_title),
      invoice_type: safeStr(invoice_info.invoice_type) || '增值税',
      tax_number: safeStr(invoice_info.tax_number),
      bank_name: safeStr(invoice_info.bank_name),
      bank_account: safeStr(invoice_info.bank_account),
      address: safeStr(invoice_info.address),
      phone: safeStr(invoice_info.phone)
    }
  }
}

// AI 解析提交
const handleAiSubmit = async () => {
  const hasText = aiInputText.value && aiInputText.value.trim()
  const hasImages = aiImageFiles.value.length > 0

  if (!hasText && !hasImages) {
    window.showToast('请输入文本描述或上传图片', 'warning')
    return
  }

  aiParsing.value = true
  aiProgress.value = 0
  aiProgressStep.value = '准备解析...'

  // 进度模拟定时器
  const progressTimer = setInterval(() => {
    if (aiProgress.value < 90) {
      aiProgress.value += Math.random() * 5 + 2
      // 根据进度更新步骤提示
      if (aiProgress.value < 20) {
        aiProgressStep.value = '正在识别文本内容...'
      } else if (aiProgress.value < 40) {
        aiProgressStep.value = '正在调用 AI 模型...'
      } else if (aiProgress.value < 60) {
        aiProgressStep.value = '正在匹配客户信息...'
      } else if (aiProgress.value < 80) {
        aiProgressStep.value = '正在匹配商品信息...'
      } else {
        aiProgressStep.value = '正在整理订单数据...'
      }
    }
  }, 500)

  try {
    // 将图片转为 base64
    const images: string[] = []
    for (const file of aiImageFiles.value) {
      const base64 = await fileToBase64(file)
      images.push(base64)
    }

    aiProgress.value = 30
    aiProgressStep.value = '正在调用 AI 模型...'

    // 调用 AI 解析接口
    const result = await salesOrderApi.parseByAi({
      text: hasText ? aiInputText.value.trim() : undefined,
      images: images.length > 0 ? images : undefined,
    })

    aiProgress.value = 80
    aiProgressStep.value = '正在填充表单数据...'

    // 填充表单
    await fillFormWithAiResult(result)

    aiProgress.value = 100
    aiProgressStep.value = '解析完成！'

    // 短暂显示完成状态
    await new Promise(resolve => setTimeout(resolve, 300))

    showAiPanel.value = false
    window.showToast('AI解析完成，请核对并补充信息', 'success')
  } catch (error: any) {
    const msg = error?.message || 'AI解析失败，请重试或手动填写'
    window.showToast(msg, 'error')
  } finally {
    clearInterval(progressTimer)
    aiParsing.value = false
    aiProgress.value = 0
    aiProgressStep.value = ''
  }
}

// 检查是否有待确认项
const hasAiPendingItems = computed(() => {
  return aiPendingCustomer.value || aiPendingItems.value.size > 0
})

// ========== AI 解析方法结束 ==========

const openEditOrder = async (order: SalesOrder) => {
  // 先获取完整订单数据（列表数据不包含明细）
  let fullOrder = order
  if (!order.items || order.items.length === 0) {
    try {
      const res = await salesOrderApi.getByOrderNo(order.order_no)
      fullOrder = res
    } catch (error) {
      window.showToast('获取订单详情失败', 'error')
      return
    }
  }

  editingOrder.value = fullOrder

  // 发货方式中文转英文映射
  const shippingMethodReverseMap: Record<string, string> = {
    '直运': 'direct',
    '仓库发货': 'warehouse',
    '仓库自提': 'warehouse_pickup'
  }

  orderForm.value = {
    order_date: fullOrder.order_date,
    customer_id: fullOrder.customer_id,
    customer_name: fullOrder.customer_name || '',
    sale_user_id: fullOrder.sale_user_id || '',
    third_party_platform: (fullOrder as any).third_party_platform || '',
    platform_order_no: (fullOrder as any).platform_order_no || '',
    deliver_info: fullOrder.deliver_info ? { ...fullOrder.deliver_info } : { addr: '', province: '', city: '', person_name: '', person_tel: '' },
    expect_deliver_date: fullOrder.expect_deliver_date || '',
    settle_type: fullOrder.settle_type,
    invoice_info: fullOrder.invoice_info ? { ...fullOrder.invoice_info, address: fullOrder.invoice_info.address || '', phone: fullOrder.invoice_info.phone || '' } : { invoice_title: '', tax_number: '', invoice_type: '', bank_name: '', bank_account: '', address: '', phone: '' },
    remark: fullOrder.remark || '',
    items: (fullOrder.items || []).map(item => ({
      ...item,
      warehouse_name: item.warehouse_name || '',
      product_name: item.product_name || '',
      product_code: item.product_code || '',
      brand_name: item.brand_name || '',
      spec_code: item.spec_code || '',
      item_remark: (item as any).item_remark || '',
      // 发货方式中文转英文
      shipping_method: (shippingMethodReverseMap[item.shipping_method] || item.shipping_method || 'warehouse') as 'direct' | 'warehouse' | 'warehouse_pickup'
    }))
  }
  customerSearchKeyword.value = fullOrder.customer_name || ''

  // 补充商品的品牌信息、包装和销售规格
  const productIds = [...new Set(fullOrder.items?.map(item => item.product_id).filter(Boolean) || [])]
  const brandMap: Record<string, string> = {}
  const specMap: Record<string, { packaging: string; sales_spec: string }> = {}
  await Promise.all(productIds.map(async (pid: string) => {
    try {
      const res = await productApi.getById(pid)
      brandMap[pid] = res.result?.brand_name || ''
      const specs = res.result?.specs || []
      specs.forEach((s: any) => {
        if (s.id) {
          specMap[s.id] = { packaging: s.packaging || '', sales_spec: s.sales_spec || '' }
        }
      })
    } catch { /* ignore */ }
  }))
  orderForm.value.items.forEach(item => {
    if (!item.brand_name && item.product_id) {
      item.brand_name = brandMap[item.product_id] || ''
    }
    if (item.spec_id && specMap[item.spec_id]) {
      item.packaging = specMap[item.spec_id].packaging
      item.sales_spec = specMap[item.spec_id].sales_spec
    }
  })

  // 加载客户收货地址和开票信息用于下拉
  try {
    const res = await customerApi.getById(fullOrder.customer_id)
    const detail = res
    customerInvoiceInfos.value = detail?.invoice_infos || []
    customerShippingAddresses.value = detail?.shipping_addresses || []

    // 匹配当前订单的收货地址
    const matchedAddr = customerShippingAddresses.value.find(
      (a: any) => a.receiver === fullOrder.deliver_info?.person_name && a.phone === fullOrder.deliver_info?.person_tel
    )
    selectedShippingAddressId.value = matchedAddr?.id || ''

    // 匹配当前订单的开票信息（如果后端有返回）
    if (fullOrder.invoice_info?.invoice_title) {
      const matchedInv = customerInvoiceInfos.value.find(
        (i: any) => i.invoice_title === fullOrder.invoice_info?.invoice_title && i.tax_number === fullOrder.invoice_info?.tax_number
      )
      selectedInvoiceInfoId.value = matchedInv?.id || ''
    } else {
      selectedInvoiceInfoId.value = ''
    }
  } catch (e) {
    console.error('加载客户信息失败:', e)
    customerInvoiceInfos.value = []
    customerShippingAddresses.value = []
    selectedShippingAddressId.value = ''
    selectedInvoiceInfoId.value = ''
  }

  // 设置省份/城市
  selectedProvince.value = fullOrder.deliver_info?.province || ''
  if (fullOrder.deliver_info?.province) {
    cityList.value = getCities(fullOrder.deliver_info.province)
    selectedCity.value = fullOrder.deliver_info?.city || ''
  }

  // 设置运费（编辑模式使用原运费值，不自动重新计算）
  freightAmt.value = (fullOrder as any).freight_amt || 0
  isFreightManuallyModified.value = true

  showOrderModal.value = true
}

/**
 * 加单功能：基于已审核订单创建新订单
 * 复制客户信息、收货信息、开票信息，清空商品明细
 */
const handleAddOrder = async (order: SalesOrder) => {
  // 获取完整订单数据
  let fullOrder = order
  if (!order.deliver_info || !order.invoice_info) {
    try {
      const res = await salesOrderApi.getByOrderNo(order.order_no)
      fullOrder = res
    } catch (error) {
      window.showToast('获取订单详情失败', 'error')
      return
    }
  }

  // 重置表单状态
  resetOrderForm()

  // 预填充客户和订单信息
  orderForm.value = {
    order_date: new Date().toISOString().split('T')[0], // 使用当前日期
    customer_id: fullOrder.customer_id,
    customer_name: fullOrder.customer_name || '',
    sale_user_id: fullOrder.sale_user_id || '',
    third_party_platform: (fullOrder as any).third_party_platform || '',
    platform_order_no: '', // 平台订单号清空，新订单可能有不同的平台订单号
    deliver_info: fullOrder.deliver_info ? { ...fullOrder.deliver_info } : {
      addr: '',
      province: '',
      city: '',
      person_name: '',
      person_tel: ''
    },
    expect_deliver_date: '',
    settle_type: fullOrder.settle_type || '月结',
    invoice_info: fullOrder.invoice_info ? {
      invoice_title: fullOrder.invoice_info.invoice_title || '',
      invoice_type: fullOrder.invoice_info.invoice_type || '',
      tax_number: fullOrder.invoice_info.tax_number || '',
      bank_name: fullOrder.invoice_info.bank_name || '',
      bank_account: fullOrder.invoice_info.bank_account || '',
      address: fullOrder.invoice_info.address || '',
      phone: fullOrder.invoice_info.phone || ''
    } : {
      invoice_title: '',
      invoice_type: '',
      tax_number: '',
      bank_name: '',
      bank_account: '',
      address: '',
      phone: ''
    },
    remark: '', // 备注清空
    items: [] // 商品明细清空
  }

  // 设置客户搜索关键字
  customerSearchKeyword.value = fullOrder.customer_name || ''

  // 设置省份和城市
  if (fullOrder.deliver_info?.province) {
    selectedProvince.value = fullOrder.deliver_info.province
    cityList.value = getCities(fullOrder.deliver_info.province)
    selectedCity.value = fullOrder.deliver_info?.city || ''
  }

  // 加载客户收货地址和开票信息用于下拉选择
  try {
    const res = await customerApi.getById(fullOrder.customer_id)
    const detail = res
    customerInvoiceInfos.value = detail?.invoice_infos || []
    customerShippingAddresses.value = detail?.shipping_addresses || []

    // 匹配当前订单的收货地址
    const matchedAddr = customerShippingAddresses.value.find(
      (a: any) => a.receiver === fullOrder.deliver_info?.person_name && a.phone === fullOrder.deliver_info?.person_tel
    )
    selectedShippingAddressId.value = matchedAddr?.id || ''

    // 匹配当前订单的开票信息
    if (fullOrder.invoice_info?.invoice_title) {
      const matchedInv = customerInvoiceInfos.value.find(
        (i: any) => i.invoice_title === fullOrder.invoice_info?.invoice_title && i.tax_number === fullOrder.invoice_info?.tax_number
      )
      selectedInvoiceInfoId.value = matchedInv?.id || ''
    }
  } catch {
    // 忽略错误，不影响主流程
  }

  // editingOrder 保持 null，表示新建模式
  // 加单默认不计算运费
  isAddOrder.value = true
  isFreightManuallyModified.value = true
  showOrderModal.value = true
}

const confirmDelete = (orderNo: string) => {
  deleteTargetOrderNo.value = orderNo
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetOrderNo.value) return
  deleteLoading.value = true
  try {
    await salesOrderApi.delete(deleteTargetOrderNo.value)
    window.showToast('订单删除成功', 'success')
    loadOrders()
    showDeleteConfirm.value = false
    deleteTargetOrderNo.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const selectCustomer = async (customer: any) => {
  orderForm.value.customer_id = customer.id
  orderForm.value.customer_name = customer.customer_name
  customerSearchKeyword.value = customer.customer_name
  showCustomerDropdown.value = false
  // 清除客户待确认标记
  aiPendingCustomer.value = false

  try {
    // 获取客户详情（包含开票信息和收货地址）
    const res = await customerApi.getById(customer.id)
    const detail = res

    // 存储所有开票信息和收货地址
    customerInvoiceInfos.value = detail?.invoice_infos || []
    customerShippingAddresses.value = detail?.shipping_addresses || []

    // 自动填充开票信息（默认选中）
    if (customerInvoiceInfos.value.length > 0) {
      const defaultInvoice = customerInvoiceInfos.value.find((i: any) => i.is_default) || customerInvoiceInfos.value[0]
      if (defaultInvoice) {
        selectedInvoiceInfoId.value = defaultInvoice.id
        orderForm.value.invoice_info = {
          invoice_title: defaultInvoice.invoice_title,
          invoice_type: defaultInvoice.invoice_type,
          tax_number: defaultInvoice.tax_number,
          bank_name: defaultInvoice.bank_name,
          bank_account: defaultInvoice.bank_account,
          address: defaultInvoice.address || '',
          phone: defaultInvoice.phone || ''
        }
      }
    } else {
      selectedInvoiceInfoId.value = ''
    }

    // 自动填充收货信息（默认选中）
    if (customerShippingAddresses.value.length > 0) {
      const defaultAddr = customerShippingAddresses.value.find((a: any) => a.is_default) || customerShippingAddresses.value[0]
      if (defaultAddr) {
        selectedShippingAddressId.value = defaultAddr.id
        applyShippingAddress(defaultAddr)
      }
    } else {
      selectedShippingAddressId.value = ''
    }
  } catch (e) {
    console.error('获取客户详情失败:', e)
  }
}

// 选择收货地址下拉
const onShippingAddressChange = (addressId: string) => {
  const addr = customerShippingAddresses.value.find((a: any) => a.id === addressId)
  if (addr) {
    applyShippingAddress(addr)
  }
}

// 填充收货信息到订单
const applyShippingAddress = (addr: any) => {
  orderForm.value.deliver_info = {
    addr: addr.address,
    province: addr.province || '',
    city: addr.city || '',
    person_name: addr.receiver,
    person_tel: addr.phone
  }
  if (addr.province) {
    selectedProvince.value = addr.province
    // 延迟设置城市，等待省份watcher完成加载城市列表
    if (addr.city) {
      nextTick(() => {
        selectedCity.value = addr.city
      })
    }
  } else {
    selectedProvince.value = ''
    selectedCity.value = ''
  }
}

// 选择开票信息下拉
const onInvoiceInfoChange = (invoiceId: string) => {
  const inv = customerInvoiceInfos.value.find((i: any) => i.id === invoiceId)
  if (inv) {
    orderForm.value.invoice_info = {
      invoice_title: inv.invoice_title,
      invoice_type: inv.invoice_type,
      tax_number: inv.tax_number,
      bank_name: inv.bank_name,
      bank_account: inv.bank_account,
      address: inv.address,
      phone: inv.phone
    }
  }
}

// Quick add shipping address
const saveQuickAddShipping = async () => {
  if (!orderForm.value.customer_id) return
  if (!quickAddShippingForm.value.recipient_name || !quickAddShippingForm.value.recipient_phone || !quickAddShippingForm.value.address) {
    window.showToast('请填写收货人、联系电话和详细地址', 'warning')
    return
  }
  quickAddLoading.value = true
  try {
    // 转换字段名：前端 recipient_name/recipient_phone -> 后端 receiver/phone
    const submitData = {
      receiver: quickAddShippingForm.value.recipient_name,
      phone: quickAddShippingForm.value.recipient_phone,
      province: quickAddShippingForm.value.province,
      city: quickAddShippingForm.value.city,
      address: quickAddShippingForm.value.address,
      is_default: quickAddShippingForm.value.is_default
    }
    const res = await customerApi.addShippingAddress(orderForm.value.customer_id, submitData)
    const newAddr = res.result
    // 刷新客户地址列表
    const detailRes = await customerApi.getById(orderForm.value.customer_id)
    customerShippingAddresses.value = detailRes.result?.shipping_addresses || []
    // 选中新添加的地址
    selectedShippingAddressId.value = newAddr.id
    onShippingAddressChange(newAddr.id)
    showQuickAddShippingModal.value = false
    resetQuickAddShippingForm()
    window.showToast('收货地址新增成功', 'success')
  } catch (e: any) {
    window.showToast(e.message || '新增失败', 'error')
  } finally {
    quickAddLoading.value = false
  }
}

const resetQuickAddShippingForm = () => {
  quickAddShippingForm.value = {
    recipient_name: '',
    recipient_phone: '',
    province: '',
    city: '',
    address: '',
    is_default: false
  }
  quickAddSelectedProvince.value = ''
  quickAddSelectedCity.value = ''
  quickAddCityList.value = []
}

// ========== 收货地址 AI 解析方法 ==========

// 切换收货地址 AI 面板显示
const toggleShippingAiPanel = () => {
  showShippingAiPanel.value = !showShippingAiPanel.value
  if (showShippingAiPanel.value) {
    shippingAiInputText.value = ''
    shippingAiImageFiles.value = []
    shippingAiImagePreviews.value = []
  }
}

// 处理收货地址 AI 图片选择
const handleShippingAiImageSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files) return

  const newFiles = Array.from(input.files)
  if (shippingAiImageFiles.value.length + newFiles.length > 3) {
    window.showToast('最多支持3张图片', 'warning')
    return
  }

  for (const file of newFiles) {
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`图片 ${file.name} 超过5MB限制`, 'warning')
      continue
    }
    shippingAiImageFiles.value.push(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      shippingAiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  input.value = ''
}

// 删除收货地址 AI 图片
const removeShippingAiImage = (index: number) => {
  shippingAiImageFiles.value.splice(index, 1)
  shippingAiImagePreviews.value.splice(index, 1)
}

// 处理收货地址 AI 粘贴图片
const handleShippingAiPaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  const imageFiles: File[] = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) imageFiles.push(file)
    }
  }

  if (imageFiles.length === 0) return

  event.preventDefault()

  if (shippingAiImageFiles.value.length + imageFiles.length > 3) {
    window.showToast('最多支持3张图片', 'warning')
    return
  }

  for (const file of imageFiles) {
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`粘贴的图片超过5MB限制`, 'warning')
      continue
    }
    shippingAiImageFiles.value.push(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      shippingAiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  window.showToast(`已粘贴${imageFiles.length}张图片`, 'success')
}

// 收货地址 AI 解析提交
const handleShippingAiSubmit = async () => {
  const hasText = shippingAiInputText.value && shippingAiInputText.value.trim()
  const hasImages = shippingAiImageFiles.value.length > 0

  if (!hasText && !hasImages) {
    window.showToast('请输入文本描述或上传图片', 'warning')
    return
  }

  shippingAiParsing.value = true

  try {
    const images: string[] = []
    for (const file of shippingAiImageFiles.value) {
      const base64 = await fileToBase64(file)
      images.push(base64)
    }

    const result = await customerApi.parseShippingAddressByAi({
      text: hasText ? shippingAiInputText.value.trim() : undefined,
      images: images.length > 0 ? images : undefined,
    })

    // 填充表单
    if (result.receiver) quickAddShippingForm.value.recipient_name = result.receiver
    if (result.phone) quickAddShippingForm.value.recipient_phone = result.phone
    if (result.province) {
      quickAddSelectedProvince.value = result.province
      quickAddShippingForm.value.province = result.province
    }
    if (result.city) {
      await nextTick()
      quickAddSelectedCity.value = result.city
      quickAddShippingForm.value.city = result.city
    }
    if (result.address) quickAddShippingForm.value.address = result.address

    showShippingAiPanel.value = false
    window.showToast('AI解析完成，请核对信息', 'success')
  } catch (error: any) {
    const msg = error?.message || 'AI解析失败，请重试或手动填写'
    window.showToast(msg, 'error')
  } finally {
    shippingAiParsing.value = false
  }
}

// Quick add invoice info
const saveQuickAddInvoice = async () => {
  if (!orderForm.value.customer_id) return
  if (!quickAddInvoiceForm.value.invoice_title || !quickAddInvoiceForm.value.invoice_type || !quickAddInvoiceForm.value.tax_number) {
    window.showToast('请填写发票抬头、开票类型和纳税人识别号', 'warning')
    return
  }
  quickAddLoading.value = true
  try {
    const res = await customerApi.addInvoiceInfo(orderForm.value.customer_id, quickAddInvoiceForm.value)
    const newInv = res.result
    // 刷新客户开票信息列表
    const detailRes = await customerApi.getById(orderForm.value.customer_id)
    customerInvoiceInfos.value = detailRes.result?.invoice_infos || []
    // 选中新添加的开票信息
    selectedInvoiceInfoId.value = newInv.id
    onInvoiceInfoChange(newInv.id)
    showQuickAddInvoiceModal.value = false
    resetQuickAddInvoiceForm()
    window.showToast('开票信息新增成功', 'success')
  } catch (e: any) {
    window.showToast(e.message || '新增失败', 'error')
  } finally {
    quickAddLoading.value = false
  }
}

const resetQuickAddInvoiceForm = () => {
  quickAddInvoiceForm.value = {
    invoice_title: '',
    invoice_type: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    is_default: false
  }
}

const addOrderItem = () => {
  orderForm.value.items.push({
    row_no: orderForm.value.items.length + 1,
    product_id: '',
    spec_id: '',
    qty: 1,
    price: 0,
    discount: 1,
    discounted_price: 0,
    amt: 0,
    warehouse_id: '',
    shipping_method: 'direct',
    out_qty: 0,
    return_qty: 0,
    remain_out_qty: 0
  })
}

const removeOrderItem = (index: number) => {
  orderForm.value.items.splice(index, 1)
  // 更新行号
  orderForm.value.items.forEach((item, i) => {
    item.row_no = i + 1
  })
}

const updateItemAmount = (index: number) => {
  const item = orderForm.value.items[index]
  item.discounted_price = item.price * item.discount
  item.amt = item.qty * item.discounted_price
}

const updateItemDiscountByPrice = (index: number) => {
  const item = orderForm.value.items[index]
  if (item.price > 0) {
    item.discount = Math.round((item.discounted_price / item.price) * 100) / 100
  } else {
    item.discount = 1
  }
  item.amt = item.qty * item.discounted_price
}

const totalAmount = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + (item.amt || 0), 0)
})

const totalQty = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + (item.qty || 0), 0)
})

const totalDiscountAmount = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + ((item.price || 0) - (item.discounted_price || 0)) * (item.qty || 0), 0)
})

// 运费自动计算
let freightCalcTimer: ReturnType<typeof setTimeout> | null = null
const calculateFreight = async () => {
  if (isFreightManuallyModified.value) return

  if (freightCalcTimer) clearTimeout(freightCalcTimer)
  freightCalcTimer = setTimeout(async () => {
    const brandIds = new Set<string>()
    orderForm.value.items.forEach(item => {
      if (item.brand_id) brandIds.add(String(item.brand_id))
    })

    let total = 0
    for (const brandId of brandIds) {
      try {
        // 使用缓存避免重复请求
        if (!brandFreightCache.value[brandId]) {
          const res = await brandApi.getById(brandId)
          brandFreightCache.value[brandId] = res?.default_freight || 0
        }
        total += brandFreightCache.value[brandId]
      } catch (e) {
        console.error('获取品牌运费失败:', e)
      }
    }
    freightAmt.value = total
  }, 300)
}

// 监听商品明细变化，自动计算运费
watch(() => orderForm.value.items, calculateFreight, { deep: true })

// 开始编辑运费
const startEditFreight = () => {
  isEditingFreight.value = true
  isFreightManuallyModified.value = true
  nextTick(() => {
    freightInputRef.value?.focus()
  })
}

// 最终金额计算（包含运费）
const finalAmount = computed(() => {
  return totalAmount.value - totalDiscountAmount.value + freightAmt.value
})

const handleSaveOrder = async () => {
  // 检查是否存在 AI 解析待确认项
  if (hasAiPendingItems.value) {
    if (aiPendingCustomer.value) {
      window.showToast('客户信息待确认，请选择客户', 'warning')
      return
    }
    if (aiPendingItems.value.size > 0) {
      window.showToast(`第${Array.from(aiPendingItems.value).map(i => i + 1).join('、')}行商品待确认，请选择商品规格`, 'warning')
      return
    }
  }

  if (!orderForm.value.customer_id) {
    window.showToast('请选择客户', 'warning')
    return
  }
  if (orderForm.value.items.length === 0) {
    window.showToast('请添加商品明细', 'warning')
    return
  }

  for (let i = 0; i < orderForm.value.items.length; i++) {
    const item = orderForm.value.items[i]
    if (!item.product_id) {
      window.showToast(`第${i + 1}行商品未选择`, 'warning')
      return
    }
    if (!item.spec_id) {
      window.showToast(`第${i + 1}行商品规格未选择`, 'warning')
      return
    }
    if (!item.qty || item.qty <= 0) {
      window.showToast(`第${i + 1}行商品数量必须大于0`, 'warning')
      return
    }
    if (item.shipping_method !== 'direct' && !item.warehouse_id) {
      window.showToast(`第${i + 1}行请选择仓库`, 'warning')
      return
    }
  }

  formLoading.value = true
  try {
    const submitData = {
      order_date: orderForm.value.order_date,
      customer_id: orderForm.value.customer_id,
      customer_name: orderForm.value.customer_name,
      sale_user_id: orderForm.value.sale_user_id || undefined,
      third_party_platform: orderForm.value.third_party_platform || undefined,
      platform_order_no: orderForm.value.platform_order_no || undefined,
      deliver_info: orderForm.value.deliver_info,
      invoice_info: orderForm.value.invoice_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      freight_amt: freightAmt.value,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        spec_id: item.spec_id ? Number(item.spec_id) : undefined,
        product_code: item.product_code || undefined,
        spec_code: item.spec_code || undefined,
        warehouse_id: item.warehouse_id ? Number(item.warehouse_id) : undefined,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        shipping_method: item.shipping_method,
        item_remark: item.item_remark || undefined
      }))
    }

    if (editingOrder.value) {
      await salesOrderApi.update(editingOrder.value.order_no, submitData)
      window.showToast('订单更新成功', 'success')
    } else {
      await salesOrderApi.create(submitData)
      window.showToast('订单创建成功', 'success')
    }

    loadOrders()
    showOrderModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleSaveAndSubmit = async () => {
  // 检查是否所有明细发货方式为直运
  const allDirect = orderForm.value.items.length > 0 &&
    orderForm.value.items.every(item => item.shipping_method === 'direct')

  if (allDirect) {
    showAllDirectConfirm.value = true
  } else {
    await executeSaveAndSubmit()
  }
}

// 全直运订单确认提交
const confirmAllDirectSubmit = async () => {
  showAllDirectConfirm.value = false
  await executeSaveAndSubmit()
}

// 实际执行保存并提交
const executeSaveAndSubmit = async () => {
  // 检查是否存在 AI 解析待确认项
  if (hasAiPendingItems.value) {
    if (aiPendingCustomer.value) {
      window.showToast('客户信息待确认，请选择客户', 'warning')
      return
    }
    if (aiPendingItems.value.size > 0) {
      window.showToast(`第${Array.from(aiPendingItems.value).map(i => i + 1).join('、')}行商品待确认，请选择商品规格`, 'warning')
      return
    }
  }

  if (!orderForm.value.customer_id) {
    window.showToast('请选择客户', 'warning')
    return
  }
  if (orderForm.value.items.length === 0) {
    window.showToast('请添加商品明细', 'warning')
    return
  }

  for (let i = 0; i < orderForm.value.items.length; i++) {
    const item = orderForm.value.items[i]
    if (!item.product_id) {
      window.showToast(`第${i + 1}行商品未选择`, 'warning')
      return
    }
    if (!item.qty || item.qty <= 0) {
      window.showToast(`第${i + 1}行数量必须大于0`, 'warning')
      return
    }
  }

  formLoading.value = true
  try {
    const submitData = {
      order_date: orderForm.value.order_date,
      customer_id: orderForm.value.customer_id,
      customer_name: orderForm.value.customer_name,
      sale_user_id: orderForm.value.sale_user_id || undefined,
      third_party_platform: orderForm.value.third_party_platform || undefined,
      platform_order_no: orderForm.value.platform_order_no || undefined,
      deliver_info: orderForm.value.deliver_info,
      invoice_info: orderForm.value.invoice_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      freight_amt: freightAmt.value,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        spec_id: item.spec_id ? Number(item.spec_id) : undefined,
        product_code: item.product_code || undefined,
        spec_code: item.spec_code || undefined,
        warehouse_id: item.warehouse_id ? Number(item.warehouse_id) : undefined,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        shipping_method: item.shipping_method,
        item_remark: item.item_remark || undefined
      }))
    }

    if (editingOrder.value) {
      // 编辑模式：先保存再审核
      await salesOrderApi.update(editingOrder.value.order_no, submitData)
      await salesOrderApi.approve(editingOrder.value.order_no)
      window.showToast('订单更新并提交成功', 'success')
    } else {
      // 新建模式：使用 createAndSubmit
      await salesOrderApi.createAndSubmit(submitData)
      window.showToast('订单创建并提交成功', 'success')
    }

    loadOrders()
    showOrderModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmAudit = (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  showAuditConfirm.value = true
}

const handleAuditOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.approve(actionTargetOrderNo.value)
    window.showToast('订单审核成功', 'success')
    showAuditConfirm.value = false
    loadOrders()
    // 更新详情弹窗状态
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'audited' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}

const confirmClose = (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  showCloseConfirm.value = true
}

const handleCloseOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.cancel(actionTargetOrderNo.value)
    window.showToast('订单关闭成功', 'success')
    showCloseConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'closed' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '关闭失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}

const confirmCancel = (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  showCancelConfirm.value = true
}

const confirmPushPurchase = async (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  actionLoading.value = true
  try {
    const fullOrder = await salesOrderApi.getByOrderNo(orderNo)
    const items = fullOrder.items || []

    // 订单明细已包含 brand_id 和 brand_name，无需再调用产品详情接口
    // 从订单详情返回的 brand_purchasers 获取采购员信息
    const brandPurchasers = fullOrder.brand_purchasers || {}

    const enrichedItems = items.map((item: any) => ({
      ...item,
      purchaser_name: item.brand_id && brandPurchasers[item.brand_id]
        ? brandPurchasers[item.brand_id].purchaser_name || ''
        : ''
    }))

    // 筛选可下推的明细（未下推）
    pushableItems.value = enrichedItems.filter((item: any) => !item.pushed)

    if (pushableItems.value.length === 0) {
      window.showToast('没有可下推采购的商品明细', 'warning')
      actionLoading.value = false
      actionTargetOrderNo.value = null
      return
    }

    showPushItemSelect.value = true
  } catch (error: any) {
    window.showToast(error.message || '获取订单详情失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

const handlePushPurchase = async (selectedRowNos: number[]) => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    const items = selectedRowNos.map(row_no => ({ row_no }))
    const result = await salesOrderApi.pushToPurchase(actionTargetOrderNo.value, items)
    // result 是采购单列表数组
    const purchaseCount = Array.isArray(result) ? result.length : (result?.purchase_orders?.length || 0)
    window.showToast(`下推采购成功，共生成${purchaseCount}张采购单`, 'success')
    showPushItemSelect.value = false
    pushableItems.value = []
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '下推采购失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}

const handleClosePushItemSelect = () => {
  showPushItemSelect.value = false
  pushableItems.value = []
}

const handleCancelOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.cancel(actionTargetOrderNo.value)
    window.showToast('订单取消成功', 'success')
    showCancelConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'cancelled' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '取消失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}

// 提交审核
const handleSubmitOrder = async (orderNo: string) => {
  actionLoading.value = true
  try {
    await salesOrderApi.submit(orderNo)
    window.showToast('订单已提交审核', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '提交失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

// 驳回确认
const confirmReject = (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  showRejectConfirm.value = true
}

// 驳回订单
const handleRejectOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.reject(actionTargetOrderNo.value)
    window.showToast('订单已驳回', 'success')
    showRejectConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'draft' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}

const refreshFlows = async (orderNo: string) => {
  try {
    const flowRes = await salesOrderApi.getStatusFlows(orderNo)
    selectedOrderFlows.value = flowRes || []
  } catch (e) {
    console.error('刷新流转记录失败:', e)
  }
}

// 合同按钮点击（功能预留）
const handleContract = (order: SalesOrder) => {
  window.showToast('合同功能开发中，敬请期待', 'info')
}

// 发货按钮点击（功能预留）
const handleShip = (order: SalesOrder) => {
  window.showToast('发货功能开发中，敬请期待', 'info')
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatAmount = (amount: number | undefined | null) => {
  if (amount === undefined || amount === null) return '-'
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const getOrderStatusInfo = (status: string) => orderStatusMap[status] || { label: status, class: '' }
const getDeliveryStatusInfo = (status: string) => deliveryStatusMap[status] || { label: status, class: '' }
const getPushStatusInfo = (status: string | undefined) => pushStatusMap[status || 'none'] || { label: status || '未下推', class: 'none' }
const getInvoiceStatusInfo = (status: string) => invoiceStatusMap[status] || { label: status, class: '' }
const getFinanceStatusInfo = (status: string) => financeStatusMap[status] || { label: status || '未付款', class: 'none' }

const statusFieldLabel = (field: string) => {
  const map: Record<string, string> = {
    order_status: '订单状态',
    delivery_status: '发货状态',
    push_status: '下推状态',
    invoice_status: '开票状态',
    finance_status: '财务状态'
  }
  return map[field] || field
}

// Lifecycle
onMounted(async () => {
  loadOrders()
  loadCustomers()
  loadWarehouses()
  loadUsers()
  // 加载省份列表
  try {
    await loadProvinceCityData()
    provinceList.value = getProvinces()
  } catch (e) {
    console.error('加载省份失败:', e)
  }
  document.addEventListener('click', handleclickOutside)
})

onActivated(() => {
  loadOrders()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleclickOutside)
})
</script>

<template>
  <div class="sales-order-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">销售订单管理</h2>
      <button class="primary-btn" @click="openCreateOrder">新建销售订单</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索订单号、客户名称、产品编号..."
            v-model="filterKeyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <select class="filter-select" v-model="filterCustomerId" @change="handleSearch">
          <option value="">全部客户</option>
          <option v-for="c in customerList" :key="c.id" :value="c.id">{{ c.customer_name }}</option>
        </select>
        <select class="filter-select" v-model="filterStatus" @change="handleSearch">
          <option value="">订单状态</option>
          <option v-for="s in orderStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <select class="filter-select" v-model="filterInvoiceStatus" @change="handleSearch">
          <option value="">发票状态</option>
          <option v-for="s in invoiceStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <select class="filter-select" v-model="filterDeliveryStatus" @change="handleSearch">
          <option value="">发货状态</option>
          <option v-for="s in deliveryStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <select class="filter-select" v-model="filterSaleUserId" @change="handleSearch" v-if="isAdmin">
          <option value="">全部业务员</option>
          <option v-for="u in userList" :key="u.id" :value="u.id">{{ u.name }}</option>
        </select>
        <div class="filter-item">
          <input type="date" class="filter-input" v-model="filterOrderDateStart" @change="handleSearch" />
        </div>
        <div class="filter-item">
          <input type="date" class="filter-input" v-model="filterOrderDateEnd" @change="handleSearch" />
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
        <button
          class="filter-btn primary-btn"
          @click="handleBatchSubmit"
          v-if="selectedRows.length > 0"
        >
          批量提交审核 ({{ selectedRows.length }})
        </button>
      </div>
    </div>

    <div class="table-section" style="position: relative;">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>

      <!-- 顶部滚动条表格 -->
      <div class="top-scrollbar-area">
        <vxe-table
          ref="topTableRef"
          :data="topDummyData"
          :scroll-x="{ enabled: true }"
          :scrollbar-config="{ x: { position: 'top' } }"
          :show-header="false"
          height="20"
          @scroll="handleTopScroll"
        >
          <vxe-column width="50" />
          <vxe-column width="160" />
          <vxe-column width="50" />
          <vxe-column width="120" />
          <vxe-column min-width="150" />
          <vxe-column min-width="180" />
          <vxe-column width="120" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="100" />
          <vxe-column width="240" />
        </vxe-table>
      </div>

      <!-- 主表格 -->
      <vxe-table
        ref="tableRef"
        :data="orders"
        :column-config="{ resizable: true }"
        :row-config="{ isHover: true }"
        :expand-config="{}"
        :scroll-x="{ enabled: true, gt: 0 }"
        :checkbox-config="{ reserve: true }"
        @checkbox-change="handleCheckboxChange"
        @scroll="handleTableScroll"
      >
        <vxe-column type="checkbox" width="50" fixed="left" class-name="col--center" />
        <vxe-column field="order_no" title="订单编号" width="160" class-name="col--center">
          <template #default="{ row }">
            <span class="order-link" @click="emit('navigate', 'sales-order-detail', { orderNo: row.order_no })">{{ row.order_no }}</span>
          </template>
        </vxe-column>
        <vxe-column type="expand" width="50" class-name="col--center">
          <template #content="{ row }">
            <div class="expand-items-panel">
              <table class="expand-items-table">
                <thead>
                  <tr>
                    <th style="width: 100px">品牌名</th>
                    <th style="width: 100px">规格编号</th>
                    <th style="width: 100px">产品名称</th>
                    <th style="width: 80px">规格</th>
                    <th style="width: 80px">包装单位</th>
                    <th style="width: 60px; text-align: right">数量</th>
                    <th style="width: 80px; text-align: right">原价</th>
                    <th style="width: 100px; text-align: right">退/换/补货数量</th>
                    <th style="width: 80px; text-align: right">含税单价</th>
                    <th style="width: 80px; text-align: right">合计</th>
                    <th style="width: 80px; text-align: right">退货方式</th>
                    <th style="width: 80px; text-align: right">退货金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in row.items" :key="idx">
                    <td>{{ item.brand_name || '-' }}</td>
                    <td>{{ item.spec_code || '-' }}</td>
                    <td>{{ item.product_name || '-' }}</td>
                    <td>{{ item.sales_spec || '-' }}</td>
                    <td>{{ item.packaging || '-' }}</td>
                    <td style="text-align: right">{{ item.qty }}</td>
                    <td style="text-align: right">{{ formatAmount(item.price) }}</td>
                    <td style="text-align: right">
                      <span v-if="item.return_qty || item.exchange_qty || item.supplement_qty">
                        <span v-if="item.return_qty">退{{ item.return_qty }}</span>
                        <span v-if="item.exchange_qty"> 换{{ item.exchange_qty }}</span>
                        <span v-if="item.supplement_qty"> 补{{ item.supplement_qty }}</span>
                      </span>
                      <span v-else>-</span>
                    </td>
                    <td style="text-align: right">{{ formatAmount(item.discounted_price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.amt) }}</td>
                    <td style="text-align: right">{{ (item as any).return_method || '-' }}</td>
                    <td style="text-align: right">{{ formatAmount((item as any).return_amt || 0) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </vxe-column>
        <vxe-column field="order_date" title="订单日期" width="120" class-name="col--center">
          <template #default="{ row }">
            {{ formatDate(row.order_date) }}
          </template>
        </vxe-column>
        <vxe-column field="customer_name" title="客户名称" min-width="150" class-name="col--center" />
        <vxe-column field="deliver_info" title="收件信息" min-width="180" class-name="col--center">
          <template #default="{ row }">
            <span v-if="row.deliver_info && (row.deliver_info.person_name || row.deliver_info.person_tel)">
              {{ row.deliver_info.person_name }} {{ row.deliver_info.person_tel ? `(${row.deliver_info.person_tel})` : '' }}
            </span>
            <span v-else>-</span>
          </template>
        </vxe-column>
        <vxe-column field="total_tax_amt" title="订单金额" width="120" class-name="col--right">
          <template #default="{ row }">
            {{ formatAmount(row.total_tax_amt) }}
          </template>
        </vxe-column>
        <vxe-column field="order_status" title="订单状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getOrderStatusInfo(row.order_status).class">
              {{ getOrderStatusInfo(row.order_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="cost_amt" title="成本" width="100" class-name="col--right">
          <template #default="{ row }">
            {{ formatAmount(row.cost_amt || 0) }}
          </template>
        </vxe-column>
        <vxe-column field="profit_amt" title="利润" width="100" class-name="col--right">
          <template #default="{ row }">
            <span :class="{ 'profit-positive': (row.profit_amt || 0) > 0, 'profit-negative': (row.profit_amt || 0) < 0 }">
              {{ formatAmount(row.profit_amt || 0) }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="finance_status" title="财务状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getFinanceStatusInfo(row.finance_status).class">
              {{ getFinanceStatusInfo(row.finance_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="invoice_status" title="发票状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getInvoiceStatusInfo(row.invoice_status).class">
              {{ getInvoiceStatusInfo(row.invoice_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="delivery_status" title="发货状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getDeliveryStatusInfo(row.delivery_status).class">
              {{ getDeliveryStatusInfo(row.delivery_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="push_status" title="下推状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getPushStatusInfo(row.push_status).class">
              {{ getPushStatusInfo(row.push_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="sale_user_name" title="业务员" width="100" class-name="col--center">
          <template #default="{ row }">
            {{ row.sale_user_name || '-' }}
          </template>
        </vxe-column>
        <vxe-column title="操作" width="320" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="emit('navigate', 'sales-order-detail', { orderNo: row.order_no })">详情</button>
              <!-- 编辑按钮：草稿状态 或 已审核且未下推状态可见 -->
              <button class="btn-link" @click="openEditOrder(row)" v-if="row.order_status === 'draft' || (row.order_status === 'audited' && (row.push_status === 'none' || !row.push_status))">编辑</button>
              <button class="btn-link success" @click="handleSubmitOrder(row.order_no)" v-if="row.order_status === 'draft'">提交审核</button>
              <!-- 兼容历史数据：pending 状态显示审核通过按钮 -->
              <button class="btn-link success" @click="confirmAudit(row.order_no)" v-if="row.order_status === 'pending'">审核通过</button>
              <button class="btn-link primary" @click="confirmPushPurchase(row.order_no)" v-if="(row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase') && (row.push_status === 'none' || row.push_status === 'partial')">下推采购</button>
              <!-- 加单按钮：已审核状态可见，用于基于当前订单创建新订单 -->
              <button class="btn-link" @click="handleAddOrder(row)" v-if="row.order_status === 'audited'">加单</button>
              <!-- 合同按钮：已审核状态可见，功能预留 -->
              <button class="btn-link" @click="handleContract(row)" v-if="row.order_status === 'audited'">合同</button>
              <!-- 发货按钮：已审核且未发货/部分发货状态可见，功能预留 -->
              <button class="btn-link" @click="handleShip(row)" v-if="row.order_status === 'audited' && (row.delivery_status === 'none' || row.delivery_status === 'partial')">发货</button>
              <!-- 取消按钮仅限草稿状态 -->
              <button class="btn-link danger" @click="confirmCancel(row.order_no)" v-if="row.order_status === 'draft'">取消</button>
              <button class="btn-link danger" @click="confirmDelete(row.order_no)" v-if="row.order_status === 'draft'">删除</button>
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

    <!-- Order Form Modal -->
    <div class="modal-overlay" v-if="showOrderModal">
      <div class="modal order-modal">
        <div class="modal-header">
          <div class="modal-header-left">
            <h3>{{ editingOrder ? '编辑销售订单' : '新建销售订单' }}</h3>
            <button v-if="!editingOrder" class="ai-btn" @click="toggleAiPanel" :class="{ active: showAiPanel }">
              AI
            </button>
          </div>
          <button class="modal-close" @click="showOrderModal = false">&times;</button>
        </div>

        <!-- AI 智能解析面板 -->
        <div class="ai-panel" v-if="showAiPanel && !editingOrder">
          <div class="ai-panel-header">
            <span class="ai-panel-title">AI 智能解析</span>
            <button class="btn-link" @click="showAiPanel = false" :disabled="aiParsing">收起</button>
          </div>

          <!-- 解析中状态 -->
          <div class="ai-thinking" v-if="aiParsing">
            <div class="ai-thinking-animation">
              <div class="ai-thinking-dot"></div>
              <div class="ai-thinking-dot"></div>
              <div class="ai-thinking-dot"></div>
            </div>
            <div class="ai-thinking-text">
              <span class="ai-thinking-label">Thinking</span>
              <span class="ai-thinking-ellipsis">
                <span class="ai-ellipsis-dot">.</span>
                <span class="ai-ellipsis-dot">.</span>
                <span class="ai-ellipsis-dot">.</span>
              </span>
            </div>
            <!-- 进度条 -->
            <div class="ai-progress-container">
              <div class="ai-progress-bar">
                <div class="ai-progress-fill" :style="{ width: aiProgress + '%' }"></div>
              </div>
              <span class="ai-progress-percent">{{ Math.round(aiProgress) }}%</span>
            </div>
            <p class="ai-thinking-step">{{ aiProgressStep }}</p>
          </div>

          <!-- 正常输入状态 -->
          <div class="ai-panel-body" v-else>
            <!-- 文本输入 -->
            <div class="ai-section">
              <label class="ai-label">文本描述</label>
              <textarea
                v-model="aiInputText"
                class="ai-textarea"
                placeholder="粘贴订单信息，或直接 Ctrl+V 粘贴图片..."
                rows="4"
                @paste="handleAiPaste"
              ></textarea>
            </div>
            <!-- 图片上传 -->
            <div class="ai-section">
              <label class="ai-label">图片（最多3张）</label>
              <div class="ai-image-upload-area">
                <div class="ai-image-list">
                  <div
                    v-for="(preview, index) in aiImagePreviews"
                    :key="index"
                    class="ai-image-item"
                  >
                    <img :src="preview" alt="预览" class="ai-image-preview" />
                    <button class="ai-image-remove" @click="removeAiImage(index)" title="删除">&times;</button>
                  </div>
                  <!-- 添加按钮（未满3张时显示） -->
                  <label v-if="aiImageFiles.length < 3" class="ai-image-add">
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      class="ai-file-input"
                      @change="handleAiImageSelect"
                    />
                    <span class="ai-image-add-icon">+</span>
                    <span class="ai-image-add-text">上传图片</span>
                  </label>
                </div>
                <p class="ai-image-hint">支持订单截图、聊天记录等，最多3张，单张不超过5MB</p>
              </div>
            </div>
            <!-- 提交按钮 -->
            <div class="ai-actions">
              <button class="btn-primary" @click="handleAiSubmit" :disabled="!aiInputText?.trim() && aiImageFiles.length === 0">
                AI 解析
              </button>
              <button class="btn-secondary" @click="toggleAiPanel">取消</button>
            </div>
          </div>
        </div>

        <div class="modal-body" v-else>
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>订单日期 *</label>
                <input type="date" class="date-input" v-model="orderForm.order_date" />
              </div>
              <div class="form-group">
                <label>客户 *</label>
                <div class="search-select" :class="{ 'ai-pending': aiPendingCustomer }">
                  <input
                    type="text"
                    v-model="customerSearchKeyword"
                    @input="handleCustomerSearch"
                    @focus="showCustomerDropdown = true; loadCustomers(customerSearchKeyword || undefined)"
                    placeholder="输入客户名称/编码搜索"
                    :class="{ 'ai-pending-input': aiPendingCustomer }"
                  />
                  <span v-if="aiPendingCustomer" class="ai-pending-badge">待确认</span>
                  <div class="search-dropdown" v-if="showCustomerDropdown && filteredCustomers.length > 0">
                    <div
                      v-for="c in filteredCustomers"
                      :key="c.id"
                      class="search-option"
                      @click="selectCustomer(c)"
                    >
                      {{ c.customer_name }} ({{ c.customer_code }})
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>期望交货日期</label>
                <input type="date" class="date-input" v-model="orderForm.expect_deliver_date" />
              </div>
              <div class="form-group">
                <label>结算方式 *</label>
                <select v-model="orderForm.settle_type">
                  <option v-for="s in settleTypeOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>第三方平台</label>
                <select v-model="orderForm.third_party_platform">
                  <option value="">请选择平台</option>
                  <option v-for="p in thirdPartyPlatformOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>平台订单号</label>
                <input type="text" v-model="orderForm.platform_order_no" placeholder="请输入平台订单号" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-title">收货信息 / 开票信息</div>
            <div class="form-row">
              <div class="form-group" style="flex: 1;">
                <label>选择收货地址</label>
                <div style="display: flex; gap: 4px;">
                  <select v-model="selectedShippingAddressId" @change="onShippingAddressChange(selectedShippingAddressId)" :disabled="!orderForm.customer_id" style="flex: 1;">
                    <option value="">请选择收货地址</option>
                    <option v-for="addr in customerShippingAddresses" :key="addr.id" :value="addr.id">
                      {{ addr.receiver }} - {{ addr.phone }} - {{ addr.province || '' }} {{ addr.city || '' }} {{ addr.address }}{{ addr.is_default ? ' (默认)' : '' }}
                    </option>
                  </select>
                  <button type="button" class="btn-quick-add" @click="showQuickAddShippingModal = true" :disabled="!orderForm.customer_id" title="新增收货地址">+</button>
                </div>
              </div>
              <div class="form-group" style="flex: 1;">
                <label>选择开票信息</label>
                <div style="display: flex; gap: 4px;">
                  <select v-model="selectedInvoiceInfoId" @change="onInvoiceInfoChange(selectedInvoiceInfoId)" :disabled="!orderForm.customer_id" style="flex: 1;">
                    <option value="">请选择开票信息</option>
                    <option v-for="inv in customerInvoiceInfos" :key="inv.id" :value="inv.id">
                      {{ inv.invoice_title }} - {{ inv.invoice_type }}{{ inv.is_default ? ' (默认)' : '' }}
                    </option>
                  </select>
                  <button type="button" class="btn-quick-add" @click="showQuickAddInvoiceModal = true" :disabled="!orderForm.customer_id" title="新增开票信息">+</button>
                </div>
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-title">商品明细</div>
            <div class="items-table">
              <table>
                <thead>
                  <tr>
                    <th style="width: 60px">行号</th>
                    <th style="width: 40px"></th>
                    <th style="width: 250px">商品</th>
                    <th style="width: 100px">品牌</th>
                    <th style="width: 200px">规格编号</th>
                    <th style="width: 120px">包装和包装单位</th>
                    <th style="width: 80px">数量</th>
                    <th style="width: 100px">单价</th>
                    <th style="width: 80px">折扣</th>
                    <th style="width: 100px">折后价</th>
                    <th style="width: 100px">金额</th>
                    <th style="width: 150px">备注</th>
                    <th style="width: 150px">
                      <div class="header-bulk-setting">
                        <span>发货方式</span>
                        <select v-model="headerShippingMethod" @change="applyHeaderShippingMethod">
                          <option value="">批量设置</option>
                          <option v-for="s in shippingMethodOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                        </select>
                      </div>
                    </th>
                    <th style="width: 180px">
                      <div class="header-bulk-setting">
                        <span>仓库</span>
                        <select v-model="headerWarehouseId" @change="applyHeaderWarehouse">
                          <option value="">批量设置</option>
                          <option v-for="w in warehouseList" :key="w.id" :value="w.id">{{ w.name }}</option>
                        </select>
                      </div>
                    </th>
                    <th style="width: 60px">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in orderForm.items" :key="index" :class="{ 'ai-pending-row': aiPendingItems.has(index) }">
                    <td>
                      {{ item.row_no }}
                      <span v-if="aiPendingItems.has(index)" class="ai-pending-badge-inline">待确认</span>
                    </td>
                    <!-- 未选择商品时：显示合并输入框 -->
                    <td v-if="!item.spec_id" colspan="10" class="merged-input-cell">
                      <div class="merged-search-wrapper">
                        <div class="search-select merged-search-select">
                          <input
                            type="text"
                            :value="specSearchKeywords[index] || ''"
                            @focus="showSpecDropdown = index; specSearchResults = []"
                            @input="handleSpecSearch(index, ($event.target as HTMLInputElement).value)"
                            placeholder="输入规格编号搜索商品..."
                          />
                          <div class="search-dropdown merged-search-dropdown" v-if="showSpecDropdown === index">
                            <div
                              v-for="spec in specSearchResults"
                              :key="spec.id"
                              class="search-option merged-search-item"
                              :class="{ 'inactive': !spec.is_active }"
                              @click="selectSpecFromSearchEdit(index, spec)"
                            >
                              <span class="spec-code">{{ spec.spec_code }}</span>
                              <span class="spec-packaging" v-if="spec.packaging">{{ spec.packaging }}</span>
                              <span class="brand-name" v-if="spec.brand_name">[{{ spec.brand_name }}]</span>
                              <span class="product-name-small">{{ spec.product_name }}</span>
                              <span class="spec-price">¥{{ spec.price.toFixed(2) }}</span>
                              <span class="spec-status" v-if="!spec.is_active">停用</span>
                            </div>
                            <div v-if="specSearchResults.length === 0" class="search-option disabled">
                              输入规格编号搜索
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                    <!-- 已选择商品时：显示分列 -->
                    <template v-else>
                      <td class="clear-btn-cell">
                        <button class="btn-clear-row" @click="clearSpecSelection(index)" title="清除整行">×</button>
                      </td>
                      <td>
                        <span v-if="item.product_name">{{ item.product_name }}</span>
                        <span v-else class="text-muted">-</span>
                      </td>
                      <td>
                        <span v-if="item.brand_name">{{ item.brand_name }}</span>
                        <span v-else class="text-muted">-</span>
                      </td>
                      <td>
                        <span class="spec-selected-code">{{ item.spec_code }}</span>
                      </td>
                      <td>
                        <span class="packaging-text">{{ (item.packaging && item.sales_spec) ? item.packaging + ' - ' + item.sales_spec : (item.packaging || item.sales_spec || '-') }}</span>
                      </td>
                      <td>
                        <input type="number" v-model="item.qty" min="1" @input="updateItemAmount(index)" />
                      </td>
                      <td>
                        <input type="number" v-model="item.price" min="0" step="0.01" @input="updateItemAmount(index)" />
                      </td>
                      <td>
                        <input type="number" v-model="item.discount" min="0" max="1" step="0.01" @input="updateItemAmount(index)" />
                      </td>
                      <td>
                        <input type="number" v-model="item.discounted_price" min="0" step="0.01" @input="updateItemDiscountByPrice(index)" />
                      </td>
                      <td>{{ formatAmount(item.amt) }}</td>
                    </template>
                    <td>
                      <input type="text" v-model="item.item_remark" placeholder="备注" class="remark-input" />
                    </td>
                    <td>
                      <select v-model="item.shipping_method" @change="if(item.shipping_method === 'direct') { item.warehouse_id = ''; item.warehouse_name = '' }">
                        <option v-for="s in shippingMethodOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                      </select>
                    </td>
                    <td v-if="item.shipping_method !== 'direct'">
                      <div class="search-select">
                        <input
                          type="text"
                          :value="item.warehouse_name || ''"
                          @click="if(item.warehouse_id) { item.warehouse_id = ''; item.warehouse_name = '' }"
                          @focus="showEditWarehouseDropdown = index; loadSpecStock(item.spec_id)"
                          readonly
                        />
                        <div class="search-dropdown" v-if="showEditWarehouseDropdown === index && getSpecStockList(item.spec_id).length > 0">
                          <div
                            v-for="s in getSpecStockList(item.spec_id)"
                            :key="s.warehouse_id"
                            class="search-option warehouse-option"
                            @click="selectWarehouseFromStockEdit(index, s)"
                          >
                            <span class="warehouse-name">{{ s.warehouse_name }}</span>
                            <span class="warehouse-stock">库存: {{ s.quantity }}</span>
                          </div>
                        </div>
                        <div class="search-dropdown" v-if="showEditWarehouseDropdown === index && getSpecStockList(item.spec_id).length === 0">
                          <div class="search-option disabled">暂无库存信息</div>
                        </div>
                      </div>
                    </td>
                    <td v-else></td>
                    <td>
                      <button class="btn-link danger" @click="removeOrderItem(index)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <button class="add-item-btn" @click="addOrderItem">+ 添加商品</button>
            </div>
          </div>

          <div class="form-section">
            <div class="section-title">费用汇总</div>
            <div class="amount-summary">
              <div class="summary-row">
                <span>产品总数量：</span>
                <span>{{ totalQty }} 件</span>
              </div>
              <div class="summary-row">
                <span>商品总金额：</span>
                <span>{{ formatAmount(totalAmount) }}</span>
              </div>
              <div class="summary-row freight-row">
                <span>运费：</span>
                <span v-if="!isEditingFreight" @click="startEditFreight" class="freight-value">{{ formatAmount(freightAmt) }}</span>
                <input v-else type="number" v-model="freightAmt" min="0" step="0.01"
                  @blur="isEditingFreight = false"
                  @keyup.enter="isEditingFreight = false"
                  ref="freightInputRef" class="freight-input" />
              </div>
              <div v-if="isAddOrder" class="freight-hint">加单默认不计算运费</div>
              <div class="summary-row">
                <span>总折扣金额：</span>
                <span>-{{ formatAmount(totalDiscountAmount) }}</span>
              </div>
              <div class="summary-row total">
                <span>最终金额：</span>
                <span>{{ formatAmount(finalAmount) }}</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>备注</label>
            <textarea v-model="orderForm.remark" placeholder="请输入备注" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showOrderModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveOrder" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
          <button class="btn-success" @click="handleSaveAndSubmit" :disabled="formLoading">
            {{ formLoading ? '提交中...' : '保存并提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Order Detail Modal -->
    <div class="modal-overlay" v-if="showDetailModal">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>订单详情 - {{ selectedOrder?.order_no }}</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedOrder">
          <div class="detail-loading" v-if="detailLoading">加载中...</div>
          <template v-else>
            <div class="detail-section">
              <div class="section-title">基本信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>订单编号</label>
                  <span>{{ selectedOrder.order_no }}</span>
                </div>
                <div class="detail-item">
                  <label>订单日期</label>
                  <span>{{ formatDate(selectedOrder.order_date) }}</span>
                </div>
                <div class="detail-item">
                  <label>客户名称</label>
                  <span>{{ selectedOrder.customer_name }}</span>
                </div>
                <div class="detail-item">
                  <label>销售人员</label>
                  <span>{{ selectedOrder.sale_user_name || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>结算方式</label>
                  <span>{{ selectedOrder.settle_type }}</span>
                </div>
                <div class="detail-item">
                  <label>期望交货日期</label>
                  <span>{{ formatDate(selectedOrder.expect_deliver_date) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-title">状态信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>订单状态</label>
                  <span class="status-tag" :class="getOrderStatusInfo(selectedOrder.order_status).class">
                    {{ getOrderStatusInfo(selectedOrder.order_status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>发货状态</label>
                  <span class="status-tag" :class="getDeliveryStatusInfo(selectedOrder.delivery_status).class">
                    {{ getDeliveryStatusInfo(selectedOrder.delivery_status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>下推状态</label>
                  <span class="status-tag" :class="getPushStatusInfo(selectedOrder.push_status).class">
                    {{ getPushStatusInfo(selectedOrder.push_status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>开票状态</label>
                  <span class="status-tag" :class="getInvoiceStatusInfo(selectedOrder.invoice_status).class">
                    {{ getInvoiceStatusInfo(selectedOrder.invoice_status).label }}
                  </span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-title">收货信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>收货人</label>
                  <span>{{ selectedOrder.deliver_info?.person_name || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>联系电话</label>
                  <span>{{ selectedOrder.deliver_info?.person_tel || '-' }}</span>
                </div>
                <div class="detail-item full-width">
                  <label>收货地址</label>
                  <span>{{ selectedOrder.deliver_info?.province }} {{ selectedOrder.deliver_info?.city }} {{ selectedOrder.deliver_info?.addr }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-title">开票信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>发票抬头</label>
                  <span>{{ selectedOrder.invoice_info?.invoice_title || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>纳税人识别号</label>
                  <span>{{ selectedOrder.invoice_info?.tax_number || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>开户行</label>
                  <span>{{ selectedOrder.invoice_info?.bank_name || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>银行账号</label>
                  <span>{{ selectedOrder.invoice_info?.bank_account || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-title">商品明细</div>
              <table class="detail-table">
                <thead>
                  <tr>
                    <th>行号</th>
                    <th>商品名称</th>
                    <th>规格编码</th>
                    <th>包装和包装单位</th>
                    <th style="text-align: right">数量</th>
                    <th style="text-align: right">单价</th>
                    <th style="text-align: right">折扣</th>
                    <th style="text-align: right">折后价</th>
                    <th style="text-align: right">金额</th>
                    <th>仓库</th>
                    <th>发货方式</th>
                    <th>退货信息</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in selectedOrder.items" :key="index">
                    <td>{{ item.row_no }}</td>
                    <td><span v-if="item.brand_name">[{{ item.brand_name }}] </span>{{ item.product_name }}</td>
                    <td>{{ item.spec_code }}</td>
                    <td>{{ (item.packaging && item.sales_spec) ? item.packaging + ' - ' + item.sales_spec : (item.packaging || item.sales_spec || '-') }}</td>
                    <td style="text-align: right">{{ item.qty }}</td>
                    <td style="text-align: right">{{ formatAmount(item.price) }}</td>
                    <td style="text-align: right">{{ item.discount }}</td>
                    <td style="text-align: right">{{ formatAmount(item.discounted_price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.amt) }}</td>
                    <td>{{ item.warehouse_name }}</td>
                    <td>{{ item.shipping_method }}</td>
                    <td>{{ (item as any).return_info || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="detail-section">
              <div class="section-title">费用信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>商品总金额</label>
                  <span>{{ formatAmount(selectedOrder.total_amt) }}</span>
                </div>
                <div class="detail-item">
                  <label>税额</label>
                  <span>{{ formatAmount(selectedOrder.tax_amt) }}</span>
                </div>
                <div class="detail-item">
                  <label>含税总金额</label>
                  <span class="amount-highlight">{{ formatAmount(selectedOrder.total_tax_amt) }}</span>
                </div>
                <div class="detail-item">
                  <label>总折扣金额</label>
                  <span>{{ formatAmount(selectedOrder.total_discount_amt) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="section-title">状态信息</div>
              <div class="status-info-grid">
                <div class="status-info-item">
                  <label>订单状态：</label>
                  <span class="status-tag" :class="getOrderStatusInfo(selectedOrder.order_status).class">{{ getOrderStatusInfo(selectedOrder.order_status).label }}</span>
                </div>
                <div class="status-info-item">
                  <label>发货状态：</label>
                  <span class="status-tag" :class="getDeliveryStatusInfo(selectedOrder.delivery_status).class">{{ getDeliveryStatusInfo(selectedOrder.delivery_status).label }}</span>
                </div>
                <div class="status-info-item">
                  <label>下推状态：</label>
                  <span class="status-tag" :class="getPushStatusInfo(selectedOrder.push_status).class">{{ getPushStatusInfo(selectedOrder.push_status).label }}</span>
                </div>
                <div class="status-info-item">
                  <label>开票状态：</label>
                  <span class="status-tag" :class="getInvoiceStatusInfo(selectedOrder.invoice_status).class">{{ getInvoiceStatusInfo(selectedOrder.invoice_status).label }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedOrderFlows && selectedOrderFlows.length > 0">
              <div class="section-title">流转记录</div>
              <div class="flow-timeline">
                <div class="flow-item" v-for="(flow, index) in selectedOrderFlows" :key="index">
                  <div class="flow-dot"></div>
                  <div class="flow-content">
                    <div class="flow-time">{{ flow.operate_time }}</div>
                    <div class="flow-detail">
                      <span class="flow-field">{{ statusFieldLabel(flow.field) }}</span>
                      <span v-if="flow.old_value" class="flow-old">{{ flow.old_value }}</span>
                      <span v-if="flow.old_value" class="flow-arrow">→</span>
                      <span class="flow-new">{{ flow.new_value }}</span>
                    </div>
                    <div class="flow-operator">操作人: {{ flow.operator }}</div>
                    <div class="flow-remark" v-if="flow.remark">{{ flow.remark }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedOrder.remark">
              <div class="section-title">备注</div>
              <p class="remarks-text">{{ selectedOrder.remark }}</p>
            </div>
          </template>
        </div>
        <div class="modal-footer" v-if="selectedOrder">
          <button
            class="btn-primary"
            v-if="selectedOrder.order_status === 'draft'"
            @click="openEditOrder(selectedOrder); showDetailModal = false"
          >
            编辑
          </button>
          <button
            class="btn-success"
            v-if="selectedOrder.order_status === 'draft'"
            @click="confirmAudit(selectedOrder.order_no)"
          >
            审核通过
          </button>
          <button
            class="btn-warning"
            v-if="(selectedOrder.order_status === 'audited' || selectedOrder.order_status === 'partially_pushed_to_purchase') && (selectedOrder.push_status === 'none' || selectedOrder.push_status === 'partial')"
            @click="confirmClose(selectedOrder.order_no)"
          >
            关闭订单
          </button>
          <button
            class="btn-primary"
            v-if="(selectedOrder.order_status === 'audited' || selectedOrder.order_status === 'partially_pushed_to_purchase') && (selectedOrder.push_status === 'none' || selectedOrder.push_status === 'partial')"
            @click="confirmPushPurchase(selectedOrder.order_no)"
          >
            下推采购
          </button>
          <button
            class="btn-danger"
            v-if="selectedOrder.order_status === 'draft' || selectedOrder.order_status === 'audited' || selectedOrder.order_status === 'partially_pushed_to_purchase'"
            @click="confirmCancel(selectedOrder.order_no)"
          >
            取消订单
          </button>
          <button class="btn-secondary" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- Quick Add Shipping Address Modal -->
    <div class="modal-overlay" v-if="showQuickAddShippingModal">
      <div class="modal" style="max-width: 600px;">
        <div class="modal-header">
          <div class="modal-header-left">
            <h3>新增收货地址</h3>
            <button class="ai-btn" @click="toggleShippingAiPanel" :class="{ active: showShippingAiPanel }">
              AI
            </button>
          </div>
          <button class="modal-close" @click="showQuickAddShippingModal = false">&times;</button>
        </div>

        <!-- AI 解析面板 -->
        <div class="ai-panel shipping-ai-panel" v-if="showShippingAiPanel">
          <div class="ai-panel-body" v-if="!shippingAiParsing">
            <div class="ai-section">
              <label class="ai-label">文本描述</label>
              <textarea
                v-model="shippingAiInputText"
                class="ai-textarea"
                placeholder="粘贴收货地址信息，如：张三 13800138000 北京市海淀区中关村大街1号..."
                rows="3"
                @paste="handleShippingAiPaste"
              ></textarea>
            </div>
            <div class="ai-section">
              <label class="ai-label">图片（最多3张）</label>
              <div class="ai-image-upload-area">
                <div class="ai-image-list">
                  <div v-for="(preview, index) in shippingAiImagePreviews" :key="index" class="ai-image-item">
                    <img :src="preview" alt="预览" class="ai-image-preview" />
                    <button class="ai-image-remove" @click="removeShippingAiImage(index)" title="删除">&times;</button>
                  </div>
                  <label v-if="shippingAiImageFiles.length < 3" class="ai-image-add">
                    <input type="file" accept="image/*" multiple class="ai-file-input" @change="handleShippingAiImageSelect" />
                    <span class="ai-image-add-icon">+</span>
                    <span class="ai-image-add-text">上传图片</span>
                  </label>
                </div>
                <p class="ai-image-hint">支持地址截图、名片等，最多3张，单张不超过5MB</p>
              </div>
            </div>
            <div class="ai-actions">
              <button class="btn-primary" @click="handleShippingAiSubmit" :disabled="!shippingAiInputText?.trim() && shippingAiImageFiles.length === 0">
                AI 解析
              </button>
              <button class="btn-secondary" @click="showShippingAiPanel = false">取消</button>
            </div>
          </div>
          <div class="ai-thinking" v-else>
            <div class="ai-thinking-animation">
              <div class="ai-thinking-dot"></div>
              <div class="ai-thinking-dot"></div>
              <div class="ai-thinking-dot"></div>
            </div>
            <p class="ai-thinking-hint">正在解析...</p>
          </div>
        </div>

        <div class="modal-body" v-if="!showShippingAiPanel || shippingAiParsing">
          <div class="form-group">
            <label>收货人 *</label>
            <input type="text" v-model="quickAddShippingForm.recipient_name" placeholder="请输入收货人姓名" />
          </div>
          <div class="form-group">
            <label>联系电话 *</label>
            <input type="text" v-model="quickAddShippingForm.recipient_phone" placeholder="请输入联系电话" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>省份</label>
              <select v-model="quickAddSelectedProvince">
                <option value="">请选择省份</option>
                <option v-for="p in provinceList" :key="p.code" :value="p.name">{{ p.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>城市</label>
              <select v-model="quickAddSelectedCity" :disabled="!quickAddSelectedProvince">
                <option value="">请选择城市</option>
                <option v-for="c in quickAddCityList" :key="c.code" :value="c.name">{{ c.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>详细地址 *</label>
            <input type="text" v-model="quickAddShippingForm.address" placeholder="请输入详细地址" />
          </div>
          <div class="form-group">
            <label><input type="checkbox" v-model="quickAddShippingForm.is_default" /> 设为默认</label>
          </div>
        </div>
        <div class="modal-footer" v-if="!showShippingAiPanel || shippingAiParsing">
          <button class="btn-secondary" @click="showQuickAddShippingModal = false">取消</button>
          <button class="btn-primary" @click="saveQuickAddShipping" :disabled="quickAddLoading">{{ quickAddLoading ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- Quick Add Invoice Info Modal -->
    <div class="modal-overlay" v-if="showQuickAddInvoiceModal">
      <div class="modal" style="max-width: 500px;">
        <div class="modal-header">
          <h3>新增开票信息</h3>
          <button class="modal-close" @click="showQuickAddInvoiceModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>发票抬头 *</label>
            <input type="text" v-model="quickAddInvoiceForm.invoice_title" placeholder="请输入公司全称" />
          </div>
          <div class="form-group">
            <label>开票类型 *</label>
            <select v-model="quickAddInvoiceForm.invoice_type">
              <option value="" disabled>请选择开票类型</option>
              <option v-for="opt in INVOICE_TYPE_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>纳税人识别号 *</label>
            <input type="text" v-model="quickAddInvoiceForm.tax_number" placeholder="请输入纳税人识别号" />
          </div>
          <div class="form-group">
            <label>开户行</label>
            <input type="text" v-model="quickAddInvoiceForm.bank_name" placeholder="请输入开户行" />
          </div>
          <div class="form-group">
            <label>银行账号</label>
            <input type="text" v-model="quickAddInvoiceForm.bank_account" placeholder="请输入银行账号" />
          </div>
          <div class="form-group">
            <label><input type="checkbox" v-model="quickAddInvoiceForm.is_default" /> 设为默认</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showQuickAddInvoiceModal = false">取消</button>
          <button class="btn-primary" @click="saveQuickAddInvoice" :disabled="quickAddLoading">{{ quickAddLoading ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div class="modal-overlay" v-if="showDeleteConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该订单吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Audit Confirm Modal -->
    <div class="modal-overlay" v-if="showAuditConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认审核</h3>
        </div>
        <div class="modal-body">
          <p>确定要审核通过该订单吗？审核通过后订单将进入执行阶段。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAuditConfirm = false">取消</button>
          <button class="btn-success" @click="handleAuditOrder" :disabled="actionLoading">
            {{ actionLoading ? '审核中...' : '确认审核' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Close Confirm Modal -->
    <div class="modal-overlay" v-if="showCloseConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认关闭</h3>
        </div>
        <div class="modal-body">
          <p>确定要关闭该订单吗？关闭后订单将不可再修改。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCloseConfirm = false">取消</button>
          <button class="btn-warning" @click="handleCloseOrder" :disabled="actionLoading">
            {{ actionLoading ? '关闭中...' : '确认关闭' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Cancel Confirm Modal -->
    <div class="modal-overlay" v-if="showCancelConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认取消</h3>
        </div>
        <div class="modal-body">
          <p>确定要取消该订单吗？取消后订单将不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCancelConfirm = false">取消</button>
          <button class="btn-danger" @click="handleCancelOrder" :disabled="actionLoading">
            {{ actionLoading ? '取消中...' : '确认取消' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reject Confirm Modal -->
    <div class="modal-overlay" v-if="showRejectConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认驳回</h3>
        </div>
        <div class="modal-body">
          <p>确定要驳回该订单吗？驳回后订单将返回草稿状态。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showRejectConfirm = false">取消</button>
          <button class="btn-warning" @click="handleRejectOrder" :disabled="actionLoading">
            {{ actionLoading ? '驳回中...' : '确认驳回' }}
          </button>
        </div>
      </div>
    </div>

    <!-- All Direct Shipping Confirm Modal -->
    <div class="modal-overlay" v-if="showAllDirectConfirm">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>直运订单确认</h3>
        </div>
        <div class="modal-body">
          <p>所有商品明细的发货方式均为"直运"，确认提交订单？</p>
          <p class="confirm-hint">直运订单将直接发货，无需经过仓库出库流程。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAllDirectConfirm = false">取消</button>
          <button class="btn-success" @click="confirmAllDirectSubmit" :disabled="actionLoading">
            {{ actionLoading ? '提交中...' : '确认提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Push Purchase Item Select Modal -->
    <PushPurchaseItemSelectModal
      :visible="showPushItemSelect"
      :items="pushableItems"
      @close="handleClosePushItemSelect"
      @submit="handlePushPurchase"
    />
  </div>
</template>

<style scoped>
.sales-order-workspace {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--color-interactive-hover);
}

.filter-section {
  background-color: var(--color-canvas);
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

.filter-item.search-filter {
  flex: 1;
  min-width: 200px;
}

.filter-input {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.filter-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.filter-select {
  padding: 8px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
  cursor: pointer;
  min-width: 120px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.filter-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background-color: var(--color-interactive-hover);
}

.filter-btn.reset-btn {
  background-color: transparent;
  color: var(--color-muted);
  border: 1px solid var(--color-hairline);
}

.filter-btn.reset-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-ink);
}

.table-section {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

/* 顶部滚动条区域 */
.top-scrollbar-area {
  margin-bottom: 0;
}

.top-scrollbar-area :deep(.vxe-table) {
  border-bottom: none;
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper) {
  overflow-y: hidden !important;
  height: 20px !important;
}

.top-scrollbar-area :deep(.vxe-table--body) {
  display: none;
}

.top-scrollbar-area :deep(.vxe-table--main-wrapper) {
  height: 20px !important;
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper::-webkit-scrollbar) {
  height: 8px;
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper::-webkit-scrollbar-track) {
  background: var(--color-neutral-bg);
  border-radius: 4px;
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper::-webkit-scrollbar-thumb) {
  background: var(--color-muted);
  border-radius: 4px;
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: var(--color-muted);
}

.top-scrollbar-area :deep(.vxe-table--body-wrapper::-webkit-scrollbar-corner) {
  background: var(--color-neutral-bg);
}

.order-link {
  color: var(--color-interactive);
  cursor: pointer;
  text-decoration: none;
}

.order-link:hover {
  text-decoration: underline;
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.draft { background-color: var(--color-neutral-bg); color: var(--color-muted); }
.status-tag.pending { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.audited { background-color: var(--color-info-bg); color: var(--color-interactive); }
.status-tag.pushed { background-color: var(--color-accent-soft); color: #c4391a; }
.status-tag.partial-pushed { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.closed { background-color: var(--color-success-bg); color: var(--color-success); }
.status-tag.cancelled { background-color: var(--color-danger-bg); color: var(--color-danger); }

.status-tag.none { background-color: var(--color-neutral-bg); color: var(--color-muted); }
.status-tag.partial { background-color: var(--color-warning-bg); color: var(--color-warning); }
.status-tag.full { background-color: var(--color-success-bg); color: var(--color-success); }
.status-tag.reconciled { background-color: var(--color-accent-soft); color: #c4391a; }

.profit-positive { color: var(--color-success); }
.profit-negative { color: var(--color-danger); }

.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 4px;
  justify-content: center;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-link:hover {
  background-color: var(--color-info-bg);
}

.btn-link.danger {
  color: var(--color-danger);
}

.btn-link.danger:hover {
  background-color: var(--color-danger-bg);
}

.btn-link.success {
  color: var(--color-success);
}

.btn-link.success:hover {
  background-color: var(--color-success-bg);
}

.btn-link.warning {
  color: var(--color-warning);
}

.btn-link.warning:hover {
  background-color: var(--color-warning-bg);
}

.btn-link.primary {
  color: var(--color-interactive);
}

.btn-link.primary:hover {
  background-color: var(--color-info-bg);
}

/* Modal styles */
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
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.order-modal {
  max-width: 1750px;
}

.detail-modal {
  max-width: 1000px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  background-color: var(--color-canvas);
  z-index: 1;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  color: var(--color-muted);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background-color: rgba(0, 0, 0, 0.08);
  color: var(--color-ink);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-hairline);
}

.form-section {
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-md);
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 16px 0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.form-group textarea {
  resize: vertical;
}

.search-select {
  position: relative;
}

.search-select input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  background-color: var(--color-canvas);
  color: var(--color-ink);
  font-size: 14px;
  cursor: pointer;
}

.search-select input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  margin-top: 4px;
}

.search-option {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-ink);
  transition: background-color var(--transition-fast);
}

.search-option:hover {
  background-color: var(--color-neutral-bg);
}

.search-option.disabled {
  color: var(--color-muted);
  cursor: default;
}

.search-option.disabled:hover {
  background-color: transparent;
}

.search-dropdown-filter {
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  background-color: var(--color-canvas);
}

.search-dropdown-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  background-color: var(--color-neutral-bg);
  color: var(--color-ink);
  font-size: 13px;
}

.search-dropdown-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.date-input {
  color-scheme: light;
}

[data-theme="dark"] .date-input {
  color-scheme: dark;
}

.items-table {
  background-color: var(--color-canvas);
  border-radius: var(--radius-sm);
  overflow: visible;
}

.items-table table {
  width: 100%;
  border-collapse: collapse;
}

.items-table th,
.items-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.items-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.items-table td {
  font-size: 13px;
  color: var(--color-ink);
}

.items-table input,
.items-table select {
  width: 100%;
  padding: 8px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.items-table input[type="number"] {
  text-align: right;
}

.header-bulk-setting {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.header-bulk-setting span {
  font-weight: 600;
  font-size: 13px;
}

.header-bulk-setting select {
  font-size: 12px;
  padding: 2px 4px;
  max-width: 100%;
}

.add-item-btn {
  width: 100%;
  padding: 12px;
  background-color: transparent;
  border: 1px dashed var(--color-hairline);
  border-radius: 0;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-item-btn:hover {
  background-color: var(--color-info-bg);
  border-color: var(--color-interactive);
}

.amount-summary {
  background-color: var(--color-canvas);
  border-radius: var(--radius-sm);
  padding: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 13px;
  color: var(--color-muted);
}

.summary-row.total {
  border-top: 1px solid var(--color-hairline);
  margin-top: 8px;
  padding-top: 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

/* 运费行样式 */
.freight-row {
  cursor: pointer;
}

.freight-row:hover .freight-value {
  color: var(--color-interactive);
  text-decoration: underline;
}

.freight-value {
  cursor: pointer;
  transition: color 0.2s;
}

.freight-hint {
  font-size: 11px;
  color: var(--text-tertiary, #999);
  text-align: right;
  padding-right: 0;
}

.freight-input {
  width: 120px;
  padding: 4px 8px;
  border: 1px solid var(--color-interactive);
  border-radius: 4px;
  background-color: var(--color-neutral-bg);
  color: var(--color-ink);
  font-size: 13px;
  text-align: right;
}

.freight-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

/* Detail styles */
.detail-loading {
  text-align: center;
  padding: 40px;
  color: var(--color-muted);
}

.detail-section {
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-md);
  padding: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full-width {
  grid-column: span 3;
}

.detail-item label {
  font-size: 12px;
  color: var(--color-muted);
}

.detail-item span {
  font-size: 14px;
  color: var(--color-ink);
}

.amount-highlight {
  color: var(--color-interactive) !important;
  font-weight: 600;
  font-size: 16px !important;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-canvas);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.detail-table th,
.detail-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.detail-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.detail-table td {
  font-size: 13px;
  color: var(--color-ink);
}

.remarks-text {
  font-size: 14px;
  color: var(--color-ink);
  margin: 0;
  line-height: 1.6;
}

/* 流转记录样式 */
.flow-timeline {
  padding-left: 20px;
}

.flow-item {
  position: relative;
  padding-bottom: 20px;
  padding-left: 24px;
  border-left: 2px solid var(--color-hairline);
}

.flow-item:last-child {
  border-left: 2px solid transparent;
  padding-bottom: 0;
}

.flow-dot {
  position: absolute;
  left: -7px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--color-interactive);
  border: 2px solid var(--color-canvas);
}

.flow-item:last-child .flow-dot {
  background-color: var(--color-success);
}

.flow-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.flow-time {
  font-size: 12px;
  color: var(--color-muted);
}

.flow-detail {
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-field {
  font-weight: 500;
  color: var(--color-ink);
}

.flow-old {
  color: var(--color-muted);
  text-decoration: line-through;
}

.flow-arrow {
  color: var(--color-muted);
}

.flow-new {
  color: var(--color-interactive);
  font-weight: 500;
}

.flow-operator {
  font-size: 12px;
  color: var(--color-muted);
}

.flow-remark {
  font-size: 12px;
  color: var(--color-muted);
  font-style: italic;
}

.status-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-group label {
  width: 80px;
  font-size: 13px;
  color: var(--color-muted);
}

.status-group select {
  padding: 8px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
  min-width: 120px;
}

/* Buttons */
.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-ink);
}

.btn-quick-add {
  width: 32px;
  min-width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-interactive);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 18px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-quick-add:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-quick-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-success);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-success:hover:not(:disabled) {
  filter: brightness(0.9);
}

.btn-success:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-warning {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-warning);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-warning:hover:not(:disabled) {
  filter: brightness(0.9);
}

.btn-warning:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-danger);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  filter: brightness(0.9);
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-modal {
  max-width: 400px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--color-ink);
  margin: 0;
}

/* Table loading */
.table-loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.table-loading-content {
  padding: 20px 40px;
  background-color: var(--color-canvas);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-hover);
  font-size: 14px;
  color: var(--color-ink);
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-item.full-width {
    grid-column: span 2;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}

/* Product tree dropdown */
.product-tree-dropdown {
  max-height: 300px;
}

.product-tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.product-tree-item:hover {
  background-color: var(--color-neutral-bg);
}

.expand-icon {
  font-size: 10px;
  transition: transform 0.2s;
  color: var(--color-muted);
  width: 14px;
  text-align: center;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.brand-name {
  font-size: 12px;
  color: var(--color-interactive);
  margin-right: 2px;
}

.product-name {
  font-size: 14px;
  color: var(--color-ink);
}

.product-code {
  font-size: 12px;
  color: var(--color-muted);
}

.spec-count {
  font-size: 11px;
  color: var(--color-interactive);
  margin-left: auto;
}

.spec-list {
  border-left: 2px solid var(--color-hairline);
  margin-left: 14px;
}

.spec-item {
  padding-left: 20px !important;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.spec-item.inactive {
  opacity: 0.5;
}

.spec-code {
  color: var(--color-ink);
  font-weight: 500;
}

.spec-info {
  color: var(--color-muted);
  font-size: 12px;
}

.spec-price {
  color: var(--color-interactive);
  font-size: 13px;
  margin-left: auto;
}

.spec-status {
  font-size: 11px;
  color: var(--color-danger);
  background-color: var(--color-danger-bg);
  padding: 1px 4px;
  border-radius: 2px;
}

.spec-search-header {
  font-size: 11px;
  color: var(--color-muted);
  text-align: center;
  border-top: 1px solid var(--color-hairline);
  margin-top: 4px;
}

.spec-search-item {
  padding-left: 12px !important;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.spec-search-item.inactive {
  opacity: 0.5;
}

.brand-tag {
  color: var(--color-interactive);
  margin-right: 4px;
}

.text-muted {
  color: var(--color-muted);
}

.spec-search-dropdown {
  max-height: 300px;
  overflow-y: auto;
}

.spec-selected-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
  background: var(--color-neutral-bg);
  border-radius: 4px;
  cursor: pointer;
}

.spec-selected-overlay:hover {
  background: var(--color-neutral-bg);
}

.spec-selected-code {
  font-weight: 500;
  color: var(--color-ink);
}

.spec-selected-clear {
  color: var(--color-muted);
  font-size: 16px;
  font-weight: bold;
}

.spec-selected-clear:hover {
  color: var(--color-danger);
}

.product-name-small {
  font-size: 12px;
  color: var(--color-muted);
}

/* Expand items panel */
.expand-items-panel {
  padding: 12px 16px;
  background-color: var(--color-canvas);
  overflow-x: hidden;
  overflow-y: hidden;
  margin-left: 50px;
}

.expand-items-panel .expand-items-table {
  min-width: max-content;
}

/* 展开行跟随表格主体滚动 */
:deep(.vxe-table--expanded) {
  position: relative !important;
}

:deep(.vxe-table--expanded .vxe-body--column) {
  position: relative !important;
}

/* 固定列遮盖展开内容 */
:deep(.vxe-table--fixed-left-wrapper) {
  z-index: 10 !important;
}

:deep(.vxe-table--fixed-right-wrapper) {
  z-index: 10 !important;
}

:deep(.vxe-body--column) {
  &.expand--cell,
  &.col--actived {
    background-color: var(--color-canvas) !important;
  }
}

:deep(.vxe-body--row.expand--row > td) {
  background-color: var(--color-canvas) !important;
}

:deep(.vxe-body--row.expand--row:hover > td) {
  background-color: var(--color-neutral-bg) !important;
}

:deep(.vxe-body--row) > td {
  background-color: var(--color-canvas) !important;
}

:deep(.vxe-body--row:hover) > td {
  background-color: var(--color-neutral-bg) !important;
}

.expand-items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
}

.expand-items-table th {
  padding: 8px 10px;
  background-color: var(--color-neutral-bg);
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 500;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.expand-items-table td {
  padding: 8px 10px;
  color: var(--color-ink);
  background-color: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
}

.expand-items-table tr:last-child td {
  border-bottom: none;
}

.expand-items-table td:nth-child(3) {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 合并输入框样式 */
.merged-input-cell {
  padding: 8px !important;
  background-color: var(--color-neutral-bg);
}

.merged-search-wrapper {
  width: 100%;
}

.merged-search-select {
  width: 100%;
}

.merged-search-select input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-hairline);
  border-radius: 6px;
  font-size: 14px;
  background: var(--color-canvas);
  color: var(--color-ink);
  box-sizing: border-box;
}

.merged-search-select input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.merged-search-select input::placeholder {
  color: var(--color-muted);
}

.merged-search-dropdown {
  min-width: 600px;
  max-width: 800px;
}

.merged-search-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
}

.merged-search-item .spec-code {
  font-weight: 500;
  min-width: 120px;
}

.merged-search-item .spec-packaging {
  color: var(--color-muted);
  font-size: 12px;
  min-width: 80px;
}

.merged-search-item .brand-name {
  color: var(--color-interactive);
  font-size: 12px;
  min-width: 60px;
}

.merged-search-item .product-name-small {
  flex: 1;
  color: var(--color-muted);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.merged-search-item .spec-price {
  color: var(--color-interactive);
  font-weight: 500;
  margin-left: auto;
}

.merged-search-item .spec-status {
  font-size: 11px;
  color: var(--color-danger);
  background-color: var(--color-danger-bg);
  padding: 1px 4px;
  border-radius: 2px;
}

.merged-search-item.inactive {
  opacity: 0.5;
}

/* 清除按钮列 */
.clear-btn-cell {
  padding: 8px !important;
  text-align: center;
}

.btn-clear-row {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background-color: transparent;
  color: var(--color-muted);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-clear-row:hover {
  background-color: var(--color-danger-bg);
  color: var(--color-danger);
}

/* 已选择的规格编码样式 */
.spec-selected-code {
  font-weight: 500;
  color: var(--color-ink);
}

/* 包装文本样式 */
.packaging-text {
  color: var(--color-muted);
  font-size: 13px;
}

/* ========== AI 智能解析面板样式 ========== */

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-btn {
  padding: 6px 12px;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-xs);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ai-btn:hover {
  opacity: 0.9;
}

.ai-btn.active {
  box-shadow: 0 0 0 2px var(--color-accent-soft);
}

.ai-panel {
  padding: 20px;
  background-color: var(--color-neutral-bg);
  border-bottom: 1px solid var(--color-hairline);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.ai-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ai-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.ai-panel-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ai-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
}

.ai-textarea {
  width: 100%;
  padding: 12px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.ai-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.ai-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-image-upload-area {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-image-item {
  position: relative;
  width: 80px;
  height: 80px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.ai-image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-image-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  min-width: 20px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  color: #fff;
  border: none;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.ai-image-remove:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

.ai-image-remove:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-image-add {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-xs);
  cursor: pointer;
  color: var(--color-muted);
  transition: all var(--transition-fast);
}

.ai-image-add:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.ai-file-input {
  display: none;
}

.ai-image-add-icon {
  font-size: 24px;
  line-height: 1;
}

.ai-image-add-text {
  font-size: 11px;
  margin-top: 2px;
}

.ai-image-hint {
  font-size: 12px;
  color: var(--color-muted);
  margin: 0;
}

.ai-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
}

/* AI Thinking 动画 */
.ai-thinking {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 16px;
}

.ai-thinking-animation {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ai-thinking-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--color-accent);
  animation: aiDotPulse 1.4s ease-in-out infinite;
}

.ai-thinking-dot:nth-child(1) {
  animation-delay: 0s;
}

.ai-thinking-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.ai-thinking-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes aiDotPulse {
  0%, 80%, 100% {
    transform: scale(0.4);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.ai-thinking-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.ai-thinking-label {
  color: var(--color-accent);
}

.ai-thinking-ellipsis {
  display: inline-flex;
  overflow: hidden;
}

.ai-ellipsis-dot {
  animation: aiEllipsis 1.4s infinite;
  opacity: 0;
}

.ai-ellipsis-dot:nth-child(1) {
  animation-delay: 0s;
}

.ai-ellipsis-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.ai-ellipsis-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes aiEllipsis {
  0% { opacity: 0; }
  40% { opacity: 1; }
  80%, 100% { opacity: 0; }
}

.ai-thinking-hint {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

/* AI 进度条样式 */
.ai-progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 300px;
  margin-top: 8px;
}

.ai-progress-bar {
  flex: 1;
  height: 6px;
  background-color: var(--color-border);
  border-radius: 3px;
  overflow: hidden;
}

.ai-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent), #6366f1);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.ai-progress-percent {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent);
  min-width: 35px;
  text-align: right;
}

.ai-thinking-step {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
  animation: aiStepFade 1.5s ease-in-out infinite;
}

@keyframes aiStepFade {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ========== AI 待确认样式 ========== */

.search-select.ai-pending {
  position: relative;
}

.ai-pending-input {
  border-color: var(--color-warning) !important;
  border-width: 2px;
}

.ai-pending-badge {
  display: inline-block;
  padding: 2px 8px;
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  border-radius: var(--radius-xs);
  margin-left: 8px;
  font-weight: 500;
}

.ai-pending-badge-inline {
  display: inline-block;
  padding: 1px 6px;
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  border-radius: var(--radius-xs);
  margin-left: 4px;
  font-weight: 500;
}

.ai-pending-row {
  background-color: var(--color-warning-bg) !important;
  border-left: 3px solid var(--color-warning);
}

.ai-pending-row:hover {
  background-color: var(--color-warning-bg) !important;
}

.ai-pending-row td {
  border-left-color: var(--color-warning);
}

/* 收货地址 AI 解析面板样式 */
.shipping-ai-panel {
  margin: -20px -20px 0 -20px;
  border-bottom: 1px solid var(--color-hairline);
}

.shipping-ai-panel .ai-thinking {
  padding: 30px 20px;
}

.shipping-ai-panel .ai-thinking-hint {
  font-size: 14px;
  color: var(--color-muted);
  margin: 0;
}

/* 商品备注输入框样式 */
.remark-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  font-size: 13px;
  background-color: var(--color-neutral-bg);
  color: var(--color-ink);
}

.remark-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.remark-input::placeholder {
  color: var(--color-muted);
}

/* 全直运确认提示样式 */
.confirm-hint {
  color: var(--color-muted);
  font-size: 13px;
  margin-top: 8px;
}
</style>