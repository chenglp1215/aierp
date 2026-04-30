<script setup lang="ts">
defineOptions({ name: 'CrmWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { customerApi } from '../../services/api'

interface ShippingAddress {
  id?: string
  recipient_name: string
  recipient_phone: string
  province?: string
  city?: string
  district?: string
  address: string
  is_default: boolean
  remarks?: string
}

interface Customer {
  id: string
  customer_code: string
  name: string
  customer_type: string
  level: string
  level_raw: string
  status: string
  status_raw: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  province?: string
  city?: string
  address?: string
  industry?: string
  tax_number?: string
  bank_name?: string
  bank_account?: string
  credit_limit: number
  remarks?: string
  shipping_addresses: ShippingAddress[]
  created_at?: string
  updated_at?: string
}

type SpanMethod = (params: { row: any; columnIndex: number }) => { rowspan: number; colspan: number } | void

const loading = ref(false)
const customers = ref<Customer[]>([])
const tableData = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterLevel = ref('')
const filterStatus = ref('')
const filterType = ref('')

const showCustomerModal = ref(false)
const showAddressModal = ref(false)
const showDeleteConfirm = ref(false)
const editingCustomer = ref<Customer | null>(null)
const editingAddress = ref<ShippingAddress | null>(null)
const selectedCustomer = ref<Customer | null>(null)
const selectedCustomerId = ref<string | null>(null)
const deleteTargetId = ref<string | null>(null)
const deleteType = ref<'customer' | 'address'>('customer')
const stats = ref({})
const formLoading = ref(false)
const deleteLoading = ref(false)

const customerForm = ref<Partial<Customer>>({
  name: '',
  customer_type: 'company',
  level: 'normal',
  status: 'normal',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  province: '',
  city: '',
  address: '',
  industry: '',
  tax_number: '',
  bank_name: '',
  bank_account: '',
  credit_limit: 0,
  remarks: ''
})

const addressForm = ref<Partial<ShippingAddress>>({
  recipient_name: '',
  recipient_phone: '',
  province: '',
  city: '',
  district: '',
  address: '',
  is_default: false,
  remarks: ''
})

const customerTypes = [
  { value: 'company', label: '企业' },
  { value: 'individual', label: '个人' },
  { value: 'government', label: '政府' }
]

const customerLevels = [
  { value: 'vip', label: 'VIP' },
  { value: 'normal', label: '普通' },
  { value: 'potential', label: '潜在' }
]

const customerStatuses = [
  { value: 'normal', label: '正常' },
  { value: 'blacklisted', label: '黑名单' },
  { value: 'inactive', label: '未激活' }
]

const getDefaultAddress = (customer: Customer) => {
  if (!customer.shipping_addresses || customer.shipping_addresses.length === 0) {
    return null
  }
  return customer.shipping_addresses.find(addr => addr.is_default) || customer.shipping_addresses[0]
}

const formatDefaultRecipient = (customer: Customer) => {
  const addr = getDefaultAddress(customer)
  return addr?.recipient_name || '-'
}

const formatDefaultPhone = (customer: Customer) => {
  const addr = getDefaultAddress(customer)
  return addr?.recipient_phone || '-'
}

const formatDefaultAddress = (customer: Customer) => {
  const addr = getDefaultAddress(customer)
  if (!addr) return '-'
  return [addr.province, addr.city, addr.district, addr.address].filter(Boolean).join('')
}

const levelMap: Record<string, string> = {
  vip: 'VIP',
  normal: '普通',
  potential: '潜在'
}

const typeMap: Record<string, string> = {
  company: '企业',
  individual: '个人',
  government: '政府'
}

const statusMap: Record<string, string> = {
  normal: '正常',
  blacklisted: '黑名单',
  inactive: '未激活'
}

const formatLevel = (level: string | undefined) => {
  if (!level) return '-'
  const val = typeof level === 'string' ? level.toLowerCase() : String(level).toLowerCase()
  return levelMap[val] || level
}
const formatType = (type: string | undefined) => {
  if (!type) return '-'
  const val = typeof type === 'string' ? type.toLowerCase() : String(type).toLowerCase()
  return typeMap[val] || type
}
const formatStatus = (status: string | undefined) => {
  if (!status) return '-'
  const val = typeof status === 'string' ? status.toLowerCase() : String(status).toLowerCase()
  return statusMap[val] || status
}

const buildTableData = () => {
  const data: any[] = []
  for (const customer of customers.value) {
    const addr = getDefaultAddress(customer)
    data.push({
      _id: customer.id,
      ...customer,
      default_recipient: addr?.recipient_name || '-',
      default_phone: addr?.recipient_phone || '-',
      default_address: formatDefaultAddress(customer),
      address_count: customer.shipping_addresses?.length || 0,
      isFirst: true,
      rowspan: 1
    })
  }
  tableData.value = data
}

const seqMethod = ({ row }: { row: any }) => {
  const firstRows = tableData.value.filter(r => r.isFirst)
  return firstRows.findIndex(r => r._id === row._id) + 1 + (page.value - 1) * pageSize.value
}

const loadCustomers = async () => {
  loading.value = true
  try {
    const res = await customerApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      level: filterLevel.value || undefined,
      status: filterStatus.value || undefined,
      customer_type: filterType.value || undefined
    })
    customers.value = res.items.map((item: any) => ({
      ...item,
      customer_type: formatType(item.customer_type),
      level: formatLevel(item.level),
      level_raw: (item.level || '').toString().toLowerCase(),
      status: formatStatus(item.status),
      status_raw: (item.status || '').toString().toLowerCase()
    }))
    total.value = res.total
    buildTableData()
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await customerApi.getStats()
    stats.value = res.result
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

const hasActiveFilters = computed(() => {
  return !!(keyword.value || filterLevel.value || filterStatus.value || filterType.value)
})

const resetFilters = () => {
  keyword.value = ''
  filterLevel.value = ''
  filterStatus.value = ''
  filterType.value = ''
  page.value = 1
  loadCustomers()
}

const resetCustomerForm = () => {
  customerForm.value = {
    name: '',
    customer_type: 'company',
    level: 'normal',
    status: 'normal',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    province: '',
    city: '',
    address: '',
    industry: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    credit_limit: 0,
    remarks: ''
  }
  editingCustomer.value = null
}

const resetAddressForm = () => {
  addressForm.value = {
    recipient_name: '',
    recipient_phone: '',
    province: '',
    city: '',
    district: '',
    address: '',
    is_default: false,
    remarks: ''
  }
  editingAddress.value = null
}

const openCreateCustomer = () => {
  resetCustomerForm()
  showCustomerModal.value = true
}

const openEditCustomer = (row: any) => {
  const customer = customers.value.find(c => c.id === row.id)
  if (!customer) return
  editingCustomer.value = customer
  customerForm.value = { ...customer }
  showCustomerModal.value = true
}

const openAddressModal = async (row: any) => {
  const customer = customers.value.find(c => c.id === row.id)
  if (!customer) return
  selectedCustomer.value = customer
  selectedCustomerId.value = customer.id
  resetAddressForm()
  showAddressModal.value = true
}

const openEditAddress = (address: ShippingAddress) => {
  editingAddress.value = address
  addressForm.value = { ...address }
}

const confirmDelete = (type: 'customer' | 'address', customerId: string, addressId?: string) => {
  deleteType.value = type
  if (type === 'address' && addressId) {
    deleteTargetId.value = addressId
  } else {
    deleteTargetId.value = customerId
  }
  showDeleteConfirm.value = true
}

const handleSaveCustomer = async () => {
  if (!customerForm.value.name?.trim()) {
    window.showToast('请输入客户名称', 'warning')
    return
  }

  formLoading.value = true
  try {
    if (editingCustomer.value) {
      await customerApi.update(editingCustomer.value.id, customerForm.value)
      window.showToast('客户更新成功', 'success')
      const index = customers.value.findIndex(c => c.id === editingCustomer.value!.id)
      if (index !== -1) {
        const updated = {
          ...customers.value[index],
          ...customerForm.value,
          customer_type: formatType(customerForm.value.customer_type || ''),
          level: formatLevel(customerForm.value.level || ''),
          level_raw: (customerForm.value.level || '').toString().toLowerCase(),
          status: formatStatus(customerForm.value.status || ''),
          status_raw: (customerForm.value.status || '').toString().toLowerCase()
        }
        customers.value[index] = updated
      }
    } else {
      await customerApi.create(customerForm.value)
      window.showToast('客户创建成功', 'success')
      loadCustomers()
    }
    showCustomerModal.value = false
    buildTableData()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleSaveAddress = async () => {
  if (!addressForm.value.recipient_name?.trim() || !addressForm.value.recipient_phone?.trim() || !addressForm.value.address?.trim()) {
    window.showToast('请填写完整的收货信息', 'warning')
    return
  }

  formLoading.value = true
  try {
    if (editingAddress.value?.id && selectedCustomerId.value) {
      await customerApi.updateShippingAddress(selectedCustomerId.value, editingAddress.value.id, addressForm.value)
      window.showToast('收货地址更新成功', 'success')
    } else if (selectedCustomerId.value) {
      await customerApi.addShippingAddress(selectedCustomerId.value, addressForm.value)
      window.showToast('收货地址添加成功', 'success')
    }
    resetAddressForm()
    editingAddress.value = null
    const custIndex = customers.value.findIndex(c => c.id === selectedCustomerId.value)
    if (custIndex !== -1) {
      loadCustomers()
      const updated = customers.value.find(c => c.id === selectedCustomerId.value)
      if (updated) {
        selectedCustomer.value = updated
      }
    }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    if (deleteType.value === 'customer') {
      await customerApi.delete(deleteTargetId.value)
      window.showToast('客户删除成功', 'success')
      customers.value = customers.value.filter(c => c.id !== deleteTargetId.value)
      total.value--
    } else if (selectedCustomerId.value) {
      await customerApi.deleteShippingAddress(selectedCustomerId.value, deleteTargetId.value)
      window.showToast('收货地址删除成功', 'success')
      const custIndex = customers.value.findIndex(c => c.id === selectedCustomerId.value)
      if (custIndex !== -1) {
        loadCustomers()
        const updated = customers.value.find(c => c.id === selectedCustomerId.value)
        if (updated) {
          selectedCustomer.value = updated
        }
      }
    }
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadStats()
    buildTableData()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const handleSetDefaultAddress = async (addressId: string) => {
  if (!selectedCustomerId.value) return

  try {
    await customerApi.setDefaultShippingAddress(selectedCustomerId.value, addressId)
    window.showToast('默认地址设置成功', 'success')
    const custIndex = customers.value.findIndex(c => c.id === selectedCustomerId.value)
    if (custIndex !== -1) {
      loadCustomers()
      const updated = customers.value.find(c => c.id === selectedCustomerId.value)
      if (updated) {
        selectedCustomer.value = updated
      }
    }
  } catch (error: any) {
    window.showToast(error.message || '设置失败', 'error')
  }
}

const handleCancelAddressEdit = () => {
  resetAddressForm()
  editingAddress.value = null
}

const closeAddressModal = () => {
  showAddressModal.value = false
  selectedCustomer.value = null
  selectedCustomerId.value = null
  resetAddressForm()
  editingAddress.value = null
}

onMounted(() => {
  loadCustomers()
  loadStats()
})
</script>

<template>
  <div class="crm-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">客户管理</h2>
      <button class="primary-btn" @click="openCreateCustomer">新建客户</button>
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
        <div class="filter-item">
          <select class="filter-select" v-model="filterType" @change="handleSearch">
            <option value="">全部类型</option>
            <option v-for="t in customerTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterLevel" @change="handleSearch">
            <option value="">全部级别</option>
            <option v-for="l in customerLevels" :key="l.value" :value="l.value">{{ l.label }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in customerStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
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
        :data="tableData"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: seqMethod }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column field="customer_code" title="客户编码" width="140" class-name="col--center" />
        <vxe-column field="name" title="客户名称" min-width="180" />
        <vxe-column field="default_recipient" title="收货人" width="100" class-name="col--center" />
        <vxe-column field="default_phone" title="联系电话" width="130" class-name="col--center" />
        <vxe-column field="default_address" title="默认收货地址" min-width="200" show-overflow />
        <vxe-column field="level" title="客户级别" width="100" class-name="col--center">
          <template #default="{ row }">
            <span class="level-tag" :class="row.level_raw">{{ row.level }}</span>
          </template>
        </vxe-column>
        <vxe-column field="status" title="状态" width="80" class-name="col--center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status_raw">{{ row.status }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="280" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="openEditCustomer(row)">编辑</button>
              <button class="btn-link highlight" @click="openAddressModal(row)">
                收货地址 ({{ row.address_count }})
              </button>
              <button class="btn-link danger" @click="confirmDelete('customer', row.id)">删除</button>
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

    <div class="modal-overlay" v-if="showCustomerModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingCustomer ? '编辑客户' : '新建客户' }}</h3>
          <button class="modal-close" @click="showCustomerModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>客户名称 *</label>
              <input type="text" v-model="customerForm.name" placeholder="请输入客户名称" />
            </div>
            <div class="form-group">
              <label>客户类型</label>
              <select v-model="customerForm.customer_type">
                <option v-for="t in customerTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>客户级别</label>
              <select v-model="customerForm.level">
                <option v-for="l in customerLevels" :key="l.value" :value="l.value">{{ l.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>客户状态</label>
              <select v-model="customerForm.status">
                <option v-for="s in customerStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>联系人</label>
              <input type="text" v-model="customerForm.contact_person" placeholder="请输入联系人" />
            </div>
            <div class="form-group">
              <label>联系电话</label>
              <input type="text" v-model="customerForm.contact_phone" placeholder="请输入联系电话" />
            </div>
          </div>
          <div class="form-group">
            <label>电子邮箱</label>
            <input type="email" v-model="customerForm.contact_email" placeholder="请输入电子邮箱" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>省份</label>
              <input type="text" v-model="customerForm.province" placeholder="请输入省份" />
            </div>
            <div class="form-group">
              <label>城市</label>
              <input type="text" v-model="customerForm.city" placeholder="请输入城市" />
            </div>
          </div>
          <div class="form-group">
            <label>详细地址</label>
            <input type="text" v-model="customerForm.address" placeholder="请输入详细地址" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>行业</label>
              <input type="text" v-model="customerForm.industry" placeholder="请输入行业" />
            </div>
            <div class="form-group">
              <label>税号</label>
              <input type="text" v-model="customerForm.tax_number" placeholder="请输入税号" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>开户银行</label>
              <input type="text" v-model="customerForm.bank_name" placeholder="请输入开户银行" />
            </div>
            <div class="form-group">
              <label>银行账号</label>
              <input type="text" v-model="customerForm.bank_account" placeholder="请输入银行账号" />
            </div>
          </div>
          <div class="form-group">
            <label>信用额度</label>
            <input type="number" v-model="customerForm.credit_limit" placeholder="请输入信用额度" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="customerForm.remarks" placeholder="请输入备注" rows="3"></textarea>
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

    <div class="modal-overlay" v-if="showAddressModal" @click.self="closeAddressModal">
      <div class="modal address-modal">
        <div class="modal-header">
          <h3>{{ selectedCustomer?.name }} - 收货地址管理</h3>
          <button class="modal-close" @click="closeAddressModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="address-form-section">
            <h4>{{ editingAddress?.id ? '编辑收货地址' : '添加收货地址' }}</h4>
            <div class="address-form">
              <div class="form-row">
                <div class="form-group">
                  <label>收货人姓名 *</label>
                  <input type="text" v-model="addressForm.recipient_name" placeholder="请输入收货人姓名" />
                </div>
                <div class="form-group">
                  <label>收货电话 *</label>
                  <input type="text" v-model="addressForm.recipient_phone" placeholder="请输入收货电话" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>省份</label>
                  <input type="text" v-model="addressForm.province" placeholder="请输入省份" />
                </div>
                <div class="form-group">
                  <label>城市</label>
                  <input type="text" v-model="addressForm.city" placeholder="请输入城市" />
                </div>
                <div class="form-group">
                  <label>区县</label>
                  <input type="text" v-model="addressForm.district" placeholder="请输入区县" />
                </div>
              </div>
              <div class="form-group">
                <label>详细地址 *</label>
                <input type="text" v-model="addressForm.address" placeholder="请输入详细地址" />
              </div>
              <div class="form-group">
                <label>备注</label>
                <input type="text" v-model="addressForm.remarks" placeholder="请输入备注" />
              </div>
              <div class="form-group checkbox-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="addressForm.is_default" />
                  <span>设为默认地址</span>
                </label>
              </div>
              <div class="form-actions">
                <button class="btn-secondary" @click="handleCancelAddressEdit" v-if="editingAddress">取消编辑</button>
                <button class="btn-primary" @click="handleSaveAddress" :disabled="formLoading">
                  {{ formLoading ? '保存中...' : (editingAddress?.id ? '更新地址' : '添加地址') }}
                </button>
              </div>
            </div>
          </div>

          <div class="address-list-section">
            <h4>收货地址列表 ({{ selectedCustomer?.shipping_addresses?.length || 0 }})</h4>
            <div class="address-list" v-if="selectedCustomer?.shipping_addresses?.length">
              <div class="address-item" v-for="addr in selectedCustomer?.shipping_addresses" :key="addr.id">
                <div class="address-info">
                  <div class="address-main">
                    <span class="recipient">{{ addr.recipient_name }}</span>
                    <span class="phone">{{ addr.recipient_phone }}</span>
                    <span class="default-tag" v-if="addr.is_default">默认</span>
                  </div>
                  <div class="address-detail">
                    {{ [addr.province, addr.city, addr.district, addr.address].filter(Boolean).join('') }}
                  </div>
                  <div class="address-remarks" v-if="addr.remarks">
                    备注: {{ addr.remarks }}
                  </div>
                </div>
                <div class="address-actions">
                  <button class="btn-link" v-if="!addr.is_default" @click="handleSetDefaultAddress(addr.id!)">设为默认</button>
                  <button class="btn-link" @click="openEditAddress(addr)">编辑</button>
                  <button class="btn-link danger" @click="confirmDelete('address', selectedCustomer!.id, addr.id)">删除</button>
                </div>
              </div>
            </div>
            <div class="empty-address" v-else>
              暂无收货地址，请添加
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除{{ deleteType === 'customer' ? '该客户' : '该收货地址' }}吗？此操作不可恢复。</p>
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

.btn-link.highlight {
  color: var(--accent-purple);
  font-weight: 500;
}

.btn-link.highlight:hover {
  background-color: rgba(139, 92, 246, 0.1);
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.level-tag,
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.level-tag.vip {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.level-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.level-tag.potential {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

.status-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.blacklisted {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.status-tag.inactive {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
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
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.address-modal {
  max-width: 800px;
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

.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.address-form-section {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
}

.address-form-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.address-list-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.address-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.address-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.address-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.address-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.recipient {
  font-weight: 500;
  color: var(--text-primary);
}

.phone {
  color: var(--text-secondary);
}

.default-tag {
  padding: 2px 6px;
  background-color: var(--accent-blue);
  color: white;
  font-size: 11px;
  border-radius: 3px;
}

.address-detail {
  font-size: 13px;
  color: var(--text-muted);
}

.address-remarks {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

.address-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.empty-address {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }

  .address-modal {
    max-width: 95%;
  }

  .address-item {
    flex-direction: column;
    gap: 12px;
  }

  .address-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
