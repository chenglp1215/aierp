<script setup lang="ts">
defineOptions({ name: 'SalesOrderList' })

import { ref, computed, onMounted, watch } from 'vue'
import { salesOrderApi, customerApi, productApi, warehouseApi } from '../../services/api'

// Types
interface SalesOrderItem {
  product_id: string
  product_name: string
  product_code?: string
  quantity: number
  unit_price: number
  subtotal: number
}

interface SalesOrder {
  id: string
  order_no: string
  customer_id: string
  customer_name: string
  contact_phone?: string
  delivery_address?: string
  delivery_type: 'inventory' | 'direct'
  warehouse_id?: string
  warehouse_name?: string
  pickup_type: 'self_pickup' | 'express'
  express_type?: 'sf' | 'yto' | 'zto' | 'jd' | 'ems' | 'other'
  express_no?: string
  express_fee: number
  discount_ratio: number
  items: SalesOrderItem[]
  total_amount: number
  discount_amount: number
  final_amount: number
  order_status: string
  delivery_status?: string
  receive_status?: string
  invoice_status?: string
  procurement_order_id?: string
  order_date: string
  expected_delivery_date?: string
  remarks?: string
  created_at: string
}

interface Customer {
  id: string
  name: string
}

interface Product {
  id: string
  name: string
  code?: string
  price: number
}

interface Warehouse {
  id: string
  name: string
}

// Constants
const statusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待审核', class: 'pending' },
  audited: { label: '已审核', class: 'audited' },
  partially_pushed_to_purchase: { label: '部分下推采购', class: 'partial-pushed' },
  pushed_to_purchase: { label: '已下推采购', class: 'pushed' },
  closed: { label: '已关闭', class: 'closed' },
  cancelled: { label: '已取消', class: 'cancelled' }
}

const deliveryTypes = [
  { value: 'inventory', label: '库存发货' },
  { value: 'direct', label: '采购直发' }
]

const pickupTypes = [
  { value: 'self_pickup', label: '自取' },
  { value: 'express', label: '快递' }
]

const expressTypes = [
  { value: 'sf', label: '顺丰' },
  { value: 'yto', label: '圆通' },
  { value: 'zto', label: '中通' },
  { value: 'jd', label: '京东' },
  { value: 'ems', label: 'EMS' },
  { value: 'other', label: '其他' }
]

const orderStatuses = Object.entries(statusMap).map(([value, { label }]) => ({ value, label }))

// State
const loading = ref(false)
const orders = ref<SalesOrder[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')
const filterCustomerId = ref('')

// Modals
const showOrderModal = ref(false)
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const editingOrder = ref<SalesOrder | null>(null)
const selectedOrder = ref<SalesOrder | null>(null)
const deleteTargetOrderNo = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)
const detailLoading = ref(false)

// Customer/Product/Warehouse lists for dropdowns
const customerList = ref<Customer[]>([])
const productList = ref<Product[]>([])
const warehouseList = ref<Warehouse[]>([])

// Search dropdown states
const customerSearchResults = ref<any[]>([])
const productSearchResults = ref<any[]>([])
const warehouseSearchResults = ref<any[]>([])
const showCustomerDropdown = ref(false)
const showProductDropdown = ref<number | null>(null)
const showWarehouseDropdown = ref(false)
const customerSearchInput = ref('')
const productSearchInput = ref('')
const warehouseSearchInput = ref('')
let customerSearchTimer: any = null
let productSearchTimer: any = null
let warehouseSearchTimer: any = null

// Form
const orderForm = ref({
  customer_id: '',
  customer_name: '',
  receiver_name: '',
  contact_phone: '',
  delivery_address: '',
  delivery_type: 'inventory' as 'inventory' | 'direct',
  warehouse_id: '',
  warehouse_name: '',
  pickup_type: 'express' as 'self_pickup' | 'express',
  express_type: '' as string,
  express_no: '',
  express_fee: 0,
  discount_ratio: 100,
  expected_delivery_date: '',
  remarks: '',
  items: [] as SalesOrderItem[]
})

