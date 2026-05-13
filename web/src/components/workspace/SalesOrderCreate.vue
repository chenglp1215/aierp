<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import { salesOrderApi, customerApi, productApi, warehouseApi, customerDiscountApi, type Customer } from '../../services/api'
import { useProvinceCity } from '../../hooks/useProvinceCity'

const emit = defineEmits<{
  back: []
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

// Form state
const formLoading = ref(false)

// Dropdown data
const customerList = ref<Customer[]>([])
const productTree = ref<ProductWithSpecs[]>([])
const specSearchResults = ref<SpecSearchResult[]>([])
const warehouseList = ref<Warehouse[]>([])

// 仓库库存数据
const specStockMap = ref<Record<string, { warehouse_id: string; quantity: number }[]>>({})
// 表头批量设置
const headerShippingMethod = ref('')
const headerWarehouseId = ref('')
const headerWarehouseName = ref('')
const customersLoading = ref(false)

// Search states
const customerSearchKeyword = ref('')
const showCustomerDropdown = ref(false)
const showProductDropdown = ref<number | null>(null)
const showWarehouseDropdown = ref<number | null>(null)

// Province/City state
interface ProvinceItem {
  code: string
  name: string
}
interface CityItem {
  code: string
  name: string
}
const { loadProvinceCityData, getProvinces, getCities } = useProvinceCity()
const provinceList = ref<ProvinceItem[]>([])
const cityList = ref<CityItem[]>([])
const selectedProvince = ref('')
const selectedCity = ref('')

// Customer shipping addresses and invoice infos for dropdown
const customerShippingAddresses = ref<any[]>([])
const customerInvoiceInfos = ref<any[]>([])
const selectedShippingAddressId = ref('')
const selectedInvoiceInfoId = ref('')

// Click outside handler
const handleclickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.search-select')) {
    showCustomerDropdown.value = false
    showProductDropdown.value = null
    showWarehouseDropdown.value = null
    showHeaderWarehouseDropdown.value = false
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
    tax_number: '',
    bank_name: '',
    bank_account: ''
  },
  remark: '',
  items: [] as SalesOrderItem[]
})

// Methods
const loadCustomers = async (keyword?: string) => {
  customersLoading.value = true
  try {
    const params: any = { page_size: 50 }
    if (keyword) params.keyword = keyword
    const res = await customerApi.list(params)
    customerList.value = res.result?.items || []
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    customersLoading.value = false
  }
}

// 商品搜索
let productSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleProductSearch = (keyword: string) => {
  if (productSearchTimer) clearTimeout(productSearchTimer)
  if (!keyword || keyword.length < 1) {
    productTree.value = []
    specSearchResults.value = []
    return
  }
  productSearchTimer = setTimeout(async () => {
    try {
      const [productsRes, specsRes] = await Promise.all([
        productApi.search(keyword, 20),
        productApi.searchSpecs(keyword, 20)
      ])
      const products: Product[] = productsRes || []
      const allSpecs: SpecSearchResult[] = specsRes || []

      const tree: ProductWithSpecs[] = []
      const specIdsInTree = new Set<string>()
      for (const product of products) {
        try {
          const specsRes = await productApi.getSpecs(product.id)
          const specs: ProductSpec[] = specsRes.result?.items || []
          specs.forEach(s => specIdsInTree.add(s.id))
          tree.push({ product, specs, expanded: false })
        } catch {
          tree.push({ product, specs: [], expanded: false })
        }
      }

      specSearchResults.value = allSpecs.filter(s => !specIdsInTree.has(s.id))
      productTree.value = tree
    } catch (e) {
      console.error('搜索商品失败:', e)
      productTree.value = []
      specSearchResults.value = []
    }
  }, 300)
}

const toggleProductExpand = async (index: number) => {
  const item = productTree.value[index]
  item.expanded = !item.expanded
}

