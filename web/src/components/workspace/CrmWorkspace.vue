<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  customerV2Api,
  type CustomerV2,
  type CustomerV2ListItem,
  type InvoiceInfo,
  type ShippingAddressV2
} from '../../services/api'
import InvoiceInfoManager from '../common/InvoiceInfoManager.vue'
import ShippingAddressManager from '../common/ShippingAddressManager.vue'

// ==================== 列表相关 ====================
const loading = ref(false)
const customers = ref<CustomerV2ListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterType = ref('')
const stats = ref({ total: 0, active_count: 0, terminal_count: 0, dealer_count: 0 })

// ==================== 弹窗相关 ====================
const showCustomerModal = ref(false)
const showDeleteConfirm = ref(false)
const editingCustomer = ref<CustomerV2 | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)

// ==================== 转移相关 ====================
const showTransferModal = ref(false)
const transferTargetId = ref<string | null>(null)
const transferTargetName = ref<string>('')
const salesUsers = ref<any[]>([])
const selectedSalesUserId = ref<string>('')
const salesUserKeyword = ref('')
const transferLoading = ref(false)

// ==================== 表单数据 ====================
// 第一部分 - 客户基础属性
const customerForm = ref({
  name: '',
  customer_type: 'terminal' as 'terminal' | 'dealer',
  research_group: ''
})

// 第二部分 - 客户联系人信息
const contactForm = ref({
  contact_person: '',
  contact_phone: '',
  contact_email: ''
})

// 第三部分 - 开票信息
const invoiceInfos = ref<InvoiceInfo[]>([])

// 第四部分 - 收货地址
const shippingAddresses = ref<ShippingAddressV2[]>([])

// ==================== 组件引用 ====================
const invoiceManagerRef = ref<InstanceType<typeof InvoiceInfoManager> | null>(null)
const shippingAddressManagerRef = ref<InstanceType<typeof ShippingAddressManager> | null>(null)

// ==================== 常量定义 ====================
const customerTypes = [
  { value: 'terminal', label: '终端' },
  { value: 'dealer', label: '经销商' }
]

const customerTypeMap: Record<string, string> = {
  terminal: '终端',
  dealer: '经销商'
}

const statusMap: Record<string, string> = {
  active: '正常',
  inactive: '停用'
}

// ==================== 计算属性 ====================
const showResearchGroup = computed(() => customerForm.value.customer_type === 'terminal')

const isEditing = computed(() => editingCustomer.value !== null)

// ==================== 列表加载 ====================
const loadCustomers = async () => {
  loading.value = true
  try {
    const res = await customerV2Api.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      customer_type: filterType.value || undefined
    })
    customers.value = res.result?.items || []
    total.value = res.result?.total || 0
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await customerV2Api.getStats()
    stats.value = res.result || { total: 0, active_count: 0, terminal_count: 0, dealer_count: 0 }
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

// ==================== 表单操作 ====================
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

const openCreateCustomer = () => {
  resetCustomerForm()
  showCustomerModal.value = true
}