// Computed
const hasActiveFilters = computed(() => !!(keyword.value || filterStatus.value || filterCustomerId.value))

const totalAmount = computed(() => {
  const subtotal = orderForm.value.items.reduce((sum, item) => sum + item.subtotal, 0)
  return subtotal
})

const discountAmount = computed(() => {
  return totalAmount.value * (1 - orderForm.value.discount_ratio / 100)
})

const finalAmount = computed(() => {
  return totalAmount.value - discountAmount.value + orderForm.value.express_fee
})

// Methods
const loadOrders = async () => {
  loading.value = true
  try {
    const res = await salesOrderApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      customer_id: filterCustomerId.value || undefined,
      order_no: keyword.value || undefined
    })
    orders.value = res.items.map((item: any) => ({
      ...item,
      status: item.status,
      payment_status: item.payment_status
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载订单列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    const res = await customerApi.list({ page_size: 100 })
    customerList.value = res.items.map((c: any) => ({ id: c.id, name: c.name }))
  } catch (error) {
    console.error('加载客户列表失败:', error)
  }
}

const loadProducts = async () => {
  try {
    const res = await productApi.list({ page_size: 100 })
    productList.value = (res?.items || []).map((p: any) => ({
      id: p.id,
      name: p.name,
      code: p.product_code,
      price: p.price || 0
    }))
  } catch (error) {
    console.error('加载商品列表失败:', error)
  }
}

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page_size: 100 })
    warehouseList.value = res.items.map((w: any) => ({ id: w.id, name: w.name }))
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  }
}

const searchCustomers = async (keyword: string) => {
  if (!keyword || keyword.length < 1) {
    customerSearchResults.value = []
    return
  }
  try {
    const res: any = await customerApi.search(keyword, 10)
    customerSearchResults.value = res || []
  } catch (error) {
    console.error('搜索客户失败:', error)
    customerSearchResults.value = []
  }
}

const searchProducts = async (keyword: string) => {
  if (!keyword || keyword.length < 1) {
    productSearchResults.value = []
    return
  }
  try {
    const res: any = await productApi.search(keyword, 10)
    productSearchResults.value = res || []
  } catch (error) {
    console.error('搜索商品失败:', error)
    productSearchResults.value = []
  }
}

const searchWarehouses = async (keyword: string) => {
  if (!keyword || keyword.length < 1) {
    warehouseSearchResults.value = []
    return
  }
  try {
    const res: any = await warehouseApi.list({ page_size: 100 })
    const keywordLower = keyword.toLowerCase()
    warehouseSearchResults.value = (res.items || []).filter((w: any) =>
      w.name.toLowerCase().includes(keywordLower)
    )
  } catch (error) {
    console.error('搜索仓库失败:', error)
    warehouseSearchResults.value = []
  }
}

const handleCustomerSearchInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  customerSearchInput.value = value
  showCustomerDropdown.value = true
  clearTimeout(customerSearchTimer)
  customerSearchTimer = setTimeout(() => {
    searchCustomers(value)
  }, 300)
}

const handleProductSearchInput = (index: number, event: Event) => {
  const value = (event.target as HTMLInputElement).value
  productSearchInput.value = value
  showProductDropdown.value = index
  clearTimeout(productSearchTimer)
  productSearchTimer = setTimeout(() => {
    searchProducts(value)
  }, 300)
}

const handleWarehouseSearchInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  warehouseSearchInput.value = value
  showWarehouseDropdown.value = true
  clearTimeout(warehouseSearchTimer)
  warehouseSearchTimer = setTimeout(() => {
    searchWarehouses(value)
  }, 300)
}