// 选择规格
const selectSpec = async (treeIndex: number, spec: ProductSpec) => {
  const treeItem = productTree.value[treeIndex]
  const product = treeItem.product
  const itemIndex = showProductDropdown.value ?? 0
  showProductDropdown.value = null
  specSearchResults.value = []

  let discount = 1
  if (orderForm.value.customer_id && product.brand_id) {
    try {
      const discountRes = await customerDiscountApi.list({
        customer_id: orderForm.value.customer_id,
        brand_id: product.brand_id,
        is_active: true
      })
      const discountItem = discountRes.result?.items?.[0]
      if (discountItem) discount = discountItem.discount_value
    } catch (e) {
      console.error('获取客户折扣失败:', e)
    }
  }

  const discountedPrice = +(spec.price * discount).toFixed(2)
  orderForm.value.items[itemIndex] = {
    ...orderForm.value.items[itemIndex],
    product_id: product.id,
    product_name: product.name,
    product_code: product.product_code || '',
    brand_name: product.brand_name || '',
    spec_id: spec.id,
    spec_code: spec.spec_code,
    price: spec.price,
    discount: discount,
    discounted_price: discountedPrice,
    amt: +(orderForm.value.items[itemIndex].qty * discountedPrice).toFixed(2)
  }
}

// 从规格搜索结果中选择
const selectSpecFromSearch = async (specResult: SpecSearchResult) => {
  const itemIndex = showProductDropdown.value ?? 0
  showProductDropdown.value = null
  specSearchResults.value = []

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
        if (discountItem) discount = discountItem.discount_value
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
    price: specResult.price,
    discount: discount,
    discounted_price: discountedPrice,
    amt: +(orderForm.value.items[itemIndex].qty * discountedPrice).toFixed(2)
  }
}

// 仓库搜索
let warehouseSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleWarehouseSearch = (keyword: string) => {
  if (warehouseSearchTimer) clearTimeout(warehouseSearchTimer)
  if (!keyword || keyword.length < 1) {
    warehouseList.value = []
    return
  }
  warehouseSearchTimer = setTimeout(async () => {
    try {
      const res = await warehouseApi.list({ keyword, page_size: 20 })
      warehouseList.value = res.result?.items || []
    } catch (e) {
      console.error('搜索仓库失败:', e)
      warehouseList.value = []
    }
  }, 300)
}

const loadSpecStock = async (specId: string) => {
  if (!specId || specStockMap.value[specId]) return
  try {
    const res = await productApi.getSpecStockDetail(specId)
    specStockMap.value[specId] = res.result?.items || []
  } catch (e) {
    console.error('加载库存失败:', e)
    specStockMap.value[specId] = []
  }
}

const getStockQty = (specId: string, warehouseId: string): number | null => {
  const stocks = specStockMap.value[specId]
  if (!stocks) return null
  const stock = stocks.find((s: any) => s.warehouse_id === warehouseId)
  return stock ? stock.quantity : 0
}

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

const applyHeaderWarehouse = () => {
  if (!headerWarehouseId.value) return
  orderForm.value.items.forEach(item => {
    if (item.product_id && item.shipping_method !== '直运') {
      item.warehouse_id = headerWarehouseId.value
      item.warehouse_name = headerWarehouseName.value
    }
  })
}

const headerWarehouseList = ref<Warehouse[]>([])
const showHeaderWarehouseDropdown = ref(false)
let headerWarehouseSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleHeaderWarehouseSearch = (keyword: string) => {
  if (headerWarehouseSearchTimer) clearTimeout(headerWarehouseSearchTimer)
  if (!keyword || keyword.length < 1) {
    headerWarehouseList.value = []
    return
  }
  headerWarehouseSearchTimer = setTimeout(async () => {
    try {
      const res = await warehouseApi.list({ keyword, page_size: 20 })
      headerWarehouseList.value = res.result?.items || []
    } catch (e) {
      headerWarehouseList.value = []
    }
  }, 300)
}
const selectHeaderWarehouse = (warehouse: Warehouse) => {
  headerWarehouseId.value = warehouse.id
  headerWarehouseName.value = warehouse.name
  showHeaderWarehouseDropdown.value = false
  applyHeaderWarehouse()
}

const filteredCustomers = computed(() => {
  return customerList.value.slice(0, 10)
})

let customerSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleCustomerSearch = () => {
  if (customerSearchTimer) clearTimeout(customerSearchTimer)
  customerSearchTimer = setTimeout(() => {
    loadCustomers(customerSearchKeyword.value || undefined)
  }, 300)
}

