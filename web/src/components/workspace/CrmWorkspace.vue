<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  customerApi,
  type CustomerListItem
} from '../../services/api'
import { authApi } from '../../services/api'
import CustomerEditModal from './CustomerEditModal.vue'
import CustomerDetail from './CustomerDetail.vue'
import CustomerClaimModal from './CustomerClaimModal.vue'
import CustomerOrderDefaultsModal from './CustomerOrderDefaultsModal.vue'
import CustomerCreditModal from './CustomerCreditModal.vue'
import CustomerMemberModal from './CustomerMemberModal.vue'

const loading = ref(false)
const customers = ref<CustomerListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterType = ref('')
const filterStatus = ref<number | null>(null)
const filterSalesUserId = ref<number | null>(null)
const filterCreatedAtStart = ref('')
const filterCreatedAtEnd = ref('')

// 弹窗控制
const showEditModal = ref(false)
const showDetailModal = ref(false)
const showClaimModal = ref(false)
const showOrderDefaultsModal = ref(false)
const showCreditModal = ref(false)
const showMemberModal = ref(false)
const currentCustomer = ref<any>(null)
const editMode = ref<'create' | 'edit'>('create')

// 转移弹窗
const showTransferModal = ref(false)
const transferTargetId = ref<string | null>(null)
const transferTargetName = ref<string>('')
const salesUsers = ref<any[]>([])
const selectedSalesUserId = ref<string>('')
const salesUserKeyword = ref('')
const transferLoading = ref(false)

// 删除弹窗
const showDeleteConfirm = ref(false)
const deleteTargetId = ref<string | null>(null)
const deleteLoading = ref(false)

// 导出选中
const selectedRows = ref<CustomerListItem[]>([])

const customerTypeMap: Record<string, string> = {
  terminal: '终端',
  dealer: '经销商'
}

const customerStatusMap: Record<number, string> = {
  1: '正常',
  2: '公共池'
}

const hasActiveFilters = computed(() => {
  return !!(keyword.value || filterType.value || filterStatus.value || filterSalesUserId.value || filterCreatedAtStart.value || filterCreatedAtEnd.value)
})

const loadCustomers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      customer_type: filterType.value || undefined,
      customer_status: filterStatus.value ?? undefined,
      sales_user_id: filterSalesUserId.value ?? undefined,
      created_at_start: filterCreatedAtStart.value || undefined,
      created_at_end: filterCreatedAtEnd.value || undefined
    }
    const res = await customerApi.list(params)
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


const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadCustomers()
}

const handleSearch = () => {
  page.value = 1
  loadCustomers()
}

const resetFilters = () => {
  keyword.value = ''
  filterType.value = ''
  filterStatus.value = null
  filterSalesUserId.value = null
  filterCreatedAtStart.value = ''
  filterCreatedAtEnd.value = ''
  page.value = 1
  loadCustomers()
}

// ==================== 新建/编辑客户 ====================
const openCreateCustomer = () => {
  currentCustomer.value = null
  editMode.value = 'create'
  showEditModal.value = true
}

const openEditCustomer = async (row: CustomerListItem) => {
  try {
    const res = await customerApi.getById(String(row.id))
    currentCustomer.value = res
    editMode.value = 'edit'
    showEditModal.value = true
  } catch (error: any) {
    window.showToast(error.message || '加载客户详情失败', 'error')
  }
}