const selectCustomer = (customer: any) => {
  orderForm.value.customer_id = customer.id
  orderForm.value.customer_name = customer.name
  customerSearchInput.value = customer.name
  showCustomerDropdown.value = false
  customerSearchResults.value = []

  if (customer.shipping_addresses && customer.shipping_addresses.length > 0) {
    const defaultAddr = customer.shipping_addresses.find((a: any) => a.is_default) || customer.shipping_addresses[0]
    if (defaultAddr) {
      const fullAddress = [defaultAddr.province, defaultAddr.city, defaultAddr.district, defaultAddr.address]
        .filter(Boolean)
        .join('')
      orderForm.value.receiver_name = defaultAddr.recipient_name || ''
      orderForm.value.contact_phone = defaultAddr.recipient_phone || customer.contact_phone || ''
      orderForm.value.delivery_address = fullAddress || customer.address || ''
    }
  } else {
    orderForm.value.receiver_name = customer.contact_person || ''
    orderForm.value.contact_phone = customer.contact_phone || ''
    orderForm.value.delivery_address = customer.address || ''
  }
}

const selectProduct = (index: number, product: any) => {
  orderForm.value.items[index].product_id = product.id
  orderForm.value.items[index].product_name = product.name
  orderForm.value.items[index].product_code = product.product_code
  orderForm.value.items[index].unit_price = product.price || 0
  orderForm.value.items[index].subtotal = product.price || 0
  productSearchInput.value = ''
  showProductDropdown.value = null
  productSearchResults.value = []
  updateItemSubtotal(index)
}

const selectWarehouse = (warehouse: any) => {
  orderForm.value.warehouse_id = warehouse.id
  orderForm.value.warehouse_name = warehouse.name
  warehouseSearchInput.value = warehouse.name
  showWarehouseDropdown.value = false
  warehouseSearchResults.value = []
}

const closeAllDropdowns = () => {
  showCustomerDropdown.value = false
  showProductDropdown.value = null
  showWarehouseDropdown.value = false
}

const handleSearch = () => {
  page.value = 1
  loadOrders()
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadOrders()
}

const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  filterCustomerId.value = ''
  page.value = 1
  loadOrders()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetOrderForm = () => {
  orderForm.value = {
    customer_id: '',
    customer_name: '',
    receiver_name: '',
    contact_phone: '',
    delivery_address: '',
    delivery_type: 'inventory',
    warehouse_id: '',
    warehouse_name: '',
    pickup_type: 'express',
    express_type: '',
    express_no: '',
    express_fee: 0,
    discount_ratio: 100,
    expected_delivery_date: '',
    remarks: '',
    items: []
  }
  editingOrder.value = null
  customerSearchInput.value = ''
  warehouseSearchInput.value = ''
  productSearchInput.value = ''
  customerSearchResults.value = []
  productSearchResults.value = []
  warehouseSearchResults.value = []
  showCustomerDropdown.value = false
  showProductDropdown.value = null
  showWarehouseDropdown.value = false
}

const openCreateOrder = () => {
  resetOrderForm()
  showOrderModal.value = true
}

const openEditOrder = (order: SalesOrder) => {
  editingOrder.value = order
  orderForm.value = {
    customer_id: order.customer_id,
    customer_name: order.customer_name,
    receiver_name: (order as any).receiver_name || '',
    contact_phone: order.contact_phone || '',
    delivery_address: order.delivery_address || '',
    delivery_type: order.delivery_type,
    warehouse_id: order.warehouse_id || '',
    warehouse_name: order.warehouse_name || '',
    pickup_type: order.pickup_type,
    express_type: order.express_type || '',
    express_no: order.express_no || '',
    express_fee: order.express_fee,
    discount_ratio: order.discount_ratio,
    expected_delivery_date: order.expected_delivery_date ? order.expected_delivery_date.split('T')[0] : '',
    remarks: order.remarks || '',
    items: [...order.items]
  }
  customerSearchInput.value = order.customer_name
  showOrderModal.value = true
}

