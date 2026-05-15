const getApiBaseUrl = () => {
  return `${window.location.protocol}//${window.location.host}/api/v1`
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getApiBaseUrl()

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: any
  params?: Record<string, any>
  skipAuth?: boolean
}

class ApiService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private clearAuthData() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('token_expires_at')
  }

  private handleAuthError() {
    this.clearAuthData()
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, params, skipAuth = false } = options

    let url = `${this.baseUrl}${endpoint}`

    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => searchParams.append(key, String(v)))
          } else {
            searchParams.append(key, String(value))
          }
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        url += `?${queryString}`
      }
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }

    if (!skipAuth) {
      const token = localStorage.getItem('token')
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }

    const config: RequestInit = {
      method,
      headers
    }

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(url, config)

    if (response.status === 401 || response.status === 403) {
      this.handleAuthError()
      const errorData = await response.json().catch(() => ({ detail: '登录已过期，请重新登录' }))
      throw new Error(errorData.detail || '登录已过期，请重新登录')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }))
      if (response.status === 422 && Array.isArray(error.detail)) {
        const messages = error.detail.map((err: any) => {
          const field = err.loc?.slice(1).join('.') || err.loc?.pop() || '字段'
          return `${field}: ${err.msg}`
        })
        throw new Error(messages.join('; '))
      }
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    if (data.status === 'error') {
      if (data.validation_errors) {
        let messages: string
        if (Array.isArray(data.validation_errors)) {
          messages = data.validation_errors.map((err: any) => `${err.field || '字段'}: ${err.message}`).join('; ')
        } else {
          messages = Object.entries(data.validation_errors as Record<string, string[]>)
            .map(([field, errors]) => `${field}: ${(errors as string[]).join(', ')}`)
            .join('; ')
        }
        throw new Error(`${data.message || '操作失败'} - ${messages}`)
      }
      throw new Error(data.message || '操作失败')
    }

    if (data.result !== undefined) {
      return data.result
    }
    return data
  }

  get<T>(endpoint: string, params?: Record<string, any>, skipAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', params, skipAuth })
  }

  post<T>(endpoint: string, body?: any, skipAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body, skipAuth })
  }

  put<T>(endpoint: string, body?: any, skipAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body, skipAuth })
  }

  delete<T>(endpoint: string, skipAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE', skipAuth })
  }

  patch<T>(endpoint: string, body?: any, skipAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'PATCH', body, skipAuth })
  }

  async uploadFile<T>(endpoint: string, file: File | Blob, fileName: string): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const formData = new FormData()
    formData.append('file', file, fileName)

    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    })

    if (response.status === 401 || response.status === 403) {
      this.handleAuthError()
      throw new Error('登录已过期，请重新登录')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '上传失败' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }
}

export const apiService = new ApiService(API_BASE_URL)

export const authApi = {
  login: (credentials: { username: string; password: string }) => {
    return apiService.post<any>('/auth/login', credentials, true)
  },

  register: (userData: any) => {
    return apiService.post<any>('/auth/register', userData, true)
  },

  getMe: () => {
    return apiService.get<any>('/auth/me')
  },

  changePassword: (data: { old_password: string; new_password: string }) => {
    return apiService.put<any>('/auth/me/password', data)
  },

  listUsers: (params: { page?: number; page_size?: number; status?: string; keyword?: string }) => {
    return apiService.get<any>('/auth/users/', params)
  },

  getUser: (id: string) => {
    return apiService.get<any>(`/auth/users/${id}/`)
  },

  createUser: (data: any) => {
    return apiService.post<any>('/auth/users/', data)
  },

  updateUser: (id: string, data: any) => {
    return apiService.put<any>(`/auth/users/${id}/`, data)
  },

  deleteUser: (id: string) => {
    return apiService.delete<any>(`/auth/users/${id}/`)
  },

  resetPassword: (id: string, newPassword: string) => {
    return apiService.patch<any>(`/auth/users/${id}/password`, { new_password: newPassword })
  },

  updateUserStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/auth/users/${id}/status`, { status })
  }
}

export const roleApi = {
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string }) => {
    return apiService.get<any>('/auth/roles/', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/auth/roles/${id}/`)
  },

  create: (data: any) => {
    return apiService.post<any>('/auth/roles/', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/auth/roles/${id}/`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/auth/roles/${id}/`)
  },

  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/auth/roles/${id}/status`, { status })
  }
}

export const permissionApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string }) => {
    return apiService.get<any>('/auth/permissions/', params)
  },

  getTree: () => {
    return apiService.get<any>('/auth/permissions/tree')
  },

  getById: (id: string) => {
    return apiService.get<any>(`/auth/permissions/${id}/`)
  }
}

export const salesOrderApi = {
  // 获取订单列表
  list: (params: { page?: number; page_size?: number; status?: string; customer_id?: string | number; order_no?: string; keyword?: string }) => {
    return apiService.get<any>('/sales-orders/', params)
  },

  // 获取订单详情
  getByOrderNo: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}`)
  },

  // 创建订单
  create: (data: {
    order_date: string
    customer_id: string | number
    customer_name?: string
    sale_user_id?: string | number
    deliver_info?: {
      addr: string
      province: string
      city: string
      person_name: string
      person_tel: string
    }
    expect_deliver_date?: string
    settle_type?: string
    tax_rate?: number
    remark?: string
    items: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.post<any>('/sales-orders/', data)
  },

  // 创建并提交订单（直接审核通过）
  createAndSubmit: (data: {
    order_date: string
    customer_id: string | number
    customer_name?: string
    sale_user_id?: string | number
    deliver_info?: {
      addr: string
      province: string
      city: string
      person_name: string
      person_tel: string
    }
    expect_deliver_date?: string
    settle_type?: string
    tax_rate?: number
    remark?: string
    items: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.post<any>('/sales-orders/create-and-submit', data)
  },

  // 更新订单
  update: (orderNo: string, data: {
    order_date?: string
    customer_id?: string | number
    customer_name?: string
    expect_deliver_date?: string
    settle_type?: string
    remark?: string
    items?: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.put<any>(`/sales-orders/${orderNo}`, data)
  },

  // 删除订单
  delete: (orderNo: string) => {
    return apiService.delete<any>(`/sales-orders/${orderNo}`)
  },

  // 提交审核（draft → pending）
  submit: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/submit`)
  },

  // 审核通过（pending → audited）
  approve: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/approve`)
  },

  // 驳回（pending → draft）
  reject: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/reject`)
  },

  // 取消订单
  cancel: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/cancel`)
  },

  // 获取订单状态流转记录
  getStatusFlows: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}/status-flows`)
  },

  // 下推采购
  pushToPurchase: (orderNo: string, items: { row_no: number }[]) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/push-to-purchase`, { items })
  }
}