const openEditCustomer = async (row: CustomerV2ListItem) => {
  try {
    formLoading.value = true
    const res = await customerV2Api.getById(row.id)
    const customer: CustomerV2 = res.result

    editingCustomer.value = customer
    customerForm.value = {
      name: customer.name,
      customer_type: customer.customer_type,
      research_group: customer.research_group || ''
    }
    contactForm.value = {
      contact_person: customer.contact_info?.contact_person || '',
      contact_phone: customer.contact_info?.contact_phone || '',
      contact_email: customer.contact_info?.contact_email || ''
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

// ==================== 保存客户 ====================
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
      contact_info: {
        contact_person: contactForm.value.contact_person?.trim() || undefined,
        contact_phone: contactForm.value.contact_phone?.trim() || undefined,
        contact_email: contactForm.value.contact_email?.trim() || undefined,
      },
      invoice_infos: invoiceInfos.value.map(info => ({
        invoice_title: info.invoice_title,
        invoice_type: info.invoice_type,
        tax_number: info.tax_number,
        bank_name: info.bank_name,
        bank_account: info.bank_account,
        is_default: info.is_default
      })),
      shipping_addresses: shippingAddresses.value.map(addr => ({
        recipient_name: addr.recipient_name,
        recipient_phone: addr.recipient_phone,
        province: addr.province,
        province_code: addr.province_code,
        city: addr.city,
        city_code: addr.city_code,
        district: addr.district,
        address: addr.address,
        is_default: addr.is_default
      }))
    }

    if (editingCustomer.value) {
      await customerV2Api.update(editingCustomer.value.id, customerData)
      window.showToast('客户更新成功', 'success')
    } else {
      await customerV2Api.create(customerData)
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

// ==================== 删除客户 ====================
const confirmDelete = (customerId: string) => {
  deleteTargetId.value = customerId
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await customerV2Api.delete(deleteTargetId.value)
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

// ==================== 转移客户 ====================
const loadSalesUsers = async (keyword?: string) => {
  try {
    const res = await customerV2Api.getSalesUsers(keyword)
    salesUsers.value = res.result || []
  } catch (error) {
    console.error('加载销售员列表失败:', error)
  }
}

const openTransferModal = async (customer: CustomerV2ListItem) => {
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
    await customerV2Api.transfer(transferTargetId.value, selectedSalesUserId.value)
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

// ==================== 开票信息操作 ====================
const handleInvoiceAdd = async (data: InvoiceInfo) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.addInvoiceInfo(editingCustomer.value.id, data)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    invoiceInfos.value = res.result.invoice_infos || []
  } catch (error: any) {
    window.showToast(error.message || '添加开票信息失败', 'error')
    throw error
  }
}

const handleInvoiceUpdate = async (invoiceId: string, data: InvoiceInfo) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.updateInvoiceInfo(editingCustomer.value.id, invoiceId, data)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    invoiceInfos.value = res.result.invoice_infos || []
  } catch (error: any) {
    window.showToast(error.message || '更新开票信息失败', 'error')
    throw error
  }
}

const handleInvoiceDelete = async (invoiceId: string) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.deleteInvoiceInfo(editingCustomer.value.id, invoiceId)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    invoiceInfos.value = res.result.invoice_infos || []
  } catch (error: any) {
    window.showToast(error.message || '删除开票信息失败', 'error')
    throw error
  }
}

const handleInvoiceSetDefault = async (invoiceId: string) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.setDefaultInvoiceInfo(editingCustomer.value.id, invoiceId)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    invoiceInfos.value = res.result.invoice_infos || []
  } catch (error: any) {
    window.showToast(error.message || '设置默认开票信息失败', 'error')
    throw error
  }
}

const handleInvoiceUpdateLocal = (updatedInfos: InvoiceInfo[]) => {
  invoiceInfos.value = updatedInfos
}

// ==================== 收货地址操作 ====================
const handleShippingAdd = async (data: ShippingAddressV2) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.addShippingAddress(editingCustomer.value.id, data)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    shippingAddresses.value = res.result.shipping_addresses || []
  } catch (error: any) {
    window.showToast(error.message || '添加收货地址失败', 'error')
    throw error
  }
}

const handleShippingUpdate = async (addressId: string, data: ShippingAddressV2) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.updateShippingAddress(editingCustomer.value.id, addressId, data)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    shippingAddresses.value = res.result.shipping_addresses || []
  } catch (error: any) {
    window.showToast(error.message || '更新收货地址失败', 'error')
    throw error
  }
}

const handleShippingDelete = async (addressId: string) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.deleteShippingAddress(editingCustomer.value.id, addressId)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    shippingAddresses.value = res.result.shipping_addresses || []
  } catch (error: any) {
    window.showToast(error.message || '删除收货地址失败', 'error')
    throw error
  }
}

const handleShippingSetDefault = async (addressId: string) => {
  if (!editingCustomer.value) return
  try {
    await customerV2Api.setDefaultShippingAddress(editingCustomer.value.id, addressId)
    const res = await customerV2Api.getById(editingCustomer.value.id)
    shippingAddresses.value = res.result.shipping_addresses || []
  } catch (error: any) {
    window.showToast(error.message || '设置默认收货地址失败', 'error')
    throw error
  }
}