const openDetail = async (order: SalesOrder) => {
  selectedOrder.value = order
  detailLoading.value = true
  showDetailModal.value = true
  try {
    const res = await salesOrderApi.getByOrderNo(order.order_no)
    selectedOrder.value = res
  } catch (error) {
    console.error('加载订单详情失败:', error)
  } finally {
    detailLoading.value = false
  }
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
    // 直接从列表中 filter 移除，不整体刷新
    orders.value = orders.value.filter(o => o.order_no !== deleteTargetOrderNo.value)
    total.value--
    showDeleteConfirm.value = false
    deleteTargetOrderNo.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const addOrderItem = () => {
  orderForm.value.items.push({
    product_id: '',
    product_name: '',
    product_code: '',
    quantity: 1,
    unit_price: 0,
    subtotal: 0
  })
}

const removeOrderItem = (index: number) => {
  orderForm.value.items.splice(index, 1)
}

const updateItemSubtotal = (index: number) => {
  const item = orderForm.value.items[index]
  item.subtotal = item.quantity * item.unit_price
}

const handleSaveOrder = async () => {
  if (!orderForm.value.customer_id) {
    window.showToast('请选择客户', 'warning')
    return
  }
  if (orderForm.value.items.length === 0) {
    window.showToast('请添加商品明细', 'warning')
    return
  }

  if (orderForm.value.delivery_type === 'inventory' && !orderForm.value.warehouse_id) {
    window.showToast('库存发货模式请选择仓库', 'warning')
    return
  }

  if (orderForm.value.pickup_type === 'express' && !orderForm.value.express_type) {
    window.showToast('快递模式请选择快递方式', 'warning')
    return
  }

  for (let i = 0; i < orderForm.value.items.length; i++) {
    const item = orderForm.value.items[i]
    if (!item.product_id) {
      window.showToast(`第${i + 1}行商品未选择`, 'warning')
      return
    }
    if (!item.quantity || item.quantity <= 0) {
      window.showToast(`第${i + 1}行商品数量必须大于0`, 'warning')
      return
    }
  }

  formLoading.value = true
  try {
    const submitData: any = {
      ...orderForm.value,
      express_type: orderForm.value.express_type || null,
      expected_delivery_date: orderForm.value.expected_delivery_date || null,
      items: orderForm.value.items.map(item => ({
        ...item,
        subtotal: item.quantity * item.unit_price
      }))
    }

    if (editingOrder.value) {
      // 编辑模式：直接更新列表项，不整体刷新
      await salesOrderApi.update(editingOrder.value.order_no, submitData)
      window.showToast('订单更新成功', 'success')
      const index = orders.value.findIndex(o => o.order_no === editingOrder.value!.order_no)
      if (index !== -1) {
        const updatedOrder = {
          ...orders.value[index],
          ...submitData,
          total_amount: submitData.items.reduce((sum: number, item: any) => sum + item.subtotal, 0),
          discount_amount: submitData.items.reduce((sum: number, item: any) => sum + item.subtotal, 0) * (1 - submitData.discount_ratio / 100),
          final_amount: submitData.items.reduce((sum: number, item: any) => sum + item.subtotal, 0) * (submitData.discount_ratio / 100) + (submitData.express_fee || 0)
        }
        orders.value[index] = updatedOrder
      }
    } else {
      // 新建模式：整体刷新
      await salesOrderApi.create(submitData)
      window.showToast('订单创建成功', 'success')
      loadOrders()
    }
    showOrderModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleUpdateStatus = async (orderNo: string, status: string) => {
  try {
    // 根据状态调用不同的 API
    if (status === 'audited') {
      await salesOrderApi.approve(orderNo)
    } else if (status === 'cancelled') {
      await salesOrderApi.cancel(orderNo)
    } else if (status === 'draft') {
      await salesOrderApi.reject(orderNo)
    } else {
      // 其他状态暂不支持直接更新
      window.showToast('该状态暂不支持直接更新', 'warning')
      return
    }
    window.showToast('状态更新成功', 'success')
    // 直接更新列表项状态，不整体刷新
    const index = orders.value.findIndex(o => o.order_no === orderNo)
    if (index !== -1) {
      orders.value[index] = { ...orders.value[index], order_status: status }
    }
    // 更新详情弹窗中的订单状态
    if (selectedOrder.value?.order_no === orderNo) {
      selectedOrder.value = { ...selectedOrder.value, order_status: status }
    }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}

// 提交审核
const handleSubmitOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.submit(orderNo)
    window.showToast('订单已提交审核', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '提交失败', 'error')
  }
}

// 审核通过
const handleApproveOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.approve(orderNo)
    window.showToast('订单审核通过', 'success')
    const index = orders.value.findIndex(o => o.order_no === orderNo)
    if (index !== -1) {
      orders.value[index] = { ...orders.value[index], order_status: 'audited' }
    }
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  }
}