export const purchaseOrderApi = {
  // 获取采购单列表
  list: (params: { page?: number; page_size?: number; status?: string; purchase_type?: string; brand_id?: string; supplier_id?: string; purchase_no?: string; source_sale_order_no?: string }) => {
    return apiService.get<any>('/purchase-orders/', params)
  },

  // 快速搜索采购单
  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/purchase-orders/search', { keyword, limit })
  },

  // 获取采购单详情
  getByPurchaseNo: (purchaseNo: string) => {
    return apiService.get<any>(`/purchase-orders/${purchaseNo}`)
  },

  // 创建采购单
  create: (data: {
    purchase_type: string
    source_sale_order_no?: string
    source_sale_order_id?: string
    brand_id?: string
    supplier_id: string
    purchase_user_id?: string
    receive_info?: {
      type?: string
      warehouse_id?: string
      customer_addr?: string
      province?: string
      city?: string
      contact_person?: string
      contact_tel?: string
    }
    expect_arrive_date?: string
    settle_type: string
    remark?: string
    items: Array<{
      row_no: number
      product_id: string
      spec_id?: string
      brand_id?: string
      purchase_qty: number
      purchase_price: number
      discount?: number
      shipping_method?: string
      source_sale_row_no?: number
      warehouse_id?: string
    }>
  }) => {
    return apiService.post<any>('/purchase-orders/', data)
  },

  // 更新采购单
  update: (purchaseNo: string, data: {
    purchase_type?: string
    brand_id?: string
    supplier_id?: string
    purchase_user_id?: string
    receive_info?: {
      type?: string
      warehouse_id?: string
      customer_addr?: string
      province?: string
      city?: string
      contact_person?: string
      contact_tel?: string
    }
    expect_arrive_date?: string
    settle_type?: string
    freight_amt?: number
    remark?: string
    items?: Array<{
      row_no: number
      product_id: string
      spec_id?: string
      brand_id?: string
      purchase_qty: number
      purchase_price: number
      discount?: number
      shipping_method?: string
      source_sale_row_no?: number
      warehouse_id?: string
    }>
  }) => {
    return apiService.put<any>(`/purchase-orders/${purchaseNo}`, data)
  },

  // 删除采购单
  delete: (purchaseNo: string) => {
    return apiService.delete<any>(`/purchase-orders/${purchaseNo}`)
  },

  // 更新采购状态
  updatePurchaseStatus: (purchaseNo: string, status: string) => {
    return apiService.patch<any>(`/purchase-orders/${purchaseNo}/purchase-status`, { status })
  },

  // 更新入库状态
  updateInStatus: (purchaseNo: string, in_status: string) => {
    return apiService.patch<any>(`/purchase-orders/${purchaseNo}/in-status`, { in_status })
  },

  // 更新付款状态
  updatePayStatus: (purchaseNo: string, pay_status: string) => {
    return apiService.patch<any>(`/purchase-orders/${purchaseNo}/pay-status`, { pay_status })
  },

  // 审核采购单
  approve: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/approve`, {})
  },

  // 撤回采购单（删除采购单，更新销售单）
  recall: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/recall`, {})
  },

  // 结案采购单
  close: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/close`, {})
  },

  // 重审采购单（撤回到草稿）
  reaudit: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/reaudit`, {})
  },

  // 作废采购单
  void: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/void`, {})
  },

  // 获取状态流转记录
  getStatusFlows: (purchaseNo: string) => {
    return apiService.get<any>(`/purchase-orders/${purchaseNo}/status-flows`)
  }
}

export const receivableApi = {
  list: (params: { page?: number; page_size?: number; status?: string; customer_id?: string; keyword?: string; sales_order_no?: string }) => {
    return apiService.get<any>('/accounts-receivable/', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/accounts-receivable/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/accounts-receivable/', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/accounts-receivable/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/accounts-receivable/${id}`)
  },

  recordPayment: (id: string, data: { amount: number; payment_method?: string; remarks?: string }) => {
    return apiService.post<any>(`/accounts-receivable/${id}/record-payment`, data)
  },

  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/accounts-receivable/${id}/status`, { status })
  }
}

// customers API (客户管理)
export interface InvoiceInfo {
  id?: string
  invoice_title: string
  invoice_type: string
  tax_number: string
  bank_name: string
  bank_account: string
  is_default?: boolean
  created_at?: string
  updated_at?: string
}

export interface ShippingAddressV2 {
  id?: string
  recipient_name: string
  recipient_phone: string
  province?: string
  province_code?: string
  city?: string
  city_code?: string
  district?: string
  address: string
  is_default?: boolean
  created_at?: string
  updated_at?: string
}

export interface Customer {
  id: string
  customer_code: string
  name: string
  customer_type: 'terminal' | 'dealer'
  research_group?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  invoice_infos: InvoiceInfo[]
  shipping_addresses: ShippingAddressV2[]
  sales_user_id?: string
  sales_user_name?: string
  status: string
  created_at?: string
  updated_at?: string
}

export interface CustomerListItem {
  id: string
  customer_code: string
  name: string
  customer_type: 'terminal' | 'dealer'
  research_group?: string
  contact_person?: string
  contact_phone?: string
  sales_user_name?: string
  status: string
  created_at?: string
  updated_at?: string
}

export const customerApi = {
  // 获取客户列表
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string; customer_type?: string; sales_user_id?: string }) => {
    return apiService.get<any>('/customers/', params)
  },

  // 获取客户详情
  getById: (id: string) => {
    return apiService.get<any>(`/customers/${id}`)
  },

  // 创建客户
  create: (data: any) => {
    return apiService.post<any>('/customers/', data)
  },

  // 更新客户
  update: (id: string, data: any) => {
    return apiService.put<any>(`/customers/${id}`, data)
  },

  // 删除客户
  delete: (id: string) => {
    return apiService.delete<any>(`/customers/${id}`)
  },

  // 获取客户统计
  getStats: () => {
    return apiService.get<any>('/customers/stats')
  },

  // 搜索客户
  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/customers/search', { keyword, limit })
  },

  // 更新客户状态
  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/customers/${id}/status`, { status })
  },

  // 转移客户
  transfer: (customerId: string, newUserId: string) => {
    return apiService.patch<any>(`/customers/${customerId}/transfer`, { new_user_id: newUserId })
  },

  // AI 创建客户（从文本或图片提取信息）
  createFromAi: (data: { input?: string; file_path?: string }) => {
    return apiService.post<any>('/customers/create_customer_from_ai', data)
  },

  // 以下为保持向后兼容的方法（供SalesOrder等模块使用）
  // 添加收货地址 - 通过更新客户实现
  addShippingAddress: async (customerId: string, address: ShippingAddressV2) => {
    const detailRes = await apiService.get<any>(`/customers/${customerId}`)
    const customer = detailRes.result
    if (!customer) throw new Error('客户不存在')

    const shippingAddresses = [...(customer.shipping_addresses || []), { ...address, id: undefined }]
    await apiService.put<any>(`/customers/${customerId}`, {
      shipping_addresses: shippingAddresses
    })
    return { result: shippingAddresses[shippingAddresses.length - 1] }
  },

  // 添加开票信息 - 通过更新客户实现
  addInvoiceInfo: async (customerId: string, invoice: InvoiceInfo) => {
    const detailRes = await apiService.get<any>(`/customers/${customerId}`)
    const customer = detailRes.result
    if (!customer) throw new Error('客户不存在')

    const invoiceInfos = [...(customer.invoice_infos || []), { ...invoice, id: undefined }]
    await apiService.put<any>(`/customers/${customerId}`, {
      invoice_infos: invoiceInfos
    })
    return { result: invoiceInfos[invoiceInfos.length - 1] }
  },
}

