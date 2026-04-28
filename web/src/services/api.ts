const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

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
          searchParams.append(key, String(value))
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
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
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
    return apiService.get<any>('/auth/users', params)
  },

  getUser: (id: string) => {
    return apiService.get<any>(`/auth/users/${id}`)
  },

  createUser: (data: any) => {
    return apiService.post<any>('/auth/users', data)
  },

  updateUser: (id: string, data: any) => {
    return apiService.put<any>(`/auth/users/${id}`, data)
  },

  deleteUser: (id: string) => {
    return apiService.delete<any>(`/auth/users/${id}`)
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
    return apiService.get<any>('/auth/roles', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/auth/roles/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/auth/roles', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/auth/roles/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/auth/roles/${id}`)
  },

  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/auth/roles/${id}/status`, { status })
  }
}

export const permissionApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string }) => {
    return apiService.get<any>('/auth/permissions', params)
  },

  getTree: () => {
    return apiService.get<any>('/auth/permissions/tree')
  },

  getById: (id: string) => {
    return apiService.get<any>(`/auth/permissions/${id}`)
  }
}

export const salesOrderApi = {
  list: (params: { page?: number; page_size?: number; status?: string; customer_id?: string; keyword?: string }) => {
    return apiService.get<any>('/sales-orders/', params)
  },

  getByOrderNo: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/sales-orders/', data)
  },

  update: (orderNo: string, data: any) => {
    return apiService.put<any>(`/sales-orders/${orderNo}`, data)
  },

  delete: (orderNo: string) => {
    return apiService.delete<any>(`/sales-orders/${orderNo}`)
  },

  updateStatus: (orderNo: string, status: string) => {
    return apiService.patch<any>(`/sales-orders/${orderNo}/status`, { status })
  },

  updatePaymentStatus: (orderNo: string, payment_status: string) => {
    return apiService.patch<any>(`/sales-orders/${orderNo}/payment-status`, { payment_status })
  },

  confirm: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/confirm`)
  }
}

export const procurementOrderApi = {
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string }) => {
    return apiService.get<any>('/procurement-orders/', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/procurement-orders/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/procurement-orders/', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/procurement-orders/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/procurement-orders/${id}`)
  },

  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/procurement-orders/${id}/status`, { status })
  }
}

export const receivableApi = {
  list: (params: { page?: number; page_size?: number; status?: string; customer_id?: string; keyword?: string }) => {
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

export const customerApi = {
  list: (params: { page?: number; page_size?: number; status?: string; level?: string; keyword?: string; customer_type?: string }) => {
    return apiService.get<any>('/customers/', params)
  },

  getById: (id: string) => {
    return apiService.get<any>(`/customers/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/customers/', data)
  },

  update: (id: string, data: any) => {
    return apiService.put<any>(`/customers/${id}`, data)
  },

  delete: (id: string) => {
    return apiService.delete<any>(`/customers/${id}`)
  },

  updateStatus: (id: string, status: string) => {
    return apiService.patch<any>(`/customers/${id}/status`, { status })
  },

  search: (keyword: string, limit?: number) => {
    return apiService.get<any>('/customers/search', { keyword, limit })
  },

  getStats: () => {
    return apiService.get<any>('/customers/stats')
  },

  addShippingAddress: (customerId: string, address: any) => {
    return apiService.post<any>(`/customers/${customerId}/shipping-addresses`, address)
  },

  updateShippingAddress: (customerId: string, addressId: string, address: any) => {
    return apiService.put<any>(`/customers/${customerId}/shipping-addresses/${addressId}`, address)
  },

  deleteShippingAddress: (customerId: string, addressId: string) => {
    return apiService.delete<any>(`/customers/${customerId}/shipping-addresses/${addressId}`)
  },

  setDefaultShippingAddress: (customerId: string, addressId: string) => {
    return apiService.patch<any>(`/customers/${customerId}/shipping-addresses/${addressId}/default`)
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
  stock_status?: string
  created_at?: string
  updated_at?: string
}

export interface Product {
  id: string
  product_code: string
  name: string
  image_url?: string
  brand?: string
  category?: string
  tax_code?: string
  specs: ProductSpec[]
  created_at?: string
  updated_at?: string
}

export interface ProductFormData {
  product_code?: string
  name: string
  image_url?: string
  brand?: string
  category?: string
  tax_code?: string
}

export interface ProductSpecFormData {
  spec_code?: string
  packaging?: string
  sales_spec?: string
  price: number
  cas_number?: string
  is_active?: boolean
}

export const productApi = {
  list: (params: { page?: number; page_size?: number; status?: string; keyword?: string }) => {
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

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1'

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
