<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  customerApi,
  type Customer,
  type CustomerListItem,
  type InvoiceInfo,
  type ShippingAddressV2
} from '../../services/api'
import { authApi } from '../../services/api'
import ProvinceCitySelector from '../common/ProvinceCitySelector.vue'

const loading = ref(false)
const customers = ref<CustomerListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterType = ref('')
const stats = ref({ total: 0, terminal_count: 0, dealer_count: 0 })

const showCustomerModal = ref(false)
const showDeleteConfirm = ref(false)
const editingCustomer = ref<Customer | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)

const showAiPanel = ref(false)
const aiInputText = ref('')
const aiImageFile = ref<File | null>(null)
const aiLoading = ref(false)

const showTransferModal = ref(false)
const transferTargetId = ref<string | null>(null)
const transferTargetName = ref<string>('')
const salesUsers = ref<any[]>([])
const selectedSalesUserId = ref<string>('')
const salesUserKeyword = ref('')
const transferLoading = ref(false)

const customerForm = ref({
  name: '',
  customer_type: 'terminal' as 'terminal' | 'dealer',
  research_group: ''
})

const contactForm = ref({
  contact_person: '',
  contact_phone: '',
  contact_email: ''
})

const invoiceInfos = ref<InvoiceInfo[]>([])
const shippingAddresses = ref<ShippingAddressV2[]>([])

const customerTypes = [
  { value: 'terminal', label: '终端' },
  { value: 'dealer', label: '经销商' }
]

const customerTypeMap: Record<string, string> = {
  terminal: '终端',
  dealer: '经销商'
}

const statusMap: Record<string, string> = {
  normal: '正常',
  inactive: '停用',
  blacklisted: '黑名单'
}

const showResearchGroup = computed(() => customerForm.value.customer_type === 'terminal')
const isEditing = computed(() => editingCustomer.value !== null)

const loadCustomers = async () => {
  loading.value = true
  try {
    const res = await customerApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      customer_type: filterType.value || undefined
    })
    if (res) {
      customers.value = res.items || []
      total.value = res.total || 0
    } else {
      customers.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await customerApi.getStats()
    stats.value = res || { total: 0, terminal_count: 0, dealer_count: 0 }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadCustomers()
}

const handleSearch = () => {
  page.value = 1
  loadCustomers()
}

const hasActiveFilters = computed(() => !!(keyword.value || filterType.value))

const resetFilters = () => {
  keyword.value = ''
  filterType.value = ''
  page.value = 1
  loadCustomers()
}

const resetCustomerForm = () => {
  customerForm.value = {
    name: '',
    customer_type: 'terminal',
    research_group: ''
  }
  contactForm.value = {
    contact_person: '',
    contact_phone: '',
    contact_email: ''
  }
  invoiceInfos.value = []
  shippingAddresses.value = []
  editingCustomer.value = null
}

const toggleAiPanel = () => {
  showAiPanel.value = !showAiPanel.value
  if (showAiPanel.value) {
    aiInputText.value = ''
    aiImageFile.value = null
  }
}

const handleImageChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    aiImageFile.value = target.files[0]
  }
}