const selectCustomer = async (customer: any) => {
  orderForm.value.customer_id = customer.id
  orderForm.value.customer_name = customer.name
  customerSearchKeyword.value = customer.name
  showCustomerDropdown.value = false

  try {
    const res = await customerApi.getById(customer.id)
    const detail = res.result

    customerInvoiceInfos.value = detail?.invoice_infos || []
    customerShippingAddresses.value = detail?.shipping_addresses || []

    if (customerInvoiceInfos.value.length > 0) {
      const defaultInvoice = customerInvoiceInfos.value.find((i: any) => i.is_default) || customerInvoiceInfos.value[0]
      if (defaultInvoice) {
        selectedInvoiceInfoId.value = defaultInvoice.id
        orderForm.value.invoice_info = {
          invoice_title: defaultInvoice.invoice_title,
          tax_number: defaultInvoice.tax_number,
          bank_name: defaultInvoice.bank_name,
          bank_account: defaultInvoice.bank_account
        }
      }
    } else {
      selectedInvoiceInfoId.value = ''
    }

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

const onShippingAddressChange = (addressId: string) => {
  const addr = customerShippingAddresses.value.find((a: any) => a.id === addressId)
  if (addr) applyShippingAddress(addr)
}

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
    if (addr.city) {
      nextTick(() => { selectedCity.value = addr.city })
    }
  } else {
    selectedProvince.value = ''
    selectedCity.value = ''
  }
}

const onInvoiceInfoChange = (invoiceId: string) => {
  const inv = customerInvoiceInfos.value.find((i: any) => i.id === invoiceId)
  if (inv) {
    orderForm.value.invoice_info = {
      invoice_title: inv.invoice_title,
      tax_number: inv.tax_number,
      bank_name: inv.bank_name,
      bank_account: inv.bank_account
    }
  }
}

const selectWarehouse = (index: number, warehouse: Warehouse) => {
  orderForm.value.items[index].warehouse_id = warehouse.id
  orderForm.value.items[index].warehouse_name = warehouse.name
  showWarehouseDropdown.value = null
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
  orderForm.value.items.forEach((item, i) => { item.row_no = i + 1 })
}

const updateItemAmount = (index: number) => {
  const item = orderForm.value.items[index]
  item.discounted_price = item.price * item.discount
  item.amt = item.qty * item.discounted_price
}

const totalAmount = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + item.amt, 0)
})

const totalDiscountAmount = computed(() => {
  return orderForm.value.items.reduce((sum, item) => sum + (item.price - item.discounted_price) * item.qty, 0)
})

const formatAmount = (val: number) => {
  return val.toFixed(2)
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

  formLoading.value = true
  try {
    const data = {
      order_date: orderForm.value.order_date,
      customer_id: orderForm.value.customer_id,
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
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        warehouse_id: item.warehouse_id || '',
        shipping_method: item.shipping_method
      }))
    }
    await salesOrderApi.create(data)
    window.showToast('订单创建成功', 'success')
    emit('back')
  } catch (error: any) {
    window.showToast(error.message || '保存失败', 'error')
  } finally {
    formLoading.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', handleclickOutside)
  try {
    await loadProvinceCityData()
    provinceList.value = getProvinces()
  } catch (e) {
    console.error('加载省份失败:', e)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleclickOutside)
})
</script>