const onEditSaved = (data?: any) => {
  if (data && data.id && editMode.value === 'edit') {
    const idx = customers.value.findIndex(c => c.id === data.id)
    if (idx !== -1) {
      customers.value[idx] = { ...customers.value[idx], ...data }
    }
  } else {
    loadCustomers()
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
    await customerApi.delete(deleteTargetId.value)
    window.showToast('客户删除成功', 'success')
    customers.value = customers.value.filter(c => c.id !== deleteTargetId.value)
    total.value--
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

// ==================== 转移客户 ====================
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
  if (customer.customer_status === 2) {
    window.showToast('公共池客户不可转移，请先认领', 'warning')
    return
  }
  transferTargetId.value = customer.id
  transferTargetName.value = customer.customer_name
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

// ==================== 弹窗触发 ====================
const showDetail = (row: CustomerListItem) => {
  currentCustomer.value = row
  showDetailModal.value = true
}

const showClaim = (row: CustomerListItem) => {
  currentCustomer.value = row
  showClaimModal.value = true
}

const showOrderDefaults = (row: CustomerListItem) => {
  currentCustomer.value = row
  showOrderDefaultsModal.value = true
}

const showCredit = (row: CustomerListItem) => {
  currentCustomer.value = row
  showCreditModal.value = true
}

const showMember = (row: CustomerListItem) => {
  currentCustomer.value = row
  showMemberModal.value = true
}

const openDiscountSettings = (customer: CustomerListItem) => {
  const event = new CustomEvent('navigate-to-discount', {
    detail: {
      customerId: customer.id,
      customerName: customer.customer_name
    }
  })
  window.dispatchEvent(event)
}

// ==================== 认领成功回调 ====================
const onClaimSuccess = () => {
  loadCustomers()
}

// ==================== 导出 ====================
const handleExport = async () => {
  try {
    const data: any = {}
    if (selectedRows.value.length > 0) {
      data.customer_ids = selectedRows.value.map((r: any) => Number(r.id))
    } else {
      if (filterStatus.value) data.customer_status = filterStatus.value
      if (filterSalesUserId.value) data.sales_user_id = filterSalesUserId.value
      if (filterCreatedAtStart.value) data.created_at_start = filterCreatedAtStart.value
      if (filterCreatedAtEnd.value) data.created_at_end = filterCreatedAtEnd.value
    }
    const blob = await customerApi.exportCustomers(data)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `客户数据_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败', e)
  }
}

// ==================== 格式化函数 ====================
const formatAmount = (val: any) => val != null ? Number(val).toFixed(2) : '0.00'
const formatDate = (val: string | null) => val ? val.substring(0, 10) : '-'

// ==================== 生命周期 ====================
onMounted(() => {
  loadCustomers()
  loadSalesUsers()
})

const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    showEditModal.value = false
    showDetailModal.value = false
    showClaimModal.value = false
    showOrderDefaultsModal.value = false
    showCreditModal.value = false
    showMemberModal.value = false
    closeTransferModal()
    showDeleteConfirm.value = false
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

// checkbox 选择
const checkboxConfig = {
  highlight: true,
  reserve: true
}
const selectChangeEvent = ({ records }: { records: CustomerListItem[] }) => {
  selectedRows.value = records
}
</script>

<template>
  <div class="crm-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">客户管理</h2>
      <div class="header-actions">
        <button class="filter-btn" @click="handleExport" :disabled="!selectedRows.length" v-if="selectedRows.length">
          导出({{ selectedRows.length }}条)
        </button>
        <button class="filter-btn" @click="handleExport" v-else>批量导出</button>
        <button class="primary-btn" @click="openCreateCustomer">新建客户</button>
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
        <select v-model="filterStatus" class="filter-select">
          <option :value="null">全部状态</option>
          <option :value="1">正常</option>
          <option :value="2">公共池</option>
        </select>
        <select v-model="filterType" class="filter-select">
          <option value="">全部类型</option>
          <option value="terminal">终端</option>
          <option value="dealer">经销商</option>
        </select>
        <select v-model="filterSalesUserId" class="filter-select">
          <option :value="null">全部业务员</option>
          <option v-for="user in salesUsers" :key="user.id" :value="Number(user.id)">
            {{ user.full_name || user.username }}
          </option>
        </select>
        <div class="filter-item">
          <input type="date" class="filter-input" v-model="filterCreatedAtStart" placeholder="创建时间从" />
        </div>
        <div class="filter-item">
          <input type="date" class="filter-input" v-model="filterCreatedAtEnd" placeholder="至" />
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
        :data="customers"
        :column-config="{ resizable: true }"
        :seq-config="{ seqMethod: seqMethod }"
        :checkbox-config="checkboxConfig"
        @checkbox-change="selectChangeEvent"
        @checkbox-all="selectChangeEvent"
      >
        <vxe-column type="checkbox" width="40" fixed="left" />
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center col--header-center" />
        <vxe-column field="created_at" title="创建时间" width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </vxe-column>
        <vxe-column field="customer_name" title="客户名称" min-width="200" class-name="col--center col--header-center">
          <template #default="{ row }">
            <button class="btn-link name-link" @click="showDetail(row)">{{ row.customer_name }}</button>
          </template>
        </vxe-column>
        <vxe-column field="sales_user_name" title="业务员" min-width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span v-if="row.customer_status === 2" class="status-tag pool-tag">公共池</span>
            <span v-else>{{ row.sales_user_name || '-' }}</span>
          </template>
        </vxe-column>
        <vxe-column field="member_account" title="会员账号" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ row.member_account || '-' }}
          </template>
        </vxe-column>
        <vxe-column field="customer_status" title="客户状态" min-width="90" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.customer_status === 1 ? 'normal' : 'pool'">
              {{ customerStatusMap[row.customer_status] || '正常' }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="customer_type" title="客户类型" min-width="90" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="type-tag" :class="[row.customer_type, { unknown: !customerTypeMap[row.customer_type] }]">
              {{ customerTypeMap[row.customer_type] || row.customer_type }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="account_balance" title="账户余额" min-width="110" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="amount-text">{{ formatAmount(row.account_balance) }}</span>
          </template>
        </vxe-column>
        <vxe-column field="debt_total" title="欠款总额" min-width="110" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="amount-text">{{ formatAmount(row.debt_total) }}</span>
          </template>
        </vxe-column>
        <vxe-column field="is_overdue" title="是否超账期" min-width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.is_overdue === 1 ? 'danger' : 'success'">
              {{ row.is_overdue === 1 ? '是' : '否' }}
            </span>
          </template>
        </vxe-column>
        <vxe-column field="last_order_time" title="尾单时间" min-width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ formatDate(row.last_order_time) }}
          </template>
        </vxe-column>
        <vxe-column field="total_order_amount" title="成单金额" min-width="120" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="amount-text">{{ formatAmount(row.total_order_amount) }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" min-width="320" fixed="right" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="showDetail(row)">详情</button>
              <template v-if="row.customer_status === 1">
                <button class="btn-link" @click="openEditCustomer(row)">编辑</button>
                <button class="btn-link" @click="showOrderDefaults(row)">订单默认值</button>
                <button class="btn-link" @click="showMember(row)">注册会员</button>
                <button class="btn-link" @click="openDiscountSettings(row)">折扣</button>
                <button class="btn-link" @click="showCredit(row)">账期额度</button>
                <button class="btn-link" @click="openTransferModal(row)">转移</button>
                <button class="btn-link danger" @click="confirmDelete(row.id)">删除</button>
              </template>
              <template v-else-if="row.customer_status === 2">
                <button class="btn-link claim-btn" @click="showClaim(row)">认领</button>
              </template>
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

    <!-- 新建/编辑客户弹窗 -->
    <CustomerEditModal
      v-model:visible="showEditModal"
      :customer-data="currentCustomer"
      :mode="editMode"
      @saved="onEditSaved"
    />

    <!-- 客户详情弹窗 -->
    <CustomerDetail
      v-model:visible="showDetailModal"
      :customer-id="currentCustomer?.id ? Number(currentCustomer.id) : null"
      @edit="openEditCustomer"
      @claim="showClaim"
    />

    <!-- 客户认领弹窗 -->
    <CustomerClaimModal
      v-model:visible="showClaimModal"
      :customer-data="currentCustomer"
      @claim-success="onClaimSuccess"
    />

    <!-- 订单默认值设置弹窗 -->
    <CustomerOrderDefaultsModal
      v-model:visible="showOrderDefaultsModal"
      :customer-data="currentCustomer"
      @saved="loadCustomers"
    />

    <!-- 账期额度设置弹窗 -->
    <CustomerCreditModal
      v-model:visible="showCreditModal"
      :customer-data="currentCustomer"
      @saved="loadCustomers"
    />

    <!-- 注册会员弹窗 -->
    <CustomerMemberModal
      v-model:visible="showMemberModal"
      :customer-data="currentCustomer"
      @saved="loadCustomers"
    />

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
          <button class="modal-close" @click="closeTransferModal">&times;</button>
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.filter-section {
  background-color: var(--color-canvas);
  border-radius: var(--radius-sm);
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
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  box-shadow: var(--shadow-card);
  --vxe-ui-layout-background-color: var(--color-canvas);
}

:deep(.col--header-center .vxe-cell--title) {
  text-align: center;
  justify-content: center;
}

/* 行hover/焦点覆盖 */
:deep(.vxe-body--column.col--actived) {
  background-color: var(--color-canvas) !important;
}

:deep(.vxe-body--row) > td {
  background-color: var(--color-canvas) !important;
}

:deep(.vxe-body--row:hover) > td {
  background-color: var(--color-neutral-bg) !important;
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
  border-radius: var(--radius-xs);
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

.name-link {
  font-weight: 500;
}

.claim-btn {
  color: var(--color-success);
}

.claim-btn:hover {
  background-color: var(--color-success-bg);
}

.type-tag,
.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: var(--radius-xs);
  font-size: 12px;
}

.type-tag.terminal {
  background-color: var(--color-accent-soft);
  color: #c4391a;
}

.type-tag.dealer {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.type-tag.unknown {
  background-color: #d9d9d9;
  color: #666;
}

.status-tag.normal {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-tag.pool {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-tag.danger {
  background-color: var(--color-danger-bg);
  color: var(--color-danger);
}

.status-tag.success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.pool-tag {
  background-color: var(--color-info-bg);
  color: var(--color-interactive);
}

.amount-text {
  font-weight: 500;
}

/* 模态弹窗基础样式 */
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
  border-radius: var(--radius-sm);
  width: 95%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.confirm-modal {
  max-width: 400px;
}

.transfer-modal {
  max-width: 480px;
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
  background-color: rgba(0, 0, 0, 0.06);
  color: var(--color-ink);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--color-ink);
  margin: 0;
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
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
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

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
  background-color: var(--color-danger);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  border-radius: var(--radius-xs);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: var(--color-ink);
  font-size: 14px;
}

@media (max-width: 768px) {
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
.vxe-pager--goto-input {
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
[data-theme="light"] .vxe-pager--goto-input {
  background-color: var(--color-text-inverse) !important;
  border: 1px solid #e5e7eb !important;
  color: var(--color-ink) !important;
}

[data-theme="light"] .vxe-pager .vxe-pager--total,
[data-theme="light"] .vxe-pager .vxe-pager--sizes {
  color: var(--color-muted) !important;
}
</style>