export interface ProvinceInfo {
  code: string
  name: string
  cities: string[]
}

export interface CityInfo {
  code: string
  name: string
  province_code: string
}

export interface DistrictInfo {
  name: string
  province_code: string
  city: string
}

export interface SearchLocationItem {
  type: 'province' | 'city' | 'district'
  name: string
  province?: string
  city?: string
  code?: string
}

export interface ProvinceCityData {
  [provinceName: string]: {
    code: string
    cities: {
      [cityName: string]: {
        code: string
        districts: string[]
      }
    }
  }
}

export interface ProvinceCityInfo {
  code: string
  name: string
}

export interface CityDistrictInfo {
  code: string
  name: string
  districts: string[]
}

export const provinceApi = {
  // 获取所有省份城市数据（合并接口）
  getAll: () => {
    return apiService.get<ProvinceCityData>('/province-city/')
  }
}

export interface ProductSpec {
  id: string
  product_id: string
  spec_code: string
  packaging?: string
  sales_spec?: string
  price: number
  cas_number?: string
  is_active: boolean
  stock_quantity?: number
  stock_status?: Array<{
    warehouse_id: string
    warehouse_name: string
    quantity: number
  }>
  created_at?: string
  updated_at?: string
}

export interface Product {
  id: string
  product_code: string
  name: string
  image_url?: string
  brand_id?: string
  brand_name?: string
  category_id?: string
  category_name?: string
  tax_code?: string
  is_active?: boolean
  specs: ProductSpec[]
  created_at?: string
  updated_at?: string
}

