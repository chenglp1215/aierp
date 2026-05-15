<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch, onBeforeUnmount, nextTick } from 'vue'
import { salesOrderApi, customerApi, productApi, warehouseApi, customerDiscountApi, brandApi, type Customer } from '../../services/api'
import { useProvinceCity } from '../../hooks/useProvinceCity'
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
  spec_id: string
  spec_code?: string
  packaging?: string
  sales_spec?: string
  qty: number
  price: number
  discount: number
  discounted_price: number
  amt: number
  warehouse_id: string
  warehouse_name?: string
  shipping_method: string
  out_qty: number
  return_qty: number
  remain_out_qty: number
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
  order_status: string
  delivery_status: string
  receive_status: string
  invoice_status: string
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

interface Product {
  id: string
  name: string
  product_code?: string
  brand_id?: string
  brand_name?: string
  specs?: ProductSpec[]
}

interface ProductWithSpecs {
  product: Product
  specs: ProductSpec[]
  expanded: boolean
}

interface SpecSearchResult {
  id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price: number
  is_active: boolean
  product_id: string
  product_name: string
  product_code: string
  brand_name: string
}

interface ProductSpec {
  id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price: number
  is_active: boolean
}

interface Warehouse {
  id: string
  name: string
}

// Constants
const orderStatusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
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

const settleTypeOptions = [
  { value: '月结', label: '月结' },
  { value: '货到付款', label: '货到付款' },
  { value: '款到发货', label: '款到发货' }
]

const shippingMethodOptions = [
  { value: '直运', label: '直运' },
  { value: '物流', label: '物流' },
  { value: '自提', label: '自提' },
  { value: '送货', label: '送货' }
]

const orderStatusOptions = Object.entries(orderStatusMap).map(([value, { label }]) => ({ value, label }))
const deliveryStatusOptions = Object.entries(deliveryStatusMap).map(([value, { label }]) => ({ value, label }))
const receiveStatusOptions = Object.entries(receiveStatusMap).map(([value, { label }]) => ({ value, label }))
const invoiceStatusOptions = Object.entries(invoiceStatusMap).map(([value, { label }]) => ({ value, label }))

// State
const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')
const filterCustomerId = ref('')
const filterKeyword = ref('')

// Modals
const showOrderModal = ref(false)
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const showAuditConfirm = ref(false)
const showCloseConfirm = ref(false)
const showCancelConfirm = ref(false)
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
const productTree = ref<ProductWithSpecs[]>([])
const specSearchResults = ref<SpecSearchResult[]>([])
const warehouseList = ref<Warehouse[]>([])

// 仓库库存数据（按规格ID缓存）
const specStockMap = ref<Record<string, { warehouse_id: string; quantity: number }[]>>({})
// 表头批量设置
const headerShippingMethod = ref('')
const headerWarehouseId = ref('')
const customersLoading = ref(false)
const warehousesLoading = ref(false)

// Search states
const customerSearchKeyword = ref('')
const showCustomerDropdown = ref(false)
const showProductDropdown = ref<number | null>(null)
const productSearchKeywords = ref<Record<number, string>>({})

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
    showProductDropdown.value = null
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
    bank_account: ''
  },
  remark: '',
  items: [] as SalesOrderItem[]
})

// Computed
const hasActiveFilters = computed(() => !!(filterStatus.value || filterCustomerId.value || filterKeyword.value))

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

// 商品搜索（服务端模糊匹配规格编号）
let productSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleProductSearch = (index: number, keyword: string) => {
  // 保存搜索关键字
  productSearchKeywords.value[index] = keyword

  if (productSearchTimer) clearTimeout(productSearchTimer)
  if (!keyword || keyword.length < 1) {
    productTree.value = []
    specSearchResults.value = []
    return
  }
  productSearchTimer = setTimeout(async () => {
    try {
      // 只搜索规格
      const specsRes = await productApi.searchSpecs(keyword, 20)
      specSearchResults.value = specsRes?.items || []
      productTree.value = []
    } catch (e) {
      console.error('搜索商品失败:', e)
      productTree.value = []
      specSearchResults.value = []
    }
  }, 300)
}