<template>
  <div class="sales-order-create">
    <div class="page-header">
      <button class="back-btn" @click="emit('back')">
        <span class="back-icon">←</span> 返回销售订单
      </button>
      <h2>新建销售订单</h2>
      <div class="header-actions">
        <button class="btn-secondary" @click="emit('back')">取消</button>
        <button class="btn-primary" @click="handleSaveOrder" :disabled="formLoading">
          {{ formLoading ? '保存中...' : '保存订单' }}
        </button>
      </div>
    </div>

    <div class="form-content">
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
                @click="if(orderForm.customer_id) { orderForm.customer_id = ''; orderForm.customer_name = '' }"
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
            <select v-model="selectedShippingAddressId" @change="onShippingAddressChange(selectedShippingAddressId)" :disabled="!orderForm.customer_id">
              <option value="">请选择收货地址</option>
              <option v-for="addr in customerShippingAddresses" :key="addr.id" :value="addr.id">
                {{ addr.recipient_name }} - {{ addr.recipient_phone }} - {{ addr.province || '' }} {{ addr.city || '' }} {{ addr.address }}{{ addr.is_default ? ' (默认)' : '' }}
              </option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>选择开票信息</label>
            <select v-model="selectedInvoiceInfoId" @change="onInvoiceInfoChange(selectedInvoiceInfoId)" :disabled="!orderForm.customer_id">
              <option value="">请选择开票信息</option>
              <option v-for="inv in customerInvoiceInfos" :key="inv.id" :value="inv.id">
                {{ inv.invoice_title }}{{ inv.is_default ? ' (默认)' : '' }}
              </option>
            </select>
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
                <th style="width: 250px">商品</th>
                <th style="width: 100px">规格</th>
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
                    <div class="search-select header-search-select">
                      <input
                        type="text"
                        :value="headerWarehouseName"
                        @click="if(headerWarehouseId) { headerWarehouseId = ''; headerWarehouseName = '' }"
                        @focus="showHeaderWarehouseDropdown = true; headerWarehouseList = []"
                        @input="handleHeaderWarehouseSearch(($event.target as HTMLInputElement).value)"
                        placeholder="批量设置"
                      />
                      <div class="search-dropdown" v-if="showHeaderWarehouseDropdown">
                        <div
                          v-for="w in headerWarehouseList"
                          :key="w.id"
                          class="search-option"
                          @click="selectHeaderWarehouse(w)"
                        >
                          {{ w.name }}
                        </div>
                        <div v-if="headerWarehouseList.length === 0" class="search-option disabled">输入关键字搜索仓库</div>
                      </div>
                    </div>
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
                      :value="item.product_name ? (item.brand_name ? '[' + item.brand_name + '] ' + item.product_name : item.product_name) : ''"
                      @click="if(item.product_id) { item.product_id = ''; item.product_name = ''; item.product_code = ''; item.brand_name = ''; item.spec_id = ''; item.spec_code = '' }"
                      @focus="showProductDropdown = index; productTree = []"
                      @input="handleProductSearch(($event.target as HTMLInputElement).value)"
                      placeholder="输入商品名称/编码/规格编号搜索"
                    />
                    <div class="search-dropdown product-tree-dropdown" v-if="showProductDropdown === index">
                      <template v-for="(treeItem, treeIdx) in productTree" :key="treeItem.product.id">
                        <div class="search-option product-tree-item" @click.stop="toggleProductExpand(treeIdx)">
                          <span class="expand-icon" :class="{ expanded: treeItem.expanded }">▶</span>
                          <span class="brand-name" v-if="treeItem.product.brand_name">[{{ treeItem.product.brand_name }}]</span>
                          <span class="product-name">{{ treeItem.product.name }}</span>
                          <span class="product-code">({{ treeItem.product.product_code || '无编码' }})</span>
                          <span class="spec-count" v-if="treeItem.specs.length > 0">{{ treeItem.specs.length }}个规格</span>
                        </div>
                        <div class="spec-list" v-if="treeItem.expanded">
                          <div
                            v-for="spec in treeItem.specs"
                            :key="spec.id"
                            class="search-option spec-item"
                            :class="{ 'inactive': !spec.is_active }"
                            @click="selectSpec(treeIdx, spec)"
                          >
                            <span class="spec-code">{{ spec.spec_code }}</span>
                            <span class="spec-info" v-if="spec.packaging">{{ spec.packaging }}</span>
                            <span class="spec-price">¥{{ spec.price.toFixed(2) }}</span>
                            <span class="spec-status" v-if="!spec.is_active">停用</span>
                          </div>
                          <div v-if="treeItem.specs.length === 0" class="search-option disabled">暂无规格</div>
                        </div>
                      </template>
                      <template v-if="specSearchResults.length > 0">
                        <div class="search-option disabled spec-search-header">— 规格编号匹配 —</div>
                        <div
                          v-for="specResult in specSearchResults"
                          :key="specResult.id"
                          class="search-option spec-search-item"
                          :class="{ 'inactive': !specResult.is_active }"
                          @click="selectSpecFromSearch(specResult)"
                        >
                          <span class="spec-code">{{ specResult.spec_code }}</span>
                          <span class="spec-info" v-if="specResult.packaging">{{ specResult.packaging }}</span>
                          <span class="brand-name" v-if="specResult.brand_name">[{{ specResult.brand_name }}]</span>
                          <span class="product-name-small">{{ specResult.product_name }}</span>
                          <span class="spec-price">¥{{ specResult.price.toFixed(2) }}</span>
                          <span class="spec-status" v-if="!specResult.is_active">停用</span>
                        </div>
                      </template>
                      <div v-if="productTree.length === 0 && specSearchResults.length === 0" class="search-option disabled">输入关键字搜索商品或规格编号</div>
                    </div>
                  </div>
                </td>
                <td>{{ item.spec_code || '-' }}</td>
                <td><input type="number" v-model="item.qty" min="1" @input="updateItemAmount(index)" /></td>
                <td><input type="number" v-model="item.price" min="0" step="0.01" @input="updateItemAmount(index)" /></td>
                <td><input type="number" v-model="item.discount" min="0" max="1" step="0.01" @input="updateItemAmount(index)" /></td>
                <td>{{ formatAmount(item.discounted_price) }}</td>
                <td>{{ formatAmount(item.amt) }}</td>
                <td>
                  <select v-model="item.shipping_method" @change="if(item.shipping_method === '直运') { item.warehouse_id = ''; item.warehouse_name = '' }">
                    <option v-for="s in shippingMethodOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </td>
                <td v-if="item.shipping_method !== '直运'">
                  <div class="search-select">
                    <input
                      type="text"
                      :value="item.warehouse_name || ''"
                      @click="if(item.warehouse_id) { item.warehouse_id = ''; item.warehouse_name = '' }"
                      @focus="showWarehouseDropdown = index; warehouseList = []; loadSpecStock(item.spec_id)"
                      @input="handleWarehouseSearch(($event.target as HTMLInputElement).value)"
                      placeholder="输入仓库名称搜索"
                    />
                    <div class="search-dropdown" v-if="showWarehouseDropdown === index">
                      <div
                        v-for="w in warehouseList"
                        :key="w.id"
                        class="search-option warehouse-option"
                        @click="selectWarehouse(index, w)"
                      >
                        <span class="warehouse-name">{{ w.name }}</span>
                        <span class="warehouse-stock" v-if="item.spec_id">
                          库存: {{ getStockQty(item.spec_id, w.id) !== null ? getStockQty(item.spec_id, w.id) : '加载中...' }}
                        </span>
                      </div>
                      <div v-if="warehouseList.length === 0" class="search-option disabled">输入关键字搜索仓库</div>
                    </div>
                  </div>
                </td>
                <td v-else></td>
                <td><button class="btn-link danger" @click="removeOrderItem(index)">删除</button></td>
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
  </div>