const handleAiSubmit = async () => {
  if (!aiInputText.value && !aiImageFile.value) {
    window.showToast('请输入文本或上传图片', 'warning')
    return
  }

  aiLoading.value = true
  try {
    let filePath: string | undefined
    if (aiImageFile.value) {
      filePath = (aiImageFile.value as any).path
    }

    const response = await customerApi.createFromAi({
      input: aiInputText.value || undefined,
      file_path: filePath
    })

    if (response && response.result) {
      const data = response.result
      customerForm.value = {
        name: data.name || '',
        customer_type: data.customer_type || 'terminal',
        research_group: data.research_group || ''
      }
      contactForm.value = {
        contact_person: data.contact_person || '',
        contact_phone: data.contact_phone || '',
        contact_email: data.contact_email || ''
      }
      if (data.invoice_infos && data.invoice_infos.length > 0) {
        invoiceInfos.value = data.invoice_infos.map((info: any) => ({
          invoice_title: info.invoice_title || '',
          invoice_type: info.invoice_type || '增值税',
          tax_number: info.tax_number || '',
          bank_name: info.bank_name || '',
          bank_account: info.bank_account || '',
          is_default: info.is_default || false
        }))
      }
      if (data.shipping_addresses && data.shipping_addresses.length > 0) {
        shippingAddresses.value = data.shipping_addresses.map((addr: any) => ({
          recipient_name: addr.recipient_name || '',
          recipient_phone: addr.recipient_phone || '',
          province: addr.province || '',
          province_code: addr.province_code || '',
          city: addr.city || '',
          city_code: addr.city_code || '',
          address: addr.address || '',
          is_default: addr.is_default || false
        }))
      }
      showAiPanel.value = false
      window.showToast('AI 信息已填充到表单', 'success')
    }
  } catch (error: any) {
    window.showToast(error.message || 'AI 解析失败', 'error')
  } finally {
    aiLoading.value = false
  }
}

const openCreateCustomer = () => {
  resetCustomerForm()
  showCustomerModal.value = true
}