// 驳回
const handleRejectOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.reject(orderNo)
    window.showToast('订单已驳回', 'success')
    const index = orders.value.findIndex(o => o.order_no === orderNo)
    if (index !== -1) {
      orders.value[index] = { ...orders.value[index], order_status: 'draft' }
    }
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  }
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatAmount = (amount: number) => {
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

const getStatusInfo = (status: string) => statusMap[status] || { label: status, class: '' }

// Watch
watch(() => orderForm.value.discount_ratio, (newVal) => {
  if (newVal < 0) orderForm.value.discount_ratio = 0
  if (newVal > 100) orderForm.value.discount_ratio = 100
})

// Lifecycle
onMounted(() => {
  loadOrders()
  loadCustomers()
  loadProducts()
  loadWarehouses()
})
</script>

<template>
  <div class="sales-order-list">
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
            placeholder="搜索订单编号、客户名称..."
            v-model="keyword"
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
            <option v-for="s in orderStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
      <div class="active-filters" v-if="hasActiveFilters">
        <span class="filter-tag" v-if="keyword">
          关键词: {{ keyword }}
          <button class="tag-close" @click="clearKeyword">×</button>
        </span>
        <span class="filter-tag" v-if="filterStatus">
          状态: {{ getStatusInfo(filterStatus).label }}
          <button class="tag-close" @click="filterStatus = ''; handleSearch()">×</button>
        </span>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 130px">订单编号</th>
            <th>客户名称</th>
            <th style="width: 100px">发货方式</th>
            <th style="width: 100px; text-align: right">订单金额</th>
            <th style="width: 80px">订单状态</th>
            <th style="width: 100px">下单日期</th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="orders.length === 0">
            <td colspan="7" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="order in orders" :key="order.order_no">
            <td>{{ order.order_no }}</td>
            <td>{{ order.customer_name }}</td>
            <td>
              <span v-if="order.delivery_type === 'inventory'">
                库存发货
                <span v-if="order.warehouse_name" class="warehouse-tag">({{ order.warehouse_name }})</span>
              </span>
              <span v-else>采购直发</span>
            </td>
            <td style="text-align: right">{{ formatAmount(order.final_amount) }}</td>
            <td>
              <span class="status-tag" :class="getStatusInfo(order.order_status).class">
                {{ getStatusInfo(order.order_status).label }}
              </span>
            </td>
            <td>{{ formatDate(order.order_date) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openDetail(order)">详情</button>
                <button class="btn-link" @click="openEditOrder(order)" v-if="order.order_status === 'draft'">编辑</button>
                <button class="btn-link highlight" @click="handleSubmitOrder(order.order_no)" v-if="order.order_status === 'draft'">提交审核</button>
                <button class="btn-link success" @click="handleApproveOrder(order.order_no)" v-if="order.order_status === 'pending'">审核通过</button>
                <button class="btn-link warning" @click="handleRejectOrder(order.order_no)" v-if="order.order_status === 'pending'">驳回</button>
                <button class="btn-link danger" @click="confirmDelete(order.order_no)" v-if="order.order_status === 'draft'">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="orders.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <!-- Order Form Modal -->
    <div class="modal-overlay" v-if="showOrderModal" @click.self="showOrderModal = false">
      <div class="modal order-modal">
        <div class="modal-header">
          <h3>{{ editingOrder ? '编辑销售订单' : '新建销售订单' }}</h3>
          <button class="modal-close" @click="showOrderModal = false">&times;</button>
        </div>
        <div class="modal-body" @click="closeAllDropdowns">
          <div class="form-section">
            <h4>客户信息</h4>
            <div class="form-row">
              <div class="form-group search-select">
                <label>客户 *</label>
                <div class="search-input-wrapper">
                  <input
                    type="text"
                    :value="customerSearchInput"
                    @input="handleCustomerSearchInput"
                    @focus="showCustomerDropdown = true"
                    placeholder="输入客户名称搜索"
                  />
                  <div class="search-dropdown" v-if="showCustomerDropdown && customerSearchResults.length > 0">
                    <div
                      v-for="c in customerSearchResults"
                      :key="c.id"
                      class="search-option"
                      @click.stop="selectCustomer(c)"
                    >
                      {{ c.name }}
                    </div>
                  </div>
                </div>
              </div>
              <div class="form-group">
                <label>收货人</label>
                <input type="text" v-model="orderForm.receiver_name" placeholder="请输入收货人" />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input type="text" v-model="orderForm.contact_phone" placeholder="请输入联系电话" />
              </div>
            </div>
            <div class="form-group">
              <label>交货地址</label>
              <input type="text" v-model="orderForm.delivery_address" placeholder="请输入交货地址" />
            </div>
          </div>

          <div class="form-section">
            <h4>发货信息</h4>
            <div class="form-row">
              <div class="form-group">
                <label>发货方式 *</label>
                <select v-model="orderForm.delivery_type">
                  <option v-for="t in deliveryTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <div class="form-group search-select" v-if="orderForm.delivery_type === 'inventory'">
                <label>发货仓库 *</label>
                <div class="search-input-wrapper">
                  <input
                    type="text"
                    :value="warehouseSearchInput"
                    @input="handleWarehouseSearchInput"
                    @focus="showWarehouseDropdown = true"
                    placeholder="输入仓库名称搜索"
                  />
                  <div class="search-dropdown" v-if="showWarehouseDropdown && warehouseSearchResults.length > 0">
                    <div
                      v-for="w in warehouseSearchResults"
                      :key="w.id"
                      class="search-option"
                      @click.stop="selectWarehouse(w)"
                    >
                      {{ w.name }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>取货方式 *</label>
                <select v-model="orderForm.pickup_type">
                  <option v-for="p in pickupTypes" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
              <div class="form-group" v-if="orderForm.pickup_type === 'express'">
                <label>快递方式</label>
                <select v-model="orderForm.express_type">
                  <option value="">请选择</option>
                  <option v-for="e in expressTypes" :key="e.value" :value="e.value">{{ e.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row" v-if="orderForm.pickup_type === 'express'">
              <div class="form-group">
                <label>快递单号</label>
                <input type="text" v-model="orderForm.express_no" placeholder="请输入快递单号" />
              </div>
              <div class="form-group">
                <label>快递费用</label>
                <input type="number" v-model="orderForm.express_fee" min="0" step="0.01" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>预计交货日期</label>
                <input type="date" v-model="orderForm.expected_delivery_date" />
              </div>
              <div class="form-group">
                <label>折扣比例 (%)</label>
                <input type="number" v-model="orderForm.discount_ratio" min="0" max="100" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>商品明细</h4>
            <div class="items-table">
              <table>
                <thead>
                  <tr>
                    <th style="width: 200px">商品</th>
                    <th style="width: 100px">商品编码</th>
                    <th style="width: 80px">数量</th>
                    <th style="width: 120px">单价</th>
                    <th style="width: 120px">小计</th>
                    <th style="width: 60px">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in orderForm.items" :key="index">
                    <td>
                      <div class="search-input-wrapper product-search">
                        <input
                          type="text"
                          :value="item.product_name || ''"
                          @input="handleProductSearchInput(index, $event)"
                          @focus="showProductDropdown = index"
                          placeholder="输入商品搜索"
                        />
                        <div class="search-dropdown" v-if="showProductDropdown === index && productSearchResults.length > 0">
                          <div
                            v-for="p in productSearchResults"
                            :key="p.id"
                            class="search-option"
                            @click.stop="selectProduct(index, p)"
                          >
                            {{ p.name }} ({{ p.product_code || '无编码' }})
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>{{ item.product_code || '-' }}</td>
                    <td>
                      <input type="number" v-model="item.quantity" min="1" @input="updateItemSubtotal(index)" />
                    </td>
                    <td>
                      <input type="number" v-model="item.unit_price" min="0" step="0.01" @input="updateItemSubtotal(index)" />
                    </td>
                    <td>{{ formatAmount(item.quantity * item.unit_price) }}</td>
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
            <h4>费用汇总</h4>
            <div class="amount-summary">
              <div class="summary-row">
                <span>商品总金额：</span>
                <span>{{ formatAmount(totalAmount) }}</span>
              </div>
              <div class="summary-row">
                <span>折扣 ({{ orderForm.discount_ratio }}%)：</span>
                <span>-{{ formatAmount(discountAmount) }}</span>
              </div>
              <div class="summary-row">
                <span>快递费用：</span>
                <span>+{{ formatAmount(orderForm.express_fee) }}</span>
              </div>
              <div class="summary-row total">
                <span>最终金额：</span>
                <span>{{ formatAmount(finalAmount) }}</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>备注</label>
            <textarea v-model="orderForm.remarks" placeholder="请输入备注" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showOrderModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveOrder" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Order Detail Modal -->
    <div class="modal-overlay" v-if="showDetailModal" @click.self="showDetailModal = false">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>订单详情 - {{ selectedOrder?.order_no }}</h3>
          <button class="modal-close" @click="showDetailModal = false">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedOrder">
          <div class="detail-loading" v-if="detailLoading">加载中...</div>
          <template v-else>
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>订单编号</label>
                  <span>{{ selectedOrder.order_no }}</span>
                </div>
                <div class="detail-item">
                  <label>订单状态</label>
                  <span class="status-tag" :class="getStatusInfo(selectedOrder.order_status).class">
                    {{ getStatusInfo(selectedOrder.order_status).label }}
                  </span>
                </div>
                <div class="detail-item">
                  <label>下单日期</label>
                  <span>{{ formatDate(selectedOrder.order_date) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>客户信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>客户名称</label>
                  <span>{{ selectedOrder.customer_name }}</span>
                </div>
                <div class="detail-item">
                  <label>联系电话</label>
                  <span>{{ selectedOrder.contact_phone || '-' }}</span>
                </div>
                <div class="detail-item full-width">
                  <label>交货地址</label>
                  <span>{{ selectedOrder.delivery_address || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>发货信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>发货方式</label>
                  <span>{{ selectedOrder.delivery_type === 'inventory' ? '库存发货' : '采购直发' }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder.warehouse_name">
                  <label>发货仓库</label>
                  <span>{{ selectedOrder.warehouse_name }}</span>
                </div>
                <div class="detail-item">
                  <label>取货方式</label>
                  <span>{{ selectedOrder.pickup_type === 'self_pickup' ? '自取' : '快递' }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder?.express_type">
                  <label>快递方式</label>
                  <span>{{ expressTypes.find(e => e.value === selectedOrder?.express_type)?.label || selectedOrder?.express_type }}</span>
                </div>
                <div class="detail-item" v-if="selectedOrder.express_no">
                  <label>快递单号</label>
                  <span>{{ selectedOrder.express_no }}</span>
                </div>
                <div class="detail-item">
                  <label>快递费用</label>
                  <span>{{ formatAmount(selectedOrder.express_fee) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>商品明细</h4>
              <table class="detail-table">
                <thead>
                  <tr>
                    <th>商品名称</th>
                    <th>商品编码</th>
                    <th style="text-align: right">数量</th>
                    <th style="text-align: right">单价</th>
                    <th style="text-align: right">小计</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in selectedOrder.items" :key="index">
                    <td>{{ item.product_name }}</td>
                    <td>{{ item.product_code || '-' }}</td>
                    <td style="text-align: right">{{ item.quantity }}</td>
                    <td style="text-align: right">{{ formatAmount(item.unit_price) }}</td>
                    <td style="text-align: right">{{ formatAmount(item.subtotal) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="detail-section">
              <h4>费用信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>商品总金额</label>
                  <span>{{ formatAmount(selectedOrder.total_amount) }}</span>
                </div>
                <div class="detail-item">
                  <label>折扣比例</label>
                  <span>{{ selectedOrder.discount_ratio }}%</span>
                </div>
                <div class="detail-item">
                  <label>折扣金额</label>
                  <span>{{ formatAmount(selectedOrder.discount_amount) }}</span>
                </div>
                <div class="detail-item">
                  <label>快递费用</label>
                  <span>{{ formatAmount(selectedOrder.express_fee) }}</span>
                </div>
                <div class="detail-item">
                  <label>最终金额</label>
                  <span class="amount-highlight">{{ formatAmount(selectedOrder.final_amount) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedOrder.procurement_order_id">
              <h4>关联采购单</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>采购单ID</label>
                  <span>{{ selectedOrder.procurement_order_id }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="selectedOrder.remarks">
              <h4>备注</h4>
              <p class="remarks-text">{{ selectedOrder.remarks }}</p>
            </div>

            <div class="detail-section" v-if="selectedOrder.order_status !== 'draft'">
              <h4>状态更新</h4>
              <div class="status-actions">
                <button
                  class="btn-primary"
                  @click="handleUpdateStatus(selectedOrder.order_no, 'audited')"
                  v-if="selectedOrder.order_status === 'pending'"
                >
                  审核通过
                </button>
                <button
                  class="btn-primary"
                  @click="handleUpdateStatus(selectedOrder.order_no, 'closed')"
                  v-if="selectedOrder.order_status === 'audited'"
                >
                  关闭订单
                </button>
                <button
                  class="btn-danger"
                  @click="handleUpdateStatus(selectedOrder.order_no, 'cancelled')"
                  v-if="['draft', 'pending', 'audited'].includes(selectedOrder.order_status)"
                >
                  取消订单
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
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
  </div>
</template>

<style scoped>
.sales-order-list {
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

.filter-item.search-filter {
  flex: 1;
  min-width: 200px;
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

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 12px;
  background-color: rgba(0, 120, 212, 0.1);
  border-radius: 16px;
  font-size: 12px;
  color: var(--accent-blue);
}

.tag-close {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: rgba(0, 120, 212, 0.2);
  border: none;
  color: var(--accent-blue);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tag-close:hover {
  background-color: var(--accent-blue);
  color: white;
}

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  overflow-x: auto;
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

.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.audited { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.partial-pushed { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.status-tag.pushed { background-color: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.status-tag.closed { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.none { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }

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

.btn-link.highlight {
  color: var(--accent-green);
  font-weight: 500;
}

.btn-link.success {
  color: var(--accent-green);
}

.btn-link.success:hover {
  background-color: rgba(16, 185, 129, 0.1);
}

.btn-link.warning {
  color: var(--accent-yellow);
}

.btn-link.warning:hover {
  background-color: rgba(245, 158, 11, 0.1);
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.warehouse-tag {
  color: var(--accent-blue);
  font-size: 12px;
  margin-left: 4px;
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
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.order-modal {
  max-width: 1000px;
}

.detail-modal {
  max-width: 900px;
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

.form-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
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

.items-table {
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
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

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
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

.status-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

.search-select {
  position: relative;
}

.search-input-wrapper {
  position: relative;
}

.search-input-wrapper input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  color: var(--text-primary);
  font-size: 14px;
}

.search-input-wrapper input:focus {
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

.product-search {
  min-width: 180px;
}

.confirm-modal {
  max-width: 400px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
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
</style>