const handleShippingUpdateLocal = (updatedAddrs: ShippingAddressV2[]) => {
  shippingAddresses.value = updatedAddrs
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadCustomers()
  loadStats()
})

// 键盘事件
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

// ==================== 表格序号 ====================
const seqMethod = ({ row }: { row: CustomerV2ListItem }) => {
  const index = customers.value.findIndex(c => c.id === row.id)
  return index + 1 + (page.value - 1) * pageSize.value
}

// ==================== 折扣设置 ====================
const openDiscountSettings = (customer: CustomerV2ListItem) => {
  // 通过emit通知父组件进行导航
  // 父组件DashboardLayout会处理导航逻辑
  const event = new CustomEvent('navigate-to-discount', {
    detail: {
      customerId: customer.id,
      customerName: customer.name
    }
  })
  window.dispatchEvent(event)
}
</script>

<template>
  <div class="crm-workspace">
    <!-- 页面标题 -->
    <div class="workspace-header">
      <h2 class="workspace-title">客户管理</h2>
      <button class="primary-btn" @click="openCreateCustomer">新建客户</button>
    </div>

    <!-- 统计卡片 -->
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

    <!-- 筛选区域 -->
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

    <!-- 表格区域 -->
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
            <span class="status-tag" :class="row.status || 'active'">
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
          <h3>{{ isEditing ? '编辑客户' : '新建客户' }}</h3>
          <button class="modal-close" @click="showCustomerModal = false">×</button>
        </div>
        <div class="modal-body">
          <!-- 第一部分：客户基础属性 -->
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>客户名称 <span class="required">*</span></label>
                <input
                  type="text"
                  v-model="customerForm.name"
                  placeholder="请输入客户名称"
                />
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
                <input
                  type="text"
                  v-model="customerForm.research_group"
                  placeholder="请输入课题组信息"
                />
              </div>
              <div class="form-group" v-if="!showResearchGroup"></div>
            </div>
          </div>

          <!-- 第二部分：客户联系人信息 -->
          <div class="form-section">
            <div class="section-title">联系人信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>联系人</label>
                <input
                  type="text"
                  v-model="contactForm.contact_person"
                  placeholder="请输入联系人姓名"
                />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input
                  type="text"
                  v-model="contactForm.contact_phone"
                  placeholder="请输入联系电话"
                />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>电子邮箱</label>
                <input
                  type="email"
                  v-model="contactForm.contact_email"
                  placeholder="请输入电子邮箱"
                />
              </div>
            </div>
          </div>

          <!-- 第三部分：客户财务信息（开票信息） -->
          <div class="form-section">
            <div class="section-title">开票信息</div>
            <InvoiceInfoManager
              ref="invoiceManagerRef"
              :customer-id="editingCustomer?.id || ''"
              :invoice-infos="invoiceInfos"
              :readonly="false"
              @add="handleInvoiceAdd"
              @update="handleInvoiceUpdate"
              @delete="handleInvoiceDelete"
              @set-default="handleInvoiceSetDefault"
              @update:invoiceInfos="handleInvoiceUpdateLocal"
            />
          </div>

          <!-- 第四部分：收货地址 -->
          <div class="form-section">
            <div class="section-title">收货地址</div>
            <ShippingAddressManager
              ref="shippingAddressManagerRef"
              :customer-id="editingCustomer?.id || ''"
              :shipping-addresses="shippingAddresses"
              :readonly="false"
              @add="handleShippingAdd"
              @update="handleShippingUpdate"
              @delete="handleShippingDelete"
              @set-default="handleShippingSetDefault"
              @update:shippingAddresses="handleShippingUpdateLocal"
            />
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
  color: var(--text-primary);
  margin: 0;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--accent-blue);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
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

/* 表头居中 */
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

.type-tag,
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag.terminal {
  background-color: rgba(139, 92, 246, 0.1);
  color: var(--accent-purple);
}