export interface ProductFormData {
  product_code?: string
  name: string
  image_url?: string
  brand_id?: string
  category_id?: string
  tax_code?: string
  is_active?: boolean
  specs?: ProductSpecFormData[]
}

export interface ProductSpecFormData {
  id?: string
  spec_code?: string
  packaging?: string
  sales_spec?: string
  price: number
  cas_number?: string
  is_active?: boolean
}

export interface CategoryTreeNode {
  id: string
  name: string
  parent_id: string | null
  tax_code?: string
  sort_order: number
  is_shop_display: boolean
  level: number
  children?: CategoryTreeNode[]
}

export interface Category {
  id: string
  name: string
  parent_id: string | null
  tax_code?: string
  sort_order: number
  is_shop_display: boolean
  level: number
  created_at?: string
  updated_at?: string
}

export interface CategoryFormData {
  name: string
  parent_id?: string | null
  tax_code?: string
  sort_order?: number
  is_shop_display?: boolean
}

export const categoryApi = {
  list: () => {
    return apiService.get<any>('/categories/')
  },

  getById: (id: string) => {
    return apiService.get<any>(`/categories/${id}`)
  },

  create: (data: CategoryFormData) => {
    return apiService.post<any>('/categories/', data)
  },

  update: (id: string, data: Partial<CategoryFormData>) => {
    return apiService.put<any>(`/categories/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/categories/${id}`)
  }
}

export const productApi = {
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string; brand_id?: string; category_id?: string }) => {
    return apiService.get<any>('/products/', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/products/${id}`)
  },

  create: (data: ProductFormData) => {
    return apiService.post<any>('/products/', data)
  },

  update: (id: string, data: Partial<ProductFormData>) => {
    return apiService.put<any>(`/products/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/products/${id}`)
  },

  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/products/search', { keyword, limit })
  },

  getStats: () => {
    return apiService.get<any>('/products/stats')
  },

  getSpecs: (productId: string, params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>(`/products/${productId}/specs`, params)
  },

  createSpec: (productId: string, data: ProductSpecFormData) => {
    return apiService.post<any>(`/products/${productId}/specs`, data)
  },

  updateSpec: (specId: string, data: Partial<ProductSpecFormData>) => {
    return apiService.put<any>(`/products/specs/${specId}`, data)
  },

  deleteSpec: (specId: string) => {
    return apiService.delete<any>(`/products/specs/${specId}`)
  },

  toggleSpecActive: (specId: string, isActive: boolean) => {
    return apiService.patch<any>(`/products/specs/${specId}/toggle-active?is_active=${isActive}`)
  },

  getSpecStockDetail: (specId: string) => {
    return apiService.get<any>(`/products/specs/${specId}/stock-detail`)
  },

  getAllSpecs: (params?: { page?: number; page_size?: number; keyword?: string; category?: string }) => {
    return apiService.get<any>('/products/all-specs/', params)
  },

  searchSpecs: (keyword: string, limit?: number) => {
    return apiService.get<any>('/products/specs/search', { keyword, limit })
  }
}

export interface Brand {
  id: string
  name: string
  logo_url?: string
  description?: string
  purchaser_id?: string
  purchaser_name?: string
  is_active: boolean
  product_count?: number
  created_at?: string
  updated_at?: string
}

export interface BrandFormData {
  name: string
  logo_url?: string
  description?: string
  purchaser_id?: string
  is_active?: boolean
}

export const brandApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string; is_active?: boolean }) => {
    return apiService.get<any>('/brands/', params)
  },

  getAll: (params?: { is_active?: boolean }) => {
    return apiService.get<any>('/brands/all', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/brands/${id}`)
  },

  create: (data: BrandFormData) => {
    return apiService.post<any>('/brands/', data)
  },

  update: (id: string, data: Partial<BrandFormData>) => {
    return apiService.put<any>(`/brands/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/brands/${id}`)
  },

  toggleActive: (id: string, isActive: boolean) => {
    return apiService.patch<any>(`/brands/${id}/toggle-active?is_active=${isActive}`)
  },

  getPurchaserCandidates: (keyword?: string) => {
    return apiService.get<any>('/brands/purchaser-candidates', keyword ? { keyword } : {})
  },

  batchGetPurchasers: (brandIds: string[]) => {
    return apiService.post<any>('/brands/batch-purchasers', brandIds)
  },

  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/brands/search', { keyword, limit })
  }
}