// 从规格搜索结果中选择规格（直接匹配规格编号）
const selectSpecFromSearch = async (specResult: SpecSearchResult) => {
  const itemIndex = showProductDropdown.value ?? 0
  showProductDropdown.value = null
  specSearchResults.value = []
  productSearchKeywords.value[itemIndex] = ''

  // 获取商品详情以获取品牌信息用于折扣计算
  let discount = 1
  if (orderForm.value.customer_id && specResult.product_id) {
    try {
      const productRes = await productApi.getById(specResult.product_id)
      const productDetail = productRes.result
      if (productDetail?.brand_id) {
        const discountRes = await customerDiscountApi.list({
          customer_id: orderForm.value.customer_id,
          brand_id: productDetail.brand_id,
          is_active: true
        })
        const discountItem = discountRes.result?.items?.[0]
        if (discountItem) {
          discount = discountItem.discount_value
        }
      }
    } catch (e) {
      console.error('获取商品折扣失败:', e)
    }
  }

  const discountedPrice = +(specResult.price * discount).toFixed(2)

  orderForm.value.items[itemIndex] = {
    ...orderForm.value.items[itemIndex],
    product_id: specResult.product_id,
    product_name: specResult.product_name,
    product_code: specResult.product_code || '',
    brand_name: specResult.brand_name || '',
    spec_id: specResult.id,
    spec_code: specResult.spec_code,
    packaging: specResult.packaging || '',
    sales_spec: specResult.sales_spec || '',
    price: specResult.price,
    discount: discount,
    discounted_price: discountedPrice,
    amt: +(orderForm.value.items[itemIndex].qty * discountedPrice).toFixed(2)
  }
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

// 加载规格的库存数据
const loadSpecStock = async (specId: string) => {
  if (!specId || specStockMap.value[specId]) return
  try {
    const res = await productApi.getSpecStockDetail(specId)
    specStockMap.value[specId] = res?.items || []
  } catch (e) {
    console.error('加载库存失败:', e)
    specStockMap.value[specId] = []
  }
}

// 获取仓库中某规格的库存数量
const getStockQty = (specId: string, warehouseId: string): number | null => {
  const stocks = specStockMap.value[specId]
  if (!stocks) return null
  const stock = stocks.find((s: any) => s.warehouse_id === warehouseId)
  return stock ? stock.quantity : 0
}

// 批量设置发货方式
const applyHeaderShippingMethod = () => {
  if (!headerShippingMethod.value) return
  orderForm.value.items.forEach(item => {
    if (item.product_id) {
      item.shipping_method = headerShippingMethod.value
      if (headerShippingMethod.value === '直运') {
        item.warehouse_id = ''
        item.warehouse_name = ''
      }
    }
  })
}

// 批量设置仓库
const applyHeaderWarehouse = () => {
  if (!headerWarehouseId.value) return
  const warehouse = warehouseList.value.find((w: Warehouse) => w.id === headerWarehouseId.value)
  orderForm.value.items.forEach(item => {
    if (item.product_id && item.shipping_method !== '直运') {
      item.warehouse_id = headerWarehouseId.value
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

const resetFilters = () => {
  filterStatus.value = ''
  filterCustomerId.value = ''
  filterKeyword.value = ''
  page.value = 1
  loadOrders()
}

const resetOrderForm = () => {
  orderForm.value = {
    order_date: new Date().toISOString().split('T')[0],
    customer_id: '',
    customer_name: '',
    sale_user_id: '',
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
      bank_account: ''
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
}

const openCreateOrder = () => {
  resetOrderForm()
  showOrderModal.value = true
}

const openEditOrder = async (order: SalesOrder) => {
  editingOrder.value = order
  orderForm.value = {
    order_date: order.order_date,
    customer_id: order.customer_id,
    customer_name: order.customer_name || '',
    sale_user_id: order.sale_user_id || '',
    deliver_info: { ...order.deliver_info },
    expect_deliver_date: order.expect_deliver_date || '',
    settle_type: order.settle_type,
    invoice_info: { ...order.invoice_info },
    remark: order.remark || '',
    items: order.items.map(item => ({
      ...item,
      warehouse_name: item.warehouse_name || '',
      product_name: item.product_name || '',
      product_code: item.product_code || '',
      brand_name: item.brand_name || '',
      spec_code: item.spec_code || ''
    }))
  }
  customerSearchKeyword.value = order.customer_name || ''

  // 补充商品的品牌信息、包装和销售规格
  const productIds = [...new Set(order.items.map(item => item.product_id).filter(Boolean))]
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
    const res = await customerApi.getById(order.customer_id)
    const detail = res
    customerInvoiceInfos.value = detail?.invoice_infos || []
    customerShippingAddresses.value = detail?.shipping_addresses || []

    // 匹配当前订单的收货地址
    const matchedAddr = customerShippingAddresses.value.find(
      (a: any) => a.recipient_name === order.deliver_info?.person_name && a.recipient_phone === order.deliver_info?.person_tel
    )
    selectedShippingAddressId.value = matchedAddr?.id || ''

    // 匹配当前订单的开票信息
    const matchedInv = customerInvoiceInfos.value.find(
      (i: any) => i.invoice_title === order.invoice_info?.invoice_title && i.tax_number === order.invoice_info?.tax_number
    )
    selectedInvoiceInfoId.value = matchedInv?.id || ''
  } catch (e) {
    console.error('加载客户信息失败:', e)
    customerInvoiceInfos.value = []
    customerShippingAddresses.value = []
    selectedShippingAddressId.value = ''
    selectedInvoiceInfoId.value = ''
  }

  // 设置省份/城市
  selectedProvince.value = order.deliver_info?.province || ''
  if (order.deliver_info?.province) {
    cityList.value = getCities(order.deliver_info.province)
    selectedCity.value = order.deliver_info?.city || ''
  }
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
  orderForm.value.customer_name = customer.name
  customerSearchKeyword.value = customer.name
  showCustomerDropdown.value = false

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
          bank_account: defaultInvoice.bank_account
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
    person_name: addr.recipient_name,
    person_tel: addr.recipient_phone
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
      bank_account: inv.bank_account
    }
  }
}

const onWarehouseChange = (index: number, warehouseId: string) => {
  if (!warehouseId) {
    orderForm.value.items[index].warehouse_id = ''
    orderForm.value.items[index].warehouse_name = ''
    return
  }
  const warehouse = warehouseList.value.find((w: Warehouse) => w.id === warehouseId)
  if (warehouse) {
    orderForm.value.items[index].warehouse_id = warehouse.id
    orderForm.value.items[index].warehouse_name = warehouse.name
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
    const res = await customerApi.addShippingAddress(orderForm.value.customer_id, quickAddShippingForm.value)
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
    shipping_method: '直运',
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

const totalDiscountAmount = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + ((item.price || 0) - (item.discounted_price || 0)) * (item.qty || 0), 0)
})

const handleSaveOrder = async () => {
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
    if (item.shipping_method !== '直运' && !item.warehouse_id) {
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
      deliver_info: orderForm.value.deliver_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      invoice_info: orderForm.value.invoice_info,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        product_code: item.product_code || item.product_id,
        spec_code: item.spec_code || item.spec_id,
        packaging: item.packaging,
        sales_spec: item.sales_spec,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        warehouse_id: item.warehouse_id,
        shipping_method: item.shipping_method
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
      deliver_info: orderForm.value.deliver_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      invoice_info: orderForm.value.invoice_info,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        product_code: item.product_code || item.product_id,
        spec_code: item.spec_code || item.spec_id,
        packaging: item.packaging,
        sales_spec: item.sales_spec,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        warehouse_id: item.warehouse_id,
        shipping_method: item.shipping_method
      }))
    }

    if (editingOrder.value) {
      // 编辑模式：先保存再审核
      await salesOrderApi.update(editingOrder.value.order_no, submitData)
      await salesOrderApi.updateOrderStatus(editingOrder.value.order_no, 'audited')
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
    await salesOrderApi.updateOrderStatus(actionTargetOrderNo.value, 'audited')
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
    await salesOrderApi.updateOrderStatus(actionTargetOrderNo.value, 'closed')
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
    const orderRes = await salesOrderApi.getByOrderNo(orderNo)
    const fullOrder = orderRes.result
    const items = fullOrder.items || []

    // 补充 brand_name 和 brand_id
    const productIds: string[] = [...new Set(items.map((item: any) => item.product_id).filter(Boolean) as string[])]
    const brandMap: Record<string, string> = {}
    const brandIdMap: Record<string, string> = {}
    for (const pid of productIds) {
      try {
        const prodRes = await productApi.getById(pid)
        if (prodRes.result) {
          brandMap[pid] = prodRes.result.brand_name || ''
          brandIdMap[pid] = prodRes.result.brand_id || ''
        }
      } catch {}
    }

    const enrichedItems = items.map((item: any) => ({
      ...item,
      brand_name: item.brand_name || brandMap[item.product_id] || '',
      brand_id: item.brand_id || brandIdMap[item.product_id] || ''
    }))

    // 批量获取品牌的采购人信息
    const uniqueBrandIds = [...new Set(enrichedItems.map((item: any) => item.brand_id).filter(Boolean))] as string[]
    if (uniqueBrandIds.length > 0) {
      try {
        const purchaserRes = await brandApi.batchGetPurchasers(uniqueBrandIds)
        const purchaserMap: Record<string, { purchaser_id: string; purchaser_name: string }> = purchaserRes || {}
        enrichedItems.forEach((item: any) => {
          if (item.brand_id && purchaserMap[item.brand_id]) {
            item.purchaser_name = purchaserMap[item.brand_id].purchaser_name || ''
          }
        })
      } catch {}
    }

    pushableItems.value = enrichedItems
    showPushItemSelect.value = true
  } catch (error: any) {
    window.showToast(error.message || '加载商品数据失败', 'error')
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
    const purchaseCount = result.result?.purchase_orders?.length || 0
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
    await salesOrderApi.updateOrderStatus(actionTargetOrderNo.value, 'cancelled')
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

const refreshFlows = async (orderNo: string) => {
  try {
    const flowRes = await salesOrderApi.getStatusFlows(orderNo)
    selectedOrderFlows.value = flowRes.result || []
  } catch (e) {
    console.error('刷新流转记录失败:', e)
  }
}

const handleUpdateOrderStatus = async (orderNo: string, status: string) => {
  try {
    await salesOrderApi.updateOrderStatus(orderNo, status)
    window.showToast('订单状态更新成功', 'success')
    loadOrders()
    if (selectedOrder.value?.order_no === orderNo) {
      selectedOrder.value = { ...selectedOrder.value, order_status: status }
    }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}

const handleUpdateDeliveryStatus = async (orderNo: string, delivery_status: string) => {
  try {
    await salesOrderApi.updateDeliveryStatus(orderNo, delivery_status)
    window.showToast('发货状态更新成功', 'success')
    loadOrders()
    if (selectedOrder.value?.order_no === orderNo) {
      selectedOrder.value = { ...selectedOrder.value, delivery_status }
    }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}

const handleUpdateReceiveStatus = async (orderNo: string, receive_status: string) => {
  try {
    await salesOrderApi.updateReceiveStatus(orderNo, receive_status)
    window.showToast('收货状态更新成功', 'success')
    loadOrders()
    if (selectedOrder.value?.order_no === orderNo) {
      selectedOrder.value = { ...selectedOrder.value, receive_status }
    }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}

const handleUpdateInvoiceStatus = async (orderNo: string, invoice_status: string) => {
  try {
    await salesOrderApi.updateInvoiceStatus(orderNo, invoice_status)
    window.showToast('开票状态更新成功', 'success')
    loadOrders()
    if (selectedOrder.value?.order_no === orderNo) {
      selectedOrder.value = { ...selectedOrder.value, invoice_status }
    }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
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
const getReceiveStatusInfo = (status: string) => receiveStatusMap[status] || { label: status, class: '' }
const getInvoiceStatusInfo = (status: string) => invoiceStatusMap[status] || { label: status, class: '' }

const statusFieldLabel = (field: string) => {
  const map: Record<string, string> = {
    order_status: '订单状态',
    delivery_status: '发货状态',
    receive_status: '收货状态',
    invoice_status: '开票状态'
  }
  return map[field] || field
}

// Lifecycle
onMounted(async () => {
  loadOrders()
  loadCustomers()
  loadWarehouses()
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
        <div class="filter-item">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索订单号、客户名称..."
            v-model="filterKeyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterCustomerId" @change="handleSearch">
            <option value="">全部客户</option>
            <option v-for="c in customerList" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in orderStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
    </div>

    <div class="table-section" style="position: relative;">
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
        <vxe-column field="order_no" title="订单编号" width="160" fixed="left" class-name="col--center">
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
                    <th style="width: 50px">行号</th>
                    <th>商品名称</th>
                    <th style="width: 100px">规格编码</th>
                    <th style="width: 120px">包装和包装单位</th>
                    <th style="width: 80px; text-align: right">数量</th>
                    <th style="width: 100px; text-align: right">单价</th>
                    <th style="width: 100px; text-align: right">折后价</th>
                    <th style="width: 100px; text-align: right">金额</th>
                    <th style="width: 120px">仓库</th>
                    <th style="width: 80px">发货方式</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in row.items" :key="idx">
                    <td class="col--center">{{ item.row_no }}</td>
                    <td><span v-if="item.brand_name">[{{ item.brand_name }}] </span>{{ item.product_name || '-' }}</td>
                    <td>{{ item.spec_code || '-' }}</td>
                    <td>{{ (item.packaging && item.sales_spec) ? item.packaging + ' - ' + item.sales_spec : (item.packaging || item.sales_spec || '-') }}</td>
                    <td style="text-align: right">{{ item.qty }}</td>
                    <td style="text-align: right">{{ formatAmount(item.price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.discounted_price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.amt) }}</td>
                    <td>{{ item.warehouse_name || '-' }}</td>
                    <td>{{ item.shipping_method }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </vxe-column>
        <vxe-column field="customer_name" title="客户名称" min-width="150" class-name="col--center" />
        <vxe-column field="order_date" title="订单日期" width="120" class-name="col--center">
          <template #default="{ row }">
            {{ formatDate(row.order_date) }}
          </template>
        </vxe-column>
        <vxe-column field="total_amt" title="商品总金额" width="120" class-name="col--right">
          <template #default="{ row }">
            {{ formatAmount(row.total_amt) }}
          </template>
        </vxe-column>
        <vxe-column field="total_tax_amt" title="含税总金额" width="120" class-name="col--right">
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
        <vxe-column field="delivery_status" title="发货状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getDeliveryStatusInfo(row.delivery_status).class">
              {{ getDeliveryStatusInfo(row.delivery_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="receive_status" title="收货状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getReceiveStatusInfo(row.receive_status).class">
              {{ getReceiveStatusInfo(row.receive_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="invoice_status" title="开票状态" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="getInvoiceStatusInfo(row.invoice_status).class">
              {{ getInvoiceStatusInfo(row.invoice_status).label }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="settle_type" title="结算方式" width="100" class-name="col--center" />
        <vxe-column title="操作" width="240" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="emit('navigate', 'sales-order-detail', { orderNo: row.order_no })">详情</button>
              <button class="btn-link" @click="openEditOrder(row)" v-if="row.order_status === 'draft'">编辑</button>
              <button class="btn-link success" @click="confirmAudit(row.order_no)" v-if="row.order_status === 'draft'">审核</button>
              <button class="btn-link primary" @click="confirmPushPurchase(row.order_no)" v-if="row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase'">下推采购</button>
              <button class="btn-link warning" @click="confirmClose(row.order_no)" v-if="row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase'">关闭</button>
              <button class="btn-link danger" @click="confirmCancel(row.order_no)" v-if="row.order_status === 'draft' || row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase'">取消</button>
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
          <h3>{{ editingOrder ? '编辑销售订单' : '新建销售订单' }}</h3>
          <button class="modal-close" @click="showOrderModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>订单日期 *</label>
                <input type="date" class="date-input" v-model="orderForm.order_date" />
              </div>
              <div class="form-group">
                <label>客户 *</label>
                <div class="search-select">
                  <input
                    type="text"
                    v-model="customerSearchKeyword"
                    @input="handleCustomerSearch"
                    @focus="showCustomerDropdown = true; loadCustomers(customerSearchKeyword || undefined)"
                    placeholder="输入客户名称/编码搜索"
                  />
                  <div class="search-dropdown" v-if="showCustomerDropdown && filteredCustomers.length > 0">
                    <div
                      v-for="c in filteredCustomers"
                      :key="c.id"
                      class="search-option"
                      @click="selectCustomer(c)"
                    >
                      {{ c.name }} ({{ c.customer_code }})
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
                      {{ addr.recipient_name }} - {{ addr.recipient_phone }} - {{ addr.province || '' }} {{ addr.city || '' }} {{ addr.address }}{{ addr.is_default ? ' (默认)' : '' }}
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
                    <th style="width: 200px">商品</th>
                    <th style="width: 100px">规格编码</th>
                    <th style="width: 120px">包装和包装单位</th>
                    <th style="width: 80px">数量</th>
                    <th style="width: 100px">单价</th>
                    <th style="width: 80px">折扣</th>
                    <th style="width: 100px">折后价</th>
                    <th style="width: 100px">金额</th>
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
                  <tr v-for="(item, index) in orderForm.items" :key="index">
                    <td>{{ item.row_no }}</td>
                    <td>
                      <div class="search-select">
                        <input
                          type="text"
                          :value="productSearchKeywords[index] ?? (item.product_name ? (item.brand_name ? '[' + item.brand_name + '] ' + item.product_name : item.product_name) : '')"
                          @focus="showProductDropdown = index; productTree = []"
                          @input="handleProductSearch(index, ($event.target as HTMLInputElement).value)"
                          placeholder="输入规格编号搜索"
                        />
                        <div class="search-dropdown product-tree-dropdown" v-if="showProductDropdown === index">
                          <!-- 规格搜索结果 -->
                          <template v-if="specSearchResults.length > 0">
                            <div
                              v-for="specResult in specSearchResults"
                              :key="specResult.id"
                              class="search-option spec-search-item"
                              :class="{ 'inactive': !specResult.is_active }"
                              @click="selectSpecFromSearch(specResult)"
                            >
                              <span class="spec-code">{{ specResult.spec_code }}</span>
                              <span class="spec-info" v-if="specResult.packaging || specResult.sales_spec">{{ [specResult.packaging, specResult.sales_spec].filter(Boolean).join(' - ') }}</span>
                              <span class="brand-name" v-if="specResult.brand_name">[{{ specResult.brand_name }}]</span>
                              <span class="product-name-small">{{ specResult.product_name }}</span>
                              <span class="spec-price">¥{{ specResult.price.toFixed(2) }}</span>
                              <span class="spec-status" v-if="!specResult.is_active">停用</span>
                            </div>
                          </template>
                          <div v-if="specSearchResults.length === 0" class="search-option disabled">
                            输入关键字搜索规格编号
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>{{ item.spec_code || '-' }}</td>
                    <td>{{ (item.packaging && item.sales_spec) ? item.packaging + ' - ' + item.sales_spec : (item.packaging || item.sales_spec || '-') }}</td>
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
                    <td>
                      <select v-model="item.shipping_method" @change="if(item.shipping_method === '直运') { item.warehouse_id = ''; item.warehouse_name = '' }">
                        <option v-for="s in shippingMethodOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                      </select>
                    </td>
                    <td v-if="item.shipping_method !== '直运'">
                      <select
                        :value="item.warehouse_id"
                        @focus="loadSpecStock(item.spec_id)"
                        @change="onWarehouseChange(index, ($event.target as HTMLSelectElement).value)"
                      >
                        <option value="">请选择仓库</option>
                        <option v-for="w in warehouseList" :key="w.id" :value="w.id">
                          {{ w.name }}{{ item.spec_id ? ' (库存: ' + (getStockQty(item.spec_id, w.id) !== null ? getStockQty(item.spec_id, w.id) : '加载中') + ')' : '' }}
                        </option>
                      </select>
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
                <span>商品总金额：</span>
                <span>{{ formatAmount(totalAmount) }}</span>
              </div>
              <div class="summary-row">
                <span>总折扣金额：</span>
                <span>-{{ formatAmount(totalDiscountAmount) }}</span>
              </div>
              <div class="summary-row total">
                <span>最终金额：</span>
                <span>{{ formatAmount(totalAmount - totalDiscountAmount) }}</span>
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
                  <label>收货状态</label>
                  <span class="status-tag" :class="getReceiveStatusInfo(selectedOrder.receive_status).class">
                    {{ getReceiveStatusInfo(selectedOrder.receive_status).label }}
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
              <div class="section-title">状态更新</div>
              <div class="status-actions">
                <div class="status-group">
                  <label>订单状态：</label>
                  <select
                    v-model="selectedOrder.order_status"
                    @change="handleUpdateOrderStatus(selectedOrder.order_no, selectedOrder.order_status)"
                    :disabled="selectedOrder.order_status === 'closed' || selectedOrder.order_status === 'cancelled'"
                  >
                    <option v-for="s in orderStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </div>
                <div class="status-group">
                  <label>发货状态：</label>
                  <select
                    v-model="selectedOrder.delivery_status"
                    @change="handleUpdateDeliveryStatus(selectedOrder.order_no, selectedOrder.delivery_status)"
                  >
                    <option v-for="s in deliveryStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </div>
                <div class="status-group">
                  <label>收货状态：</label>
                  <select
                    v-model="selectedOrder.receive_status"
                    @change="handleUpdateReceiveStatus(selectedOrder.order_no, selectedOrder.receive_status)"
                  >
                    <option v-for="s in receiveStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </div>
                <div class="status-group">
                  <label>开票状态：</label>
                  <select
                    v-model="selectedOrder.invoice_status"
                    @change="handleUpdateInvoiceStatus(selectedOrder.order_no, selectedOrder.invoice_status)"
                  >
                    <option v-for="s in invoiceStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
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
            v-if="selectedOrder.order_status === 'audited' || selectedOrder.order_status === 'partially_pushed_to_purchase'"
            @click="confirmClose(selectedOrder.order_no)"
          >
            关闭订单
          </button>
          <button
            class="btn-primary"
            v-if="selectedOrder.order_status === 'audited' || selectedOrder.order_status === 'partially_pushed_to_purchase'"
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
      <div class="modal" style="max-width: 500px;">
        <div class="modal-header">
          <h3>新增收货地址</h3>
          <button class="modal-close" @click="showQuickAddShippingModal = false">&times;</button>
        </div>
        <div class="modal-body">
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
        <div class="modal-footer">
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

.filter-input {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
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
  min-width: 120px;
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
  overflow-x: auto;
}

.order-link {
  color: var(--accent-blue);
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

.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.audited { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.pushed { background-color: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.status-tag.partial-pushed { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.closed { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }

.status-tag.none { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }

.action-btns {
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

.btn-link.success {
  color: #10b981;
}

.btn-link.success:hover {
  background-color: rgba(16, 185, 129, 0.1);
}

.btn-link.warning {
  color: #f59e0b;
}

.btn-link.warning:hover {
  background-color: rgba(245, 158, 11, 0.1);
}

.btn-link.primary {
  color: var(--accent-blue);
}

.btn-link.primary:hover {
  background-color: rgba(0, 120, 212, 0.1);
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
  background-color: var(--bg-card);
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
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  background-color: var(--bg-card);
  z-index: 1;
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
  gap: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.form-section {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
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
  color: var(--text-secondary);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
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
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

.search-select input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  margin-top: 4px;
}

.search-option {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  transition: background-color var(--transition-fast);
}

.search-option:hover {
  background-color: var(--bg-secondary);
}

.search-option.disabled {
  color: var(--text-muted);
  cursor: default;
}

.search-option.disabled:hover {
  background-color: transparent;
}

.search-dropdown-filter {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  background-color: var(--bg-card);
}

.search-dropdown-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.search-dropdown-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.date-input {
  color-scheme: light;
}

[data-theme="dark"] .date-input {
  color-scheme: dark;
}

.items-table {
  background-color: var(--bg-card);
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
  border-bottom: 1px solid var(--border-color);
}

.items-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.items-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.items-table input,
.items-table select {
  width: 100%;
  padding: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
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
  border: 1px dashed var(--border-color);
  border-radius: 0;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-item-btn:hover {
  background-color: rgba(0, 120, 212, 0.05);
  border-color: var(--accent-blue);
}

.amount-summary {
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  padding: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.summary-row.total {
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
  padding-top: 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Detail styles */
.detail-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.detail-section {
  background-color: var(--bg-secondary);
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
  color: var(--text-muted);
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
}

.amount-highlight {
  color: var(--accent-blue) !important;
  font-weight: 600;
  font-size: 16px !important;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.detail-table th,
.detail-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.detail-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.detail-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.remarks-text {
  font-size: 14px;
  color: var(--text-primary);
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
  border-left: 2px solid var(--border-color);
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
  background-color: var(--accent-blue);
  border: 2px solid var(--bg-card);
}

.flow-item:last-child .flow-dot {
  background-color: #10b981;
}

.flow-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.flow-time {
  font-size: 12px;
  color: var(--text-muted);
}

.flow-detail {
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-field {
  font-weight: 500;
  color: var(--text-primary);
}

.flow-old {
  color: var(--text-muted);
  text-decoration: line-through;
}

.flow-arrow {
  color: var(--text-muted);
}

.flow-new {
  color: var(--accent-blue);
  font-weight: 500;
}

.flow-operator {
  font-size: 12px;
  color: var(--text-muted);
}

.flow-remark {
  font-size: 12px;
  color: var(--text-secondary);
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
  color: var(--text-secondary);
}

.status-group select {
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  min-width: 120px;
}

/* Buttons */
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

.btn-quick-add {
  width: 32px;
  min-width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent-blue);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 18px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-quick-add:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
}

.btn-quick-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.btn-success {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: #10b981;
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-success:hover:not(:disabled) {
  background-color: #059669;
}

.btn-success:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-warning {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: #f59e0b;
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-warning:hover:not(:disabled) {
  background-color: #d97706;
}

.btn-warning:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-red);
  color: white;
  font-size: 14px;
  border: none;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
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
  color: var(--text-primary);
  margin: 0;
}

/* Table loading */
.table-loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.table-loading-content {
  padding: 20px 40px;
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-hover);
  font-size: 14px;
  color: var(--text-primary);
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
  background-color: var(--bg-secondary);
}

.expand-icon {
  font-size: 10px;
  transition: transform 0.2s;
  color: var(--text-muted);
  width: 14px;
  text-align: center;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.brand-name {
  font-size: 12px;
  color: var(--accent-blue);
  margin-right: 2px;
}

.product-name {
  font-size: 14px;
  color: var(--text-primary);
}

.product-code {
  font-size: 12px;
  color: var(--text-muted);
}

.spec-count {
  font-size: 11px;
  color: var(--accent-blue);
  margin-left: auto;
}

.spec-list {
  border-left: 2px solid var(--border-color);
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
  color: var(--text-primary);
  font-weight: 500;
}

.spec-info {
  color: var(--text-muted);
  font-size: 12px;
}

.spec-price {
  color: var(--accent-blue);
  font-size: 13px;
  margin-left: auto;
}

.spec-status {
  font-size: 11px;
  color: var(--accent-red);
  background-color: rgba(239, 68, 68, 0.1);
  padding: 1px 4px;
  border-radius: 2px;
}

.spec-search-header {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  border-top: 1px solid var(--border-color);
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

.product-name-small {
  font-size: 12px;
  color: var(--text-muted);
}

/* Expand items panel */
.expand-items-panel {
  padding: 12px 16px;
  background-color: var(--bg-card);
}

:deep(.vxe-body--column) {
  &.expand--cell,
  &.col--actived {
    background-color: var(--bg-card) !important;
  }
}

:deep(.vxe-body--row.expand--row > td) {
  background-color: var(--bg-card) !important;
}

:deep(.vxe-body--row.expand--row:hover > td) {
  background-color: var(--bg-secondary) !important;
}

:deep(.vxe-body--row) > td {
  background-color: var(--bg-card) !important;
}

:deep(.vxe-body--row:hover) > td {
  background-color: var(--bg-secondary) !important;
}

.expand-items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background-color: var(--bg-card);
}

.expand-items-table th {
  padding: 8px 10px;
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.expand-items-table td {
  padding: 8px 10px;
  color: var(--text-primary);
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.expand-items-table tr:last-child td {
  border-bottom: none;
}
</style>