.type-tag.dealer {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.active,
.status-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.inactive {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
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
  position: sticky;
  bottom: 0;
  background-color: var(--bg-card);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
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

.form-group .required {
  color: var(--accent-red);
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

.form-group input::placeholder {
  color: var(--text-muted);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
  cursor: pointer;
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
  cursor: pointer;
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
  cursor: pointer;
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

.transfer-modal {
  max-width: 480px;
}

.transfer-info {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.transfer-info strong {
  color: var(--accent-blue);
}

.sales-user-search {
  margin-bottom: 12px;
}

.sales-user-list {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.sales-user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background-color var(--transition-fast);
}

.sales-user-item:last-child {
  border-bottom: none;
}

.sales-user-item:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

.sales-user-item.selected {
  background-color: rgba(0, 120, 212, 0.1);
  border-left: 3px solid var(--accent-blue);
}

.sales-user-name {
  font-size: 14px;
  color: var(--text-primary);
}

.sales-user-dept {
  font-size: 12px;
  color: var(--text-muted);
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
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
  color: var(--text-primary);
}

.vxe-table .table-header-cell {
  background-color: var(--bg-secondary);
  color: var(--text-muted);
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
  background-color: var(--bg-card) !important;
  border-top: 1px solid var(--border-color);
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
  color: var(--text-secondary) !important;
}

.vxe-pager .vxe-pager--num-btn.is--active {
  background-color: var(--accent-blue) !important;
  color: white !important;
  border-color: var(--accent-blue);
}

.vxe-pager .vxe-pager--sizes .vxe-input,
.vxe-pager--sizes .vxe-input {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
}

.vxe-pager .vxe-pager--sizes .vxe-input .vxe-input--inner,
.vxe-pager--sizes .vxe-input .vxe-input--inner {
  background-color: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color) !important;
}

.vxe-pager .vxe-pager--jump-prev-btn,
.vxe-pager .vxe-pager--jump-next-btn,
.vxe-pager .vxe-pager--jump-number {
  background-color: transparent !important;
  color: var(--text-secondary) !important;
}

.vxe-pager .vxe-pager--goto {
  background-color: transparent !important;
  color: var(--text-secondary) !important;
}

.vxe-pager .vxe-pager--goto .vxe-pager--goto-input,
.vxe-pager .vxe-pager--goto-input {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
}

.vxe-pager .vxe-pager--total {
  background-color: transparent !important;
  color: var(--text-secondary) !important;
}

.vxe-pager .vxe-pager--sizes {
  background-color: transparent !important;
  color: var(--text-secondary) !important;
}

[data-theme="light"] .vxe-pager {
  background-color: #ffffff !important;
  border-top: 1px solid #e5e7eb;
}

[data-theme="light"] .vxe-pager .vxe-pager--prev-btn,
[data-theme="light"] .vxe-pager .vxe-pager--next-btn,
[data-theme="light"] .vxe-pager .vxe-pager--jump-prev-btn,
[data-theme="light"] .vxe-pager .vxe-pager--jump-next-btn,
[data-theme="light"] .vxe-pager .vxe-pager--num-btn,
[data-theme="light"] .vxe-pager .vxe-pager--btn-btn,
[data-theme="light"] .vxe-pager .vxe-pager--fulljump,
[data-theme="light"] .vxe-pager .vxe-pager--goto {
  color: #666666 !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--num-btn.is--active {
  color: #ffffff !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--sizes .vxe-input,
[data-theme="light"] .vxe-pager--sizes .vxe-input {
  background-color: #ffffff !important;
  border: 1px solid #e5e7eb !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--sizes .vxe-input .vxe-input--inner,
[data-theme="light"] .vxe-pager--sizes .vxe-input .vxe-input--inner {
  background-color: #ffffff !important;
  color: #374151 !important;
  border: 1px solid #e5e7eb !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--goto .vxe-pager--goto-input,
[data-theme="light"] .vxe-pager .vxe-pager--goto-input {
  background-color: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  color: #374151 !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--total,
[data-theme="light"] .vxe-pager .vxe-pager--sizes {
  color: #666666 !important;
}
</style>