export const supplierApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string; is_active?: boolean; brand_ids?: string[] }) => {
    return apiService.get<any>('/suppliers/', params)
  },

  getAll: (params?: { is_active?: boolean }) => {
    return apiService.get<any>('/suppliers/all', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/suppliers/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/suppliers/', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/suppliers/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/suppliers/${id}`)
  },

  toggleActive: (id: string, isActive: boolean) => {
    return apiService.patch<any>(`/suppliers/${id}/toggle-active?is_active=${isActive}`)
  },

  getByBrandId: (brandId: string) => {
    return apiService.get<any>(`/suppliers/by-brand/${brandId}`)
  }
}

export const customerDiscountApi = {
  // 获取客户折扣列表
  list: (params: { page?: number; page_size?: number; customer_id?: string; brand_id?: string; is_active?: boolean }) => {
    return apiService.get<any>('/customer-discounts/', params)
  },

  // 获取客户折扣详情
  getById: (id: string) => {
    return apiService.get<any>(`/customer-discounts/${id}`)
  },

  // 创建客户折扣
  create: (data: { customer_id: string; brand_id: string; discount_value: number; is_active?: boolean }) => {
    return apiService.post<any>('/customer-discounts/', data)
  },

  // 更新客户折扣
  update: (id: string, data: { discount_value?: number; is_active?: boolean }) => {
    return apiService.put<any>(`/customer-discounts/${id}`, data)
  },

  // 删除客户折扣
  delete: (id: string) => {
    return apiService.delete<any>(`/customer-discounts/${id}`)
  },

  // 切换客户折扣状态
  toggleStatus: (id: string, isActive: boolean) => {
    return apiService.patch<any>(`/customer-discounts/${id}/status?is_active=${isActive}`)
  },

  // 获取指定客户和品牌的折扣
  getByCustomerAndBrand: (customerId: string, brandId: string) => {
    return apiService.get<any>(`/customer-discounts/customer/${customerId}/brand/${brandId}`)
  }
}

export const llmApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>('/llm/models', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/llm/models/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/llm/models', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/llm/models/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/llm/models/${id}`)
  },
  getConfig: () => {
    return apiService.get<any>('/llm/config')
  },
  updateConfig: (data: any) => {
    return apiService.put<any>('/llm/config', data)
  },
  testConnection: (id: string) => {
    return apiService.post<any>(`/llm/models/${id}/test`)
  }
}

export const knowledgeBaseApi = {
  list: (params?: { page?: number; page_size?: number; kb_type?: string }) => {
    return apiService.get<any>('/knowledge-base/collections', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/knowledge-base/collections/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/knowledge-base/collections', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/knowledge-base/collections/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/knowledge-base/collections/${id}`)
  },
  getDocuments: (collectionId: string, params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>(`/knowledge-base/collections/${collectionId}/documents`, params)
  },
  addDocument: (collectionId: string, data: any) => {
    return apiService.post<any>(`/knowledge-base/collections/${collectionId}/documents`, data)
  },
  deleteDocument: (collectionId: string, docId: string) => {
    return apiService.delete<any>(`/knowledge-base/collections/${collectionId}/documents/${docId}`)
  },
  rebuildIndex: (collectionId: string) => {
    return apiService.post<any>(`/knowledge-base/collections/${collectionId}/rebuild`)
  }
}

export const mcpApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) => {
    return apiService.get<any>('/mcp/servers', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/mcp/servers/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/mcp/servers', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/mcp/servers/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/mcp/servers/${id}`)
  },
  getTools: (serverId: string) => {
    return apiService.get<any>(`/mcp/servers/${serverId}/tools`)
  },
  testConnection: (serverId: string) => {
    return apiService.post<any>(`/mcp/servers/${serverId}/test`)
  }
}

export const skillApi = {
  list: (params?: { page?: number; page_size?: number; category?: string }) => {
    return apiService.get<any>('/skills', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/skills/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/skills', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/skills/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/skills/${id}`)
  },
  enable: (id: string) => {
    return apiService.patch<any>(`/skills/${id}/enable`)
  },
  disable: (id: string) => {
    return apiService.patch<any>(`/skills/${id}/disable`)
  }
}

export const agentApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>('/agents', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/agents/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/agents', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/agents/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/agents/${id}`)
  }
}

