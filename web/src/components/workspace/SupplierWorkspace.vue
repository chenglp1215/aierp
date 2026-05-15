<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { supplierApi, brandApi, type Brand } from '../../services/api'

interface SupplierBrand {
  brand_id: number
  brand_name?: string
  discount: number
  is_priority: boolean
}

interface BankAccount {
  bank_name: string
  account_name: string
  account_no: string
}

interface Supplier {
  id: number
  name: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  address?: string
  bank_account?: BankAccount
  supplied_brands: SupplierBrand[]
  remark?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

interface SupplierFormData {
  name: string
  contact_person: string
  contact_phone: string
  contact_email: string
  address: string
  bank_account: BankAccount
  supplied_brands: SupplierBrand[]
  remark: string
  is_active: boolean
}

const loading = ref(false)
const suppliers = ref<Supplier[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterActive = ref<boolean | ''>('')
const filterBrands = ref<string[]>([])

const showFormModal = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref<Supplier | null>(null)
const editingSupplier = ref<Supplier | null>(null)
const formLoading = ref(false)

const brands = ref<Brand[]>([])

const supplierForm = ref<SupplierFormData>({
  name: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  address: '',
  bank_account: {
    bank_name: '',
    account_name: '',
    account_no: ''
  },
  supplied_brands: [],
  remark: '',
  is_active: true
})

const loadSuppliers = async () => {
  loading.value = true
  try {
    const res = await supplierApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      is_active: filterActive.value === '' ? undefined : filterActive.value,
      brand_ids: filterBrands.value.length > 0 ? filterBrands.value : undefined
    })
    suppliers.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载供应商列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadBrands = async () => {
  try {
    const res = await brandApi.getAll({ is_active: true })
    brands.value = res || []
  } catch (error) {
    console.error('加载品牌列表失败:', error)
  }
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadSuppliers()
}

const handleSearch = () => {
  page.value = 1
  loadSuppliers()
}

const resetFilters = () => {
  keyword.value = ''
  filterActive.value = ''
  filterBrands.value = []
  page.value = 1
  loadSuppliers()
}

const hasActiveFilters = computed(() => !!(keyword.value || filterActive.value !== '' || filterBrands.value.length > 0))

const removeBrandFilter = (brandId: string) => {
  const index = filterBrands.value.indexOf(brandId)
  if (index > -1) {
    filterBrands.value.splice(index, 1)
  }
}

const resetForm = () => {
  supplierForm.value = {
    name: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    bank_account: {
      bank_name: '',
      account_name: '',
      account_no: ''
    },
    supplied_brands: [],
    remark: '',
    is_active: true
  }
  editingSupplier.value = null
}

const openCreate = () => {
  resetForm()
  showFormModal.value = true
}

const openEdit = (supplier: Supplier) => {
  editingSupplier.value = supplier
  supplierForm.value = {
    name: supplier.name,
    contact_person: supplier.contact_person || '',
    contact_phone: supplier.contact_phone || '',
    contact_email: supplier.contact_email || '',
    address: supplier.address || '',
    bank_account: supplier.bank_account || { bank_name: '', account_name: '', account_no: '' },
    supplied_brands: supplier.supplied_brands || [],
    remark: supplier.remark || '',
    is_active: supplier.is_active
  }
  showFormModal.value = true
}

const addBrandRow = () => {
  supplierForm.value.supplied_brands.push({
    brand_id: '',
    discount: 1.0,
    is_priority: false
  })
}

const removeBrandRow = (index: number) => {
  supplierForm.value.supplied_brands.splice(index, 1)
}

const handleSave = async () => {
  if (!supplierForm.value.name?.trim()) {
    window.showToast('请输入供应商名称', 'warning')
    return
  }
  if (supplierForm.value.name.length > 200) {
    window.showToast('供应商名称不能超过200个字符', 'warning')
    return
  }

  // 校验供货品牌
  for (let i = 0; i < supplierForm.value.supplied_brands.length; i++) {
    const brand = supplierForm.value.supplied_brands[i]
    if (!brand.brand_id) {
      window.showToast(`第${i + 1}条供货品牌请选择品牌`, 'warning')
      return
    }
    if (brand.discount < 0 || brand.discount > 1) {
      window.showToast(`第${i + 1}条供货品牌的折扣率必须在0-1之间`, 'warning')
      return
    }
  }

  formLoading.value = true
  try {
    if (editingSupplier.value) {
      await supplierApi.update(editingSupplier.value.id, supplierForm.value)
      window.showToast('供应商更新成功', 'success')
    } else {
      await supplierApi.create(supplierForm.value)
      window.showToast('供应商创建成功', 'success')
    }
    showFormModal.value = false
    loadSuppliers()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = (supplier: Supplier) => {
  deleteTarget.value = supplier
  showDeleteModal.value = true
}

const handleDelete = async () => {
  if (!deleteTarget.value) return
  formLoading.value = true
  try {
    await supplierApi.delete(deleteTarget.value.id)
    window.showToast('供应商删除成功', 'success')
    showDeleteModal.value = false
    deleteTarget.value = null
    loadSuppliers()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleToggleActive = async (supplier: Supplier) => {
  try {
    const newStatus = !supplier.is_active
    await supplierApi.toggleActive(supplier.id, newStatus)
    window.showToast(newStatus ? '供应商已启用' : '供应商已停用', 'success')
    loadSuppliers()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getBrandName = (brandId: string) => {
  const brand = brands.value.find(b => b.id === brandId)
  return brand ? brand.name : brandId
}

onMounted(() => {
  loadSuppliers()
  loadBrands()
})
</script>

<template>
  <div class="supplier-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">供应商管理</h2>
      <button class="primary-btn" @click="openCreate">新建供应商</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索供应商名称..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filterBrands" multiple class="filter-select brand-select" size="1">
          <option value="" disabled>选择品牌</option>
          <option v-for="brand in brands" :key="brand.id" :value="brand.id">{{ brand.name }}</option>
        </select>
        <select v-model="filterActive" class="filter-select">
          <option value="">全部状态</option>
          <option :value="true">启用</option>
          <option :value="false">停用</option>
        </select>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
      <div class="filter-tags" v-if="filterBrands.length > 0">
        <span class="filter-tag" v-for="brandId in filterBrands" :key="brandId">
          {{ getBrandName(brandId) }}
          <button class="tag-close" @click="removeBrandFilter(brandId)">×</button>
        </span>
      </div>
    </div>

    <div class="supplier-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-else-if="suppliers.length === 0" class="empty-state">
        <div class="empty-icon">🏭</div>
        <p>暂无供应商数据</p>
        <button class="primary-btn" @click="openCreate">新建第一个供应商</button>
      </div>
      <div v-else class="supplier-table-wrapper">
        <table class="supplier-table">
          <thead>
            <tr>
              <th>供应商名称</th>
              <th>联系人</th>
              <th>联系电话</th>
              <th>供货品牌</th>
              <th>状态</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="supplier in suppliers" :key="supplier.id">
              <td>{{ supplier.name }}</td>
              <td>{{ supplier.contact_person || '-' }}</td>
              <td>{{ supplier.contact_phone || '-' }}</td>
              <td>
                <div class="brand-tags">
                  <span
                    v-for="(brand, idx) in supplier.supplied_brands"
                    :key="idx"
                    class="brand-tag"
                    :class="{ priority: brand.is_priority }"
                  >
                    {{ getBrandName(brand.brand_id) }}
                    <span v-if="brand.discount < 1" class="discount">({{ (brand.discount * 100).toFixed(0) }}%)</span>
                    <span v-if="brand.is_priority" class="priority-badge">优先</span>
                  </span>
                  <span v-if="!supplier.supplied_brands || supplier.supplied_brands.length === 0" class="text-muted">-</span>
                </div>
              </td>
              <td>
                <span :class="['status-tag', supplier.is_active ? 'active' : 'inactive']">
                  {{ supplier.is_active ? '启用' : '停用' }}
                </span>
              </td>
              <td>{{ formatDate(supplier.updated_at) }}</td>
              <td>
                <div class="action-buttons">
                  <button class="action-btn" @click="openEdit(supplier)">编辑</button>
                  <button class="action-btn" @click="handleToggleActive(supplier)">
                    {{ supplier.is_active ? '停用' : '启用' }}
                  </button>
                  <button class="action-btn danger" @click="confirmDelete(supplier)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <vxe-pager
        v-if="total > 0"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :layouts="['PrevPage', 'JumpNumber', 'NextPage', 'FullJump', 'Sizes', 'Total']"
        @page-change="handlePageChange"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <div class="modal-overlay" v-if="showFormModal" @click.self="showFormModal = false">
      <div class="modal supplier-modal">
        <div class="modal-header">
          <h3>{{ editingSupplier ? '编辑供应商' : '新建供应商' }}</h3>
          <button class="modal-close" @click="showFormModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <h4>基本信息</h4>
            <div class="form-group">
              <label>供应商名称 *</label>
              <input type="text" v-model="supplierForm.name" placeholder="请输入供应商名称（1-200字符）" maxlength="200" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>联系人</label>
                <input type="text" v-model="supplierForm.contact_person" placeholder="联系人姓名" maxlength="100" />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input type="text" v-model="supplierForm.contact_phone" placeholder="联系电话" maxlength="50" />
              </div>
            </div>
            <div class="form-group">
              <label>联系邮箱</label>
              <input type="text" v-model="supplierForm.contact_email" placeholder="联系邮箱" maxlength="200" />
            </div>
            <div class="form-group">
              <label>地址</label>
              <input type="text" v-model="supplierForm.address" placeholder="供应商地址" />
            </div>
          </div>

          <div class="form-section">
            <h4>银行账户信息</h4>
            <div class="form-row">
              <div class="form-group">
                <label>开户行</label>
                <input type="text" v-model="supplierForm.bank_account.bank_name" placeholder="开户行名称" />
              </div>
              <div class="form-group">
                <label>账户名</label>
                <input type="text" v-model="supplierForm.bank_account.account_name" placeholder="账户名" />
              </div>
            </div>
            <div class="form-group">
              <label>账号</label>
              <input type="text" v-model="supplierForm.bank_account.account_no" placeholder="银行账号" />
            </div>
          </div>

          <div class="form-section">
            <h4>供货品牌</h4>
            <div class="brands-table">
              <table>
                <thead>
                  <tr>
                    <th>品牌</th>
                    <th>折扣率</th>
                    <th>优先选择</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(brand, idx) in supplierForm.supplied_brands" :key="idx">
                    <td>
                      <select v-model="brand.brand_id" class="form-select">
                        <option value="">请选择品牌</option>
                        <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type="number"
                        v-model.number="brand.discount"
                        min="0"
                        max="1"
                        step="0.01"
                        class="discount-input"
                        placeholder="1.0"
                      />
                    </td>
                    <td>
                      <input type="checkbox" v-model="brand.is_priority" />
                    </td>
                    <td>
                      <button class="remove-btn" @click="removeBrandRow(idx)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <button class="add-brand-btn" @click="addBrandRow">+ 添加供货品牌</button>
            </div>
          </div>

          <div class="form-section">
            <div class="form-group">
              <label>备注</label>
              <textarea
                v-model="supplierForm.remark"
                placeholder="备注信息"
                rows="2"
                maxlength="500"
              ></textarea>
            </div>
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="supplierForm.is_active" />
                启用供应商
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showFormModal = false">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div class="modal-overlay" v-if="showDeleteModal" @click.self="showDeleteModal = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除供应商 <strong>"{{ deleteTarget?.name }}"</strong> 吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="formLoading">
            {{ formLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.supplier-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
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
  flex-shrink: 0;
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
}

.filter-select.brand-select {
  min-width: 150px;
  max-width: 200px;
  height: auto;
}

.filter-select.brand-select option {
  padding: 4px 8px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: var(--accent-blue);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.tag-close {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0;
  font-size: 14px;
  line-height: 1;
  opacity: 0.8;
}

.tag-close:hover {
  opacity: 1;
}

.filter-btn {
  padding: 8px 16px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
}

.filter-btn.reset-btn {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.supplier-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.supplier-table-wrapper {
  flex: 1;
  overflow: auto;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
}

.supplier-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.supplier-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 500;
  color: var(--text-secondary);
  background-color: var(--bg-secondary);
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

.supplier-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.supplier-table tbody tr:hover {
  background-color: var(--bg-secondary);
}

.brand-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.brand-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.brand-tag.priority {
  background-color: rgba(255, 152, 0, 0.15);
  color: #ff9800;
}

.discount {
  color: var(--text-muted);
  font-size: 11px;
}

.priority-badge {
  background-color: #ff9800;
  color: white;
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 10px;
}

.status-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.status-tag.active {
  background-color: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-tag.inactive {
  background-color: rgba(158, 158, 158, 0.15);
  color: #9e9e9e;
}

.text-muted {
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 10px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.action-btn.danger:hover {
  background-color: #ef5350;
  border-color: #ef5350;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-primary);
  border-radius: 8px;
  width: 600px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.supplier-modal {
  width: 700px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.form-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.form-group input,
.form-group textarea,
.form-select {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.form-group input:focus,
.form-group textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-select {
  cursor: pointer;
}

.checkbox-group {
  margin-top: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}

.brands-table {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.brands-table table {
  width: 100%;
  border-collapse: collapse;
}

.brands-table th,
.brands-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.brands-table th {
  background-color: var(--bg-secondary);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.brands-table td {
  font-size: 13px;
}

.brands-table .discount-input {
  width: 80px;
  text-align: center;
}

.remove-btn {
  padding: 4px 8px;
  background-color: rgba(239, 83, 80, 0.1);
  color: #ef5350;
  border: 1px solid rgba(239, 83, 80, 0.3);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
}

.remove-btn:hover {
  background-color: #ef5350;
  color: white;
  border-color: #ef5350;
}

.add-brand-btn {
  width: 100%;
  padding: 10px;
  background-color: var(--bg-secondary);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  margin-top: 8px;
}

.add-brand-btn:hover {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  padding: 8px 16px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.btn-primary {
  padding: 8px 16px;
  background-color: var(--accent-blue);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 8px 16px;
  background-color: #ef5350;
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-modal {
  width: 400px;
}

.confirm-modal .modal-body p {
  margin: 0;
  color: var(--text-primary);
}
</style>