const openEditCustomer = async (row: CustomerListItem) => {
  try {
    formLoading.value = true
    const res = await customerApi.getById(row.id)
    const customer: Customer = res

    editingCustomer.value = customer
    customerForm.value = {
      name: customer.name,
      customer_type: customer.customer_type,
      research_group: customer.research_group || ''
    }
    contactForm.value = {
      contact_person: customer.contact_person || '',
      contact_phone: customer.contact_phone || '',
      contact_email: customer.contact_email || ''
    }
    invoiceInfos.value = customer.invoice_infos || []
    shippingAddresses.value = customer.shipping_addresses || []

    showCustomerModal.value = true
  } catch (error: any) {
    window.showToast(error.message || '加载客户详情失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const validateCustomerForm = (): boolean => {
  if (!customerForm.value.name?.trim()) {
    window.showToast('请输入客户名称', 'warning')
    return false
  }
  if (!customerForm.value.customer_type) {
    window.showToast('请选择客户类型', 'warning')
    return false
  }
  if (showResearchGroup.value && !customerForm.value.research_group?.trim()) {
    window.showToast('请输入课题组信息', 'warning')
    return false
  }
  return true
}

const handleSaveCustomer = async () => {
  if (!validateCustomerForm()) return

  formLoading.value = true
  try {
    const customerData: any = {
      name: customerForm.value.name.trim(),
      customer_type: customerForm.value.customer_type,
      research_group: customerForm.value.research_group?.trim() || undefined,
      contact_person: contactForm.value.contact_person?.trim() || undefined,
      contact_phone: contactForm.value.contact_phone?.trim() || undefined,
      contact_email: contactForm.value.contact_email?.trim() || undefined,
      invoice_infos: invoiceInfos.value.map((info) => ({
        id: info.id || undefined,
        invoice_title: info.invoice_title,
        invoice_type: info.invoice_type,
        tax_number: info.tax_number,
        bank_name: info.bank_name,
        bank_account: info.bank_account,
        is_default: info.is_default === true
      })),
      shipping_addresses: shippingAddresses.value.map((addr) => ({
        id: addr.id || undefined,
        recipient_name: addr.recipient_name,
        recipient_phone: addr.recipient_phone,
        province: addr.province || '',
        province_code: addr.province_code || '',
        city: addr.city || '',
        city_code: addr.city_code || '',
        address: addr.address,
        is_default: addr.is_default === true
      }))
    }

    if (editingCustomer.value) {
      await customerApi.update(editingCustomer.value.id, customerData)
      window.showToast('客户更新成功', 'success')
    } else {
      await customerApi.create(customerData)
      window.showToast('客户创建成功', 'success')
    }

    showCustomerModal.value = false
    loadCustomers()
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = (customerId: string) => {
  deleteTargetId.value = customerId
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await customerApi.delete(deleteTargetId.value)
    window.showToast('客户删除成功', 'success')
    customers.value = customers.value.filter(c => c.id !== deleteTargetId.value)
    total.value--
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const loadSalesUsers = async (keyword?: string) => {
  try {
    const res = await authApi.listUsers({ keyword, page_size: 100 })
    if (res) {
      salesUsers.value = res.items || []
    } else {
      salesUsers.value = []
    }
  } catch (error) {
    console.error('加载销售员列表失败:', error)
  }
}

const openTransferModal = async (customer: CustomerListItem) => {
  transferTargetId.value = customer.id
  transferTargetName.value = customer.name
  selectedSalesUserId.value = ''
  salesUserKeyword.value = ''
  await loadSalesUsers()
  showTransferModal.value = true
}

const handleTransfer = async () => {
  if (!transferTargetId.value || !selectedSalesUserId.value) {
    window.showToast('请选择目标销售', 'warning')
    return
  }

  transferLoading.value = true
  try {
    await customerApi.transfer(transferTargetId.value, selectedSalesUserId.value)
    window.showToast('客户转移成功', 'success')
    showTransferModal.value = false
    transferTargetId.value = null
    transferTargetName.value = ''
    loadCustomers()
  } catch (error: any) {
    window.showToast(error.message || '转移失败', 'error')
  } finally {
    transferLoading.value = false
  }
}

const closeTransferModal = () => {
  showTransferModal.value = false
  transferTargetId.value = null
  transferTargetName.value = ''
  selectedSalesUserId.value = ''
  salesUserKeyword.value = ''
  salesUsers.value = []
}

const addInvoiceInfo = () => {
  invoiceInfos.value.push({
    invoice_title: '',
    invoice_type: '增值税',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    is_default: invoiceInfos.value.length === 0
  })
}

const removeInvoiceInfo = (index: number) => {
  const wasDefault = invoiceInfos.value[index].is_default
  invoiceInfos.value.splice(index, 1)
  if (invoiceInfos.value.length > 0) {
    if (wasDefault || !invoiceInfos.value.some(i => i.is_default)) {
      invoiceInfos.value[0].is_default = true
    }
  }
}

const setDefaultInvoice = (index: number) => {
  invoiceInfos.value.forEach((info, i) => {
    info.is_default = i === index
  })
}

const addShippingAddress = () => {
  shippingAddresses.value.push({
    recipient_name: '',
    recipient_phone: '',
    province: '',
    province_code: '',
    city: '',
    city_code: '',
    address: '',
    is_default: shippingAddresses.value.length === 0
  })
}

const removeShippingAddress = (index: number) => {
  const wasDefault = shippingAddresses.value[index].is_default
  shippingAddresses.value.splice(index, 1)
  if (shippingAddresses.value.length > 0) {
    if (wasDefault || !shippingAddresses.value.some(a => a.is_default)) {
      shippingAddresses.value[0].is_default = true
    }
  }
}

const setDefaultAddress = (index: number) => {
  shippingAddresses.value.forEach((addr, i) => {
    addr.is_default = i === index
  })
}

const openDiscountSettings = (customer: CustomerListItem) => {
  const event = new CustomEvent('navigate-to-discount', {
    detail: {
      customerId: customer.id,
      customerName: customer.name
    }
  })
  window.dispatchEvent(event)
}

onMounted(() => {
  loadCustomers()
  loadStats()
})

const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    showCustomerModal.value = false
    closeTransferModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})

const seqMethod = ({ row }: { row: CustomerListItem }) => {
  const index = customers.value.findIndex(c => c.id === row.id)
  return index + 1 + (page.value - 1) * pageSize.value
}
</script>

<template>
  <div class="crm-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">客户管理</h2>
      <button class="primary-btn" @click="openCreateCustomer">新建客户</button>
    </div>

    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total || 0 }}</div>
        <div class="stat-label">客户总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.terminal_count || 0 }}</div>
        <div class="stat-label">终端客户</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.dealer_count || 0 }}</div>
        <div class="stat-label">经销商</div>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索客户名称、编码..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filterType" class="filter-select">
          <option value="">全部类型</option>
          <option v-for="t in customerTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
    </div>

    <div class="table-section" style="position: relative;">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="customers"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: seqMethod }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center col--header-center" />
        <vxe-column field="name" title="客户名称" min-width="250" class-name="col--center col--header-center" />
        <vxe-column field="customer_type" title="客户类型" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="type-tag" :class="row.customer_type">
              {{ customerTypeMap[row.customer_type] || row.customer_type }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="contact_person" title="联系人" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ row.contact_person || '-' }}
          </template>
        </vxe-column>
        <vxe-column field="contact_phone" title="联系电话" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ row.contact_phone || '-' }}
          </template>
        </vxe-column>
        <vxe-column field="sales_user_name" title="销售人" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ row.sales_user_name || '-' }}
          </template>
        </vxe-column>
        <vxe-column field="status" title="状态" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status">
              {{ statusMap[row.status] || '正常' }}
            </span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="340" fixed="right" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="openEditCustomer(row)">编辑</button>
              <button class="btn-link" @click="openTransferModal(row)">转移</button>
              <button class="btn-link" @click="openDiscountSettings(row)">折扣设置</button>
              <button class="btn-link danger" @click="confirmDelete(row.id)">删除</button>
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

    <!-- 客户编辑弹窗 -->
    <div class="modal-overlay" v-if="showCustomerModal">
      <div class="modal customer-modal">
        <div class="modal-header">
          <div class="modal-header-left">
            <h3>{{ isEditing ? '编辑客户' : '新建客户' }}</h3>
            <button v-if="!isEditing" class="ai-btn" @click="toggleAiPanel" :class="{ active: showAiPanel }">
              <span class="ai-icon">🤖</span> AI
            </button>
          </div>
          <button class="modal-close" @click="showCustomerModal = false">×</button>
        </div>

        <!-- AI 输入面板 -->
        <div class="ai-panel" v-if="showAiPanel && !isEditing">
          <div class="ai-panel-content">
            <div class="form-group">
              <label>输入文本描述</label>
              <textarea
                v-model="aiInputText"
                placeholder="请输入客户信息描述，如：客户名称是xxx，联系人是xxx，电话是xxx..."
                rows="4"
              ></textarea>
            </div>
            <div class="form-group">
              <label>或上传图片</label>
              <div class="image-upload">
                <input type="file" accept="image/*" @change="handleImageChange" id="ai-image-upload" />
                <label for="ai-image-upload" class="upload-label">
                  <span v-if="!aiImageFile">点击上传图片</span>
                  <span v-else>{{ aiImageFile.name }}</span>
                </label>
              </div>
            </div>
            <div class="ai-panel-footer">
              <button class="btn-secondary" @click="toggleAiPanel">取消</button>
              <button class="btn-primary" @click="handleAiSubmit" :disabled="aiLoading">
                {{ aiLoading ? '解析中...' : '提交解析' }}
              </button>
            </div>
          </div>
        </div>

        <div class="modal-body" v-else>
          <!-- 基本信息 -->
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>客户名称 <span class="required">*</span></label>
                <input type="text" v-model="customerForm.name" placeholder="请输入客户名称" />
              </div>
              <div class="form-group">
                <label>客户类型 <span class="required">*</span></label>
                <select v-model="customerForm.customer_type">
                  <option v-for="t in customerTypes" :key="t.value" :value="t.value">
                    {{ t.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-row" v-if="showResearchGroup">
              <div class="form-group">
                <label>课题组信息</label>
                <input type="text" v-model="customerForm.research_group" placeholder="请输入课题组信息" />
              </div>
              <div class="form-group" v-if="!showResearchGroup"></div>
            </div>
          </div>

          <!-- 联系人信息 -->
          <div class="form-section">
            <div class="section-title">联系人信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>联系人</label>
                <input type="text" v-model="contactForm.contact_person" placeholder="请输入联系人姓名" />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input type="text" v-model="contactForm.contact_phone" placeholder="请输入联系电话" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>电子邮箱</label>
                <input type="email" v-model="contactForm.contact_email" placeholder="请输入电子邮箱" />
              </div>
            </div>
          </div>

          <!-- 开票信息 -->
          <div class="form-section">
            <div class="section-title">
              <span>开票信息</span>
              <button class="btn-link add-btn" @click="addInvoiceInfo">+ 添加</button>
            </div>
            <div class="info-table" v-if="invoiceInfos.length > 0">
              <div class="info-table-header">
                <div class="info-th" style="flex: 2;">开票抬头</div>
                <div class="info-th" style="flex: 1;">开票类型</div>
                <div class="info-th" style="flex: 1.5;">税务编码</div>
                <div class="info-th" style="flex: 1.5;">开户银行</div>
                <div class="info-th" style="flex: 1.5;">银行账号</div>
                <div class="info-th" style="width: 120px;">操作</div>
              </div>
              <div class="info-table-body">
                <div
                  class="info-tr"
                  :class="{ 'is-default': info.is_default }"
                  v-for="(info, idx) in invoiceInfos"
                  :key="idx"
                >
                  <div class="info-td" style="flex: 2;">
                    <input type="text" v-model="info.invoice_title" placeholder="开票抬头" />
                  </div>
                  <div class="info-td" style="flex: 1;">
                    <select v-model="info.invoice_type">
                      <option value="增值税">增值税</option>
                      <option value="普通发票">普通发票</option>
                      <option value="增值税专用发票">增值税专用发票</option>
                      <option value="不开票">不开票</option>
                    </select>
                  </div>
                  <div class="info-td" style="flex: 1.5;">
                    <input type="text" v-model="info.tax_number" placeholder="税务编码" />
                  </div>
                  <div class="info-td" style="flex: 1.5;">
                    <input type="text" v-model="info.bank_name" placeholder="开户银行" />
                  </div>
                  <div class="info-td" style="flex: 1.5;">
                    <input type="text" v-model="info.bank_account" placeholder="银行账号" />
                  </div>
                  <div class="info-td" style="width: 120px; display: flex; gap: 4px;">
                    <button class="btn-link" @click="setDefaultInvoice(idx)" v-if="!info.is_default">设默认</button>
                    <button class="btn-link danger" @click="removeInvoiceInfo(idx)" v-if="invoiceInfos.length > 1">删除</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="empty-tip" v-else>暂无开票信息</div>
          </div>

          <!-- 收货地址 -->
          <div class="form-section">
            <div class="section-title">
              <span>收货地址</span>
              <button class="btn-link add-btn" @click="addShippingAddress">+ 添加</button>
            </div>
            <div class="info-table" v-if="shippingAddresses.length > 0">
              <div class="info-table-header">
                <div class="info-th" style="flex: 1;">收货人</div>
                <div class="info-th" style="flex: 1.2;">联系电话</div>
                <div class="info-th" style="flex: 1;">省份</div>
                <div class="info-th" style="flex: 1;">城市</div>
                <div class="info-th" style="flex: 2;">详细地址</div>
                <div class="info-th" style="width: 120px;">操作</div>
              </div>
              <div class="info-table-body">
                <div
                  class="info-tr"
                  :class="{ 'is-default': addr.is_default }"
                  v-for="(addr, idx) in shippingAddresses"
                  :key="idx"
                >
                  <div class="info-td" style="flex: 1;">
                    <input type="text" v-model="addr.recipient_name" placeholder="收货人" />
                  </div>
                  <div class="info-td" style="flex: 1.2;">
                    <input type="text" v-model="addr.recipient_phone" placeholder="联系电话" />
                  </div>
                  <div class="info-td" style="flex: 1.5;">
                    <ProvinceCitySelector
                      v-model:province="addr.province"
                      v-model:provinceCode="addr.province_code"
                      v-model:city="addr.city"
                      v-model:cityCode="addr.city_code"
                    />
                  </div>
                  <div class="info-td" style="flex: 1.5;">
                    <input type="text" v-model="addr.address" placeholder="详细地址" />
                  </div>
                  <div class="info-td" style="width: 120px; display: flex; gap: 4px;">
                    <button class="btn-link" @click="setDefaultAddress(idx)" v-if="!addr.is_default">设默认</button>
                    <button class="btn-link danger" @click="removeShippingAddress(idx)" v-if="shippingAddresses.length > 1">删除</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="empty-tip" v-else>暂无收货地址</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCustomerModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveCustomer" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该客户吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 转移客户弹窗 -->
    <div class="modal-overlay" v-if="showTransferModal" @click.self="closeTransferModal">
      <div class="modal transfer-modal">
        <div class="modal-header">
          <h3>转移客户</h3>
          <button class="modal-close" @click="closeTransferModal">×</button>
        </div>
        <div class="modal-body">
          <p class="transfer-info">确定将客户 <strong>{{ transferTargetName }}</strong> 转移给其他销售吗？</p>
          <div class="form-group">
            <label>选择目标销售</label>
            <div class="sales-user-search">
              <input
                type="text"
                v-model="salesUserKeyword"
                placeholder="搜索销售员姓名..."
                class="filter-input"
                @input="loadSalesUsers(salesUserKeyword)"
              />
            </div>
            <div class="sales-user-list">
              <div
                v-for="user in salesUsers"
                :key="user.id"
                class="sales-user-item"
                :class="{ selected: selectedSalesUserId === user.id }"
                @click="selectedSalesUserId = user.id"
              >
                <span class="sales-user-name">{{ user.full_name || user.username }}</span>
                <span class="sales-user-dept">{{ user.department || '-' }}</span>
              </div>
              <div v-if="salesUsers.length === 0" class="empty-tip">暂无销售员</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeTransferModal">取消</button>
          <button class="btn-primary" @click="handleTransfer" :disabled="transferLoading || !selectedSalesUserId">
            {{ transferLoading ? '转移中...' : '确认转移' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.crm-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  margin: 0;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 16px;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-interactive);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-muted);
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

.filter-input::placeholder {
  color: var(--color-muted);
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
  min-width: 100px;
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
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.table-section {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  box-shadow: var(--shadow-card);
}

:deep(.col--header-center .vxe-cell--title) {
  text-align: center;
  justify-content: center;
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

.btn-link.add-btn {
  font-size: 12px;
  padding: 2px 8px;
}

.type-tag,
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag.terminal {
  background-color: var(--color-accent-soft);
  color: var(--color-accent);
}

.type-tag.dealer {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-tag.normal,
.status-tag.active {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-tag.inactive {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-tag.blacklisted {
  background-color: var(--color-danger-bg);
  color: var(--color-danger);
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
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 95%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.customer-modal {
  max-width: 900px;
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

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ai-btn:hover {
  background-color: var(--color-accent);
}

.ai-btn.active {
  background-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-soft);
}

.ai-icon {
  font-size: 14px;
}

.ai-panel {
  padding: 20px;
  background-color: var(--color-neutral-bg);
  border-bottom: 1px solid var(--color-hairline);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-panel-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-panel textarea {
  width: 100%;
  padding: 12px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.ai-panel textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.image-upload input[type="file"] {
  display: none;
}

.upload-label {
  display: inline-block;
  padding: 12px 16px;
  background-color: var(--color-canvas);
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  width: 100%;
  text-align: center;
}

.upload-label:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.ai-panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
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
  background-color: rgba(0, 0, 0, 0.06);
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
  position: sticky;
  bottom: 0;
  background-color: var(--color-canvas);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-hairline);
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  color: var(--color-muted);
}

.form-group .required {
  color: var(--color-danger);
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.form-group input::placeholder {
  color: var(--color-muted);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-sm);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-row .full-width {
  grid-column: span 2;
}

.info-row .action-col {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.info-table {
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.info-table-header {
  display: flex;
  background-color: var(--color-neutral-bg);
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-hairline);
}

.info-th {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  padding: 0 8px;
}

.info-table-body {
  max-height: 200px;
  overflow-y: auto;
}

.info-tr {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-hairline);
}

.info-tr:last-child {
  border-bottom: none;
}

.info-tr:hover {
  background-color: var(--color-info-bg);
}

.info-tr.is-default {
  background-color: var(--color-info-bg);
  border-left: 3px solid var(--color-interactive);
}

.info-tr.is-default:hover {
  background-color: var(--color-info-bg);
}

.cell-with-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
}

.cell-with-badge input {
  padding-right: 40px;
}

.row-default-badge {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 2px 8px;
  background: var(--color-interactive);
  color: var(--color-text-inverse);
  font-size: 11px;
  font-weight: 500;
  border-radius: 10px;
  box-shadow: 0 2px 4px var(--color-info-bg);
  pointer-events: none;
}

.info-td {
  padding: 0 8px;
}

.info-td input,
.info-td select {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.info-td input:focus,
.info-td select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.info-td input::placeholder {
  color: var(--color-muted);
  font-size: 12px;
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: var(--color-muted);
  font-size: 13px;
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-primary:disabled {
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
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  background-color: var(--color-danger);
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

.transfer-modal {
  max-width: 480px;
}

.transfer-info {
  font-size: 14px;
  color: var(--color-ink);
  margin: 0 0 16px 0;
}

.transfer-info strong {
  color: var(--color-interactive);
}

.sales-user-search {
  margin-bottom: 12px;
}

.sales-user-list {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
}

.sales-user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-hairline);
  transition: background-color var(--transition-fast);
}

.sales-user-item:last-child {
  border-bottom: none;
}

.sales-user-item:hover {
  background-color: var(--color-info-bg);
}

.sales-user-item.selected {
  background-color: var(--color-info-bg);
  border-left: 3px solid var(--color-interactive);
}

.sales-user-name {
  font-size: 14px;
  color: var(--color-ink);
}

.sales-user-dept {
  font-size: 12px;
  color: var(--color-muted);
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
  background-color: var(--color-canvas);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: var(--color-ink);
  font-size: 14px;
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--color-interactive-hover);
}

@media (max-width: 768px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>

<style>
.vxe-table {
  font-size: 13px;
  color: var(--color-ink);
}

.vxe-table .table-header-cell {
  background-color: var(--color-neutral-bg);
  color: var(--color-muted);
  font-weight: 500;
}

.vxe-table .table-cell {
  padding: 8px 12px;
}

.vxe-table .vxe-body--row {
  height: 48px;
}

.vxe-table .vxe-body--column.col--ellipsis {
  height: auto;
  min-height: 48px;
  display: flex;
  align-items: center;
}

.vxe-table .vxe-body--column.col--center {
  text-align: center;
  justify-content: center;
}

.vxe-table .vxe-table--body tr:hover,
.vxe-table .vxe-table--body tr:hover > td {
  background-color: transparent !important;
}

[data-theme="light"] .vxe-table .vxe-table--body tr:hover,
[data-theme="light"] .vxe-table .vxe-table--body tr:hover > td {
  background-color: transparent !important;
}

.vxe-pager {
  margin-top: 16px;
  background-color: var(--color-canvas) !important;
  border-top: 1px solid var(--color-hairline);
}

.vxe-pager * {
  background-color: inherit !important;
}

.vxe-pager .vxe-pager--prev-btn,
.vxe-pager .vxe-pager--next-btn,
.vxe-pager .vxe-pager--jump-prev-btn,
.vxe-pager .vxe-pager--jump-next-btn,
.vxe-pager .vxe-pager--num-btn,
.vxe-pager .vxe-pager--btn-btn,
.vxe-pager .vxe-pager--fulljump,
.vxe-pager .vxe-pager--goto {
  background-color: transparent !important;
  border: none !important;
  color: var(--color-muted) !important;
}

.vxe-pager .vxe-pager--num-btn.is--active {
  background-color: var(--color-interactive) !important;
  color: white !important;
  border-color: var(--color-interactive);
}

.vxe-pager .vxe-pager--sizes .vxe-input,
.vxe-pager--sizes .vxe-input {
  background-color: var(--color-canvas) !important;
  border: 1px solid var(--color-hairline) !important;
}

.vxe-pager .vxe-pager--sizes .vxe-input .vxe-input--inner,
.vxe-pager--sizes .vxe-input .vxe-input--inner {
  background-color: var(--color-canvas) !important;
  color: var(--color-ink) !important;
  border: 1px solid var(--color-hairline) !important;
}

.vxe-pager .vxe-pager--jump-prev-btn,
.vxe-pager .vxe-pager--jump-next-btn,
.vxe-pager .vxe-pager--jump-number {
  background-color: transparent !important;
  color: var(--color-muted) !important;
}

.vxe-pager .vxe-pager--goto {
  background-color: transparent !important;
  color: var(--color-muted) !important;
}

.vxe-pager .vxe-pager--goto .vxe-pager--goto-input,
.vxe-pager .vxe-pager--goto-input {
  background-color: var(--color-canvas) !important;
  border: 1px solid var(--color-hairline) !important;
  color: var(--color-ink) !important;
}

.vxe-pager .vxe-pager--total {
  background-color: transparent !important;
  color: var(--color-muted) !important;
}

.vxe-pager .vxe-pager--sizes {
  background-color: transparent !important;
  color: var(--color-muted) !important;
}

[data-theme="light"] .vxe-pager {
  background-color: var(--color-canvas) !important;
  border-top: 1px solid var(--color-hairline);
}

[data-theme="light"] .vxe-pager .vxe-pager--prev-btn,
[data-theme="light"] .vxe-pager .vxe-pager--next-btn,
[data-theme="light"] .vxe-pager .vxe-pager--jump-prev-btn,
[data-theme="light"] .vxe-pager .vxe-pager--jump-next-btn,
[data-theme="light"] .vxe-pager .vxe-pager--num-btn,
[data-theme="light"] .vxe-pager .vxe-pager--btn-btn,
[data-theme="light"] .vxe-pager .vxe-pager--fulljump,
[data-theme="light"] .vxe-pager .vxe-pager--goto {
  color: var(--color-muted) !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--num-btn.is--active {
  color: var(--color-text-inverse) !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--sizes .vxe-input,
[data-theme="light"] .vxe-pager--sizes .vxe-input {
  background-color: var(--color-text-inverse) !important;
  border: 1px solid #e5e7eb !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--sizes .vxe-input .vxe-input--inner,
[data-theme="light"] .vxe-pager--sizes .vxe-input .vxe-input--inner {
  background-color: var(--color-text-inverse) !important;
  color: var(--color-ink) !important;
  border: 1px solid #e5e7eb !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--goto .vxe-pager--goto-input,
[data-theme="light"] .vxe-pager .vxe-pager--goto-input {
  background-color: var(--color-text-inverse) !important;
  border: 1px solid #e5e7eb !important;
  color: var(--color-ink) !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--total,
[data-theme="light"] .vxe-pager .vxe-pager--sizes {
  color: var(--color-muted) !important;
}
</style>