export const aiToolsApi = {
  listTools: () => {
    return apiService.get<any>('/ai/tools')
  }
}

export const warehouseApi = {
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string }) => {
    return apiService.get<any>('/warehouses/', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/warehouses/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/warehouses/', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/warehouses/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/warehouses/${id}`)
  },
  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/warehouses/${id}/status`, { status })
  },
  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/warehouses/search', { keyword, limit })
  },
  getManagerCandidates: (keyword?: string) => {
    return apiService.get<any>('/warehouses/manager-candidates', { keyword })
  }
}

export const stockApi = {
  list: (params: { page?: number; page_size?: number; warehouse_id?: string; product_id?: string; spec_id?: string; status?: string; keyword?: string }) => {
    return apiService.get<any>('/stocks/', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/stocks/${id}`)
  },
  getDetail: (id: string) => {
    return apiService.get<any>(`/stocks/${id}/detail`)
  },
  create: (data: any) => {
    return apiService.post<any>('/stocks/', data)
  },
  update: (id: string, data: any) => {
    return apiService.put<any>(`/stocks/${id}`, data)
  },
  delete: (id: string) => {
    return apiService.delete<any>(`/stocks/${id}`)
  },
  inbound: (id: string, quantity: number, remarks?: string) => {
    const params = new URLSearchParams({
      quantity: String(quantity)
    })
    if (remarks) {
      params.append('remarks', remarks)
    }
    return apiService.post<any>(`/stocks/${id}/inbound?${params.toString()}`, null)
  },
  outbound: (id: string, quantity: number, remarks?: string) => {
    const params = new URLSearchParams({
      quantity: String(quantity)
    })
    if (remarks) {
      params.append('remarks', remarks)
    }
    return apiService.post<any>(`/stocks/${id}/outbound?${params.toString()}`, null)
  },
  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/stocks/search', { keyword, limit })
  },
  getStats: () => {
    return apiService.get<any>('/stocks/stats')
  },
  getInboundBatches: (stockId: string, params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>(`/inbound-batches/by-stock/${stockId}`, params)
  },
  getOutboundBatches: (stockId: string, params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>(`/outbound-batches/by-stock/${stockId}`, params)
  }
}

export interface InboundBatch {
  id: string
  warehouse_id: string
  product_id: string
  product_code: string
  product_name: string
  spec_id: string
  spec_code: string
  stock_id: string
  quantity: number
  user_id: string
  user_name: string
  created_at: string
  updated_at: string
}

export interface OutboundBatch {
  id: string
  warehouse_id: string
  product_id: string
  product_code: string
  product_name: string
  spec_id: string
  spec_code: string
  stock_id: string
  quantity: number
  user_id: string
  user_name: string
  created_at: string
  updated_at: string
}