</template>

<style scoped>
.sales-order-create {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 16px;
}

.page-header h2 {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.back-btn:hover {
  background: var(--bg-secondary);
}

.back-icon {
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-primary {
  padding: 8px 24px;
  background: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 8px 24px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.form-content {
  flex: 1;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group input[readonly] {
  background: var(--bg-secondary);
  color: var(--text-muted);
}

.date-input {
  width: 100%;
}

/* Search select */
.search-select {
  position: relative;
}

.search-select input {
  width: 100%;
  box-sizing: border-box;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 300px;
  overflow-y: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0 0 6px 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 100;
}

.search-option {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-option:hover {
  background: var(--bg-secondary);
}

.search-option.disabled {
  color: var(--text-muted);
  cursor: default;
}

.search-option.disabled:hover {
  background: transparent;
}

/* Product tree */
.product-tree-dropdown {
  max-height: 350px;
}

.product-tree-item {
  font-weight: 500;
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

/* Warehouse */
.warehouse-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.warehouse-name {
  flex: 1;
}

.warehouse-stock {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 8px;
  white-space: nowrap;
}

/* Header bulk setting */
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

.header-search-select {
  width: 100%;
}

.header-search-select input {
  font-size: 12px;
  padding: 2px 4px;
  text-align: center;
}

/* Items table */
.items-table {
  overflow-x: auto;
}

.items-table table {
  width: 100%;
  border-collapse: collapse;
}

.items-table th,
.items-table td {
  padding: 8px;
  border: 1px solid var(--border-color);
  text-align: left;
  font-size: 13px;
}

.items-table th {
  background: var(--bg-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.items-table input[type="number"] {
  text-align: right;
  width: 100%;
  box-sizing: border-box;
  padding: 4px 6px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.items-table select {
  width: 100%;
  padding: 4px 6px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
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
  transition: all 0.2s;
}

.add-item-btn:hover {
  background-color: var(--bg-secondary);
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-blue);
  cursor: pointer;
  font-size: 13px;
  padding: 2px 8px;
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link:hover {
  text-decoration: underline;
}

/* Amount summary */
.amount-summary {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.summary-row.total {
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
  padding-top: 8px;
  font-weight: 600;
  font-size: 16px;
}
</style>