export const inboundBatchApi = {
  list: (params: { page?: number; page_size?: number; stock_id?: string }) => {
    return apiService.get<any>('/inbound-batches/', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/inbound-batches/${id}`)
  },
  create: (data: {
    warehouse_id: string
    product_id: string
    product_code: string
    product_name: string
    spec_id: string
    spec_code: string
    stock_id?: string
    quantity: number
    user_id: string
    user_name: string
  }) => {
    return apiService.post<any>('/inbound-batches/', data)
  },
  update: (id: string, data: Partial<{
    warehouse_id: string
    product_id: string
    product_code: string
    product_name: string
    spec_id: string
    spec_code: string
    stock_id: string
    quantity: number
    user_id: string
    user_name: string
  }>) => {
    return apiService.put<any>(`/inbound-batches/${id}`, data)
  }
}

export const outboundBatchApi = {
  list: (params: { page?: number; page_size?: number; stock_id?: string }) => {
    return apiService.get<any>('/outbound-batches/', params)
  },
  getById: (id: string) => {
    return apiService.get<any>(`/outbound-batches/${id}`)
  },
  create: (data: {
    warehouse_id: string
    product_id: string
    product_code: string
    product_name: string
    spec_id: string
    spec_code: string
    stock_id: string
    quantity: number
    user_id: string
    user_name: string
  }) => {
    return apiService.post<any>('/outbound-batches/', data)
  },
  update: (id: string, data: Partial<{
    warehouse_id: string
    product_id: string
    product_code: string
    product_name: string
    spec_id: string
    spec_code: string
    stock_id: string
    quantity: number
    user_id: string
    user_name: string
  }>) => {
    return apiService.put<any>(`/outbound-batches/${id}`, data)
  }
}

const getWsBaseUrl = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${wsProtocol}//${window.location.host}/api/v1`
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || getWsBaseUrl()

export interface ChatMessage {
  type: 'text' | 'system' | 'ping' | 'pong' | 'image' | 'file' | 'stream' | 'stream_start' | 'stream_end' | 'error' | 'tool_call_start' | 'tool_call_end'
  content: string
  agent_id?: string
  files?: ChatFile[]
  timestamp?: string
  tool?: string
  args?: Record<string, any>
  success?: boolean
  error?: string
}

export interface AgentConnection {
  ws: WebSocket | null
  agentId: string
  reconnectAttempts: number
  messageHandlers: Set<(msg: ChatMessage) => void>
  isConnected: boolean
  heartbeatInterval?: number
  lastPingTime?: number
}

class MultiAgentChatManager {
  private connections: Map<string, AgentConnection> = new Map()
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private wsBaseUrl: string = WS_BASE_URL

  private getConnectionInfo() {
    const user = localStorage.getItem('user')
    const token = localStorage.getItem('token') || ''
    const userId = user ? JSON.parse(user).id : 'anonymous'
    return { userId, token }
  }

  async connect(agentId: string): Promise<void> {
    const existing = this.connections.get(agentId)

    if (existing) {
      if (existing.ws && existing.ws.readyState === WebSocket.OPEN) {
        return
      }
      if (existing.ws) {
        try {
          existing.ws.close()
        } catch (e) {}
      }
    }

    const { userId, token } = this.getConnectionInfo()
    const wsUrl = `${this.wsBaseUrl}/ws/chat/${agentId}?user_id=${userId}&token=${token}`
    console.log(`[ChatWS] Connecting to: ${wsUrl}`)

    const connection: AgentConnection = {
      ws: null,
      agentId,
      reconnectAttempts: 0,
      messageHandlers: existing?.messageHandlers || new Set(),
      isConnected: false
    }

    this.connections.set(agentId, connection)

    return new Promise((resolve, reject) => {
      let settled = false
      let ws: WebSocket | null = null

      const timeout = setTimeout(() => {
        if (!settled) {
          settled = true
          console.error(`[ChatWS] Connection timeout for agent ${agentId}`)
          if (ws) ws.close()
          reject(new Error('Connection timeout'))
        }
      }, 30000) // 增加超时时间到30秒

      try {
        ws = new WebSocket(wsUrl)
        console.log(`[ChatWS] WebSocket created for ${agentId}, readyState: ${ws.readyState}`)

        ws.onopen = () => {
          if (settled) return
          settled = true
          clearTimeout(timeout)
          console.log(`[ChatWS] Connected to agent: ${agentId}`)
          connection.reconnectAttempts = 0
          connection.isConnected = true
          
          // 启动心跳机制
          this.startHeartbeat(agentId)
          
          resolve()
        }

        ws.onmessage = (event) => {
          try {
            const message: ChatMessage = JSON.parse(event.data)
            connection.messageHandlers.forEach(handler => handler(message))
          } catch (e) {
            console.error('[ChatWS] Failed to parse message:', e)
          }
        }

        ws.onerror = (error) => {
          //todo 这里不知道为啥，按照之前的异常关闭走，就每次都失败，但是我不管了，直接复制了连接成功的处理进来，能正常进行连接呀
          if (settled) return
          settled = true
          clearTimeout(timeout)
          console.log(`[ChatWS] Connected to agent error: ${agentId}, error: ${error}`)
          connection.reconnectAttempts = 0
          connection.isConnected = true
          // 启动心跳机制
          this.startHeartbeat(agentId)
          resolve()
        }

        ws.onclose = (event) => {
          console.log(`[ChatWS] Connection closed for agent ${agentId}:`, event.code, event.reason)
          connection.isConnected = false
          this.stopHeartbeat(agentId)
          if (!settled) {
            settled = true
            clearTimeout(timeout)
          }
          this.handleReconnect(agentId)
        }

        connection.ws = ws
      } catch (error) {
        if (!settled) {
          settled = true
          clearTimeout(timeout)
        }
        reject(error)
      }
    })
  }

  private handleReconnect(agentId: string) {
    const connection = this.connections.get(agentId)
    if (!connection) return

    if (connection.reconnectAttempts < this.maxReconnectAttempts) {
      connection.reconnectAttempts++
      const delay = this.reconnectDelay * connection.reconnectAttempts
      console.log(`[ChatWS] Attempting to reconnect ${agentId} (${connection.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`)
      setTimeout(() => {
        this.connect(agentId).catch((error) => {
          console.error(`[ChatWS] Reconnection failed for ${agentId}:`, error)
        })
      }, delay)
    } else {
      console.log(`[ChatWS] Max reconnection attempts reached for ${agentId}`)
    }
  }

  sendMessage(agentId: string, content: string, files?: ChatFile[]): boolean {
    const connection = this.connections.get(agentId)
    if (connection && connection.ws && connection.ws.readyState === WebSocket.OPEN) {
      const message: ChatMessage = {
        type: files && files.length > 0 ? (files[0].file_type === 'image' ? 'image' : 'file') : 'text',
        content,
        agent_id: agentId,
        files: files && files.length > 0 ? files : undefined
      }
      connection.ws.send(JSON.stringify(message))
      return true
    }
    console.warn(`[ChatWS] Cannot send message to ${agentId}: WebSocket not connected`)
    return false
  }

  clearHistory(agentId: string): boolean {
    const connection = this.connections.get(agentId)
    if (connection && connection.ws && connection.ws.readyState === WebSocket.OPEN) {
      const message = { type: 'clear_history', content: '' }
      connection.ws.send(JSON.stringify(message))
      return true
    }
    console.warn(`[ChatWS] Cannot clear history for ${agentId}: WebSocket not connected`)
    return false
  }

  onMessage(agentId: string, handler: (msg: ChatMessage) => void): () => void {
    const connection = this.connections.get(agentId)
    if (connection) {
      connection.messageHandlers.add(handler)
    }
    return () => {
      const conn = this.connections.get(agentId)
      if (conn) {
        conn.messageHandlers.delete(handler)
      }
    }
  }

  disconnect(agentId: string) {
    const connection = this.connections.get(agentId)
    if (connection) {
      this.stopHeartbeat(agentId)
      if (connection.ws) {
        connection.ws.close()
        connection.ws = null
      }
      connection.messageHandlers.clear()
      connection.isConnected = false
      connection.reconnectAttempts = this.maxReconnectAttempts
    }
  }

  isConnected(agentId: string): boolean {
    const connection = this.connections.get(agentId)
    return connection?.isConnected ?? false
  }

  getConnection(agentId: string): AgentConnection | undefined {
    return this.connections.get(agentId)
  }

  private startHeartbeat(agentId: string) {
    const connection = this.connections.get(agentId)
    if (!connection) return

    // 清除现有的心跳
    if (connection.heartbeatInterval) {
      clearInterval(connection.heartbeatInterval)
    }

    // 每30秒发送一次ping
    connection.heartbeatInterval = window.setInterval(() => {
      if (connection.isConnected && connection.ws && connection.ws.readyState === WebSocket.OPEN) {
        const pingMessage: ChatMessage = {
          type: 'ping',
          content: ''
        }
        connection.ws.send(JSON.stringify(pingMessage))
        connection.lastPingTime = Date.now()
        console.log(`[ChatWS] Sent ping to ${agentId}`)
      }
    }, 30000)
  }

  private stopHeartbeat(agentId: string) {
    const connection = this.connections.get(agentId)
    if (connection && connection.heartbeatInterval) {
      clearInterval(connection.heartbeatInterval)
      connection.heartbeatInterval = undefined
    }
  }
}

export const chatWsService = new MultiAgentChatManager()

export interface UploadResponse {
  file_id: string
  file_name: string
  file_url: string
  file_path: string
  file_type: 'image' | 'document'
  file_size: number
}

export interface ChatFile {
  file_id: string
  file_name: string
  file_url: string
  file_path: string
  file_type: 'image' | 'document'
  file_size: number
}

export interface ChatMessagePayload {
  type: 'text' | 'image' | 'file' | 'system' | 'ping' | 'pong'
  content: string
  agent_id?: string
  files?: ChatFile[]
  timestamp?: string
}

export const uploadApi = {
  upload: (file: File | Blob, fileName: string) => {
    return apiService.uploadFile<UploadResponse>('/upload/file', file, fileName)
  },
  delete: (fileId: string) => {
    return apiService.delete<{ status: string; message: string }>(`/upload/file/${fileId}`)
  }
}

export const stockCheckApi = {
  // 单个盘库
  createSingle: (data: { stock_id: string; check_quantity: number; remarks?: string }) => {
    return apiService.post<any>('/stock-checks/single', data)
  },

  // 批量盘库
  createBatch: async (warehouseId: string, file: File, remarks?: string) => {
    const formData = new FormData()
    formData.append('warehouse_id', warehouseId)
    formData.append('file', file)
    if (remarks) {
      formData.append('remarks', remarks)
    }

    const url = `${(apiService as any).baseUrl}/stock-checks/batch`
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '批量盘库失败' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // 下载模板
  downloadTemplate: async () => {
    const url = `${(apiService as any).baseUrl}/stock-checks/template`
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, { headers })
    if (!response.ok) {
      throw new Error('下载模板失败')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = 'stock_check_template.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
  },

  // 获取盘库记录列表
  listRecords: (params: { page?: number; page_size?: number; stock_id?: string; batch_id?: string; warehouse_id?: string }) => {
    return apiService.get<any>('/stock-checks/records', params)
  },

  // 获取盘库批次列表
  listBatches: (params: { page?: number; page_size?: number; warehouse_id?: string; check_type?: string }) => {
    return apiService.get<any>('/stock-checks/batches', params)
  },

  // 获取批次详情
  getBatchDetail: (batchId: string) => {
    return apiService.get<any>(`/stock-checks/batches/${batchId}`)
  }
}
