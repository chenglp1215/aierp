<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { brandApi, uploadApi, type Brand, type BrandFormData } from '../../services/api'

interface PurchaserCandidate {
  id: string
  full_name: string
  username: string
}

const loading = ref(false)
const brands = ref<Brand[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterActive = ref<boolean | ''>('')

const showFormModal = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref<Brand | null>(null)
const editingBrand = ref<Brand | null>(null)
const formLoading = ref(false)
const imageUploading = ref(false)
const purchaserCandidates = ref<PurchaserCandidate[]>([])

const brandForm = ref<BrandFormData>({
  name: '',
  logo_url: '',
  description: '',
  purchaser_id: '',
  is_active: true
})

const loadBrands = async () => {
  loading.value = true
  try {
    const res: any = await brandApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      is_active: filterActive.value === '' ? undefined : filterActive.value
    })
    brands.value = res.result?.items || res.items || []
    total.value = res.result?.total || res.total || 0
  } catch (error) {
    console.error('加载品牌列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadBrands()
}

const handleSearch = () => {
  page.value = 1
  loadBrands()
}

const resetFilters = () => {
  keyword.value = ''
  filterActive.value = ''
  page.value = 1
  loadBrands()
}

const hasActiveFilters = computed(() => !!(keyword.value || filterActive.value !== ''))

const resetForm = () => {
  brandForm.value = {
    name: '',
    logo_url: '',
    description: '',
    purchaser_id: '',
    is_active: true
  }
  editingBrand.value = null
}

const openCreate = () => {
  resetForm()
  showFormModal.value = true
}

const openEdit = (brand: Brand) => {
  editingBrand.value = brand
  brandForm.value = {
    name: brand.name,
    logo_url: brand.logo_url || '',
    description: brand.description || '',
    purchaser_id: brand.purchaser_id || '',
    is_active: brand.is_active
  }
  showFormModal.value = true
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  imageUploading.value = true
  try {
    const res = await uploadApi.upload(file, file.name)
    brandForm.value.logo_url = res.file_url
  } catch (error: any) {
    window.showToast(error.message || '图片上传失败', 'error')
  } finally {
    imageUploading.value = false
    target.value = ''
  }
}

const handleSave = async () => {
  if (!brandForm.value.name?.trim()) {
    window.showToast('请输入品牌名称', 'warning')
    return
  }
  if (brandForm.value.name.length > 100) {
    window.showToast('品牌名称不能超过100个字符', 'warning')
    return
  }
  if (brandForm.value.description && brandForm.value.description.length > 500) {
    window.showToast('品牌描述不能超过500个字符', 'warning')
    return
  }
  formLoading.value = true
  try {
    if (editingBrand.value) {
      await brandApi.update(editingBrand.value.id, brandForm.value)
      window.showToast('品牌更新成功', 'success')
    } else {
      await brandApi.create(brandForm.value)
      window.showToast('品牌创建成功', 'success')
    }
    showFormModal.value = false
    loadBrands()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDelete = (brand: Brand) => {
  deleteTarget.value = brand
  showDeleteModal.value = true
}

const handleDelete = async () => {
  if (!deleteTarget.value) return
  formLoading.value = true
  try {
    await brandApi.delete(deleteTarget.value.id)
    window.showToast('品牌删除成功', 'success')
    showDeleteModal.value = false
    deleteTarget.value = null
    loadBrands()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleToggleActive = async (brand: Brand) => {
  try {
    const newStatus = !brand.is_active
    await brandApi.toggleActive(brand.id, newStatus)
    window.showToast(newStatus ? '品牌已启用' : '品牌已停用', 'success')
    loadBrands()
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

const loadPurchasers = async () => {
  try {
    const res = await brandApi.getPurchaserCandidates()
    purchaserCandidates.value = res.result || []
  } catch (e) {
    console.error('加载采购人员失败:', e)
  }
}

onMounted(() => {
  loadBrands()
  loadPurchasers()
})
</script>

<template>
  <div class="brand-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">品牌管理</h2>
      <button class="primary-btn" @click="openCreate">新建品牌</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索品牌名称..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filterActive" class="filter-select">
          <option value="">全部状态</option>
          <option :value="true">启用</option>
          <option :value="false">停用</option>
        </select>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
    </div>

    <div class="brand-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-else-if="brands.length === 0" class="empty-state">
        <div class="empty-icon">🏷️</div>
        <p>暂无品牌数据</p>
        <button class="primary-btn" @click="openCreate">新建第一个品牌</button>
      </div>
      <div v-else class="brand-grid">
        <div v-for="brand in brands" :key="brand.id" class="brand-card">
          <div class="brand-card-header">
            <div class="brand-logo">
              <img v-if="brand.logo_url" :src="brand.logo_url" :alt="brand.name" />
              <div v-else class="logo-placeholder">{{ brand.name.charAt(0).toUpperCase() }}</div>
            </div>
            <div class="brand-status">
              <span :class="['status-tag', brand.is_active ? 'active' : 'inactive']">
                {{ brand.is_active ? '启用' : '停用' }}
              </span>
            </div>
          </div>
          <div class="brand-card-body">
            <h3 class="brand-name">{{ brand.name }}</h3>
            <p class="brand-description">{{ brand.description || '暂无描述' }}</p>
            <div v-if="brand.purchaser_name" class="brand-purchaser">
              采购人员: {{ brand.purchaser_name }}
            </div>
            <div class="brand-stats">
              <div class="stat-item">
                <span class="stat-label">商品数量</span>
                <span class="stat-value">{{ brand.product_count || 0 }}</span>
              </div>
            </div>
          </div>
          <div class="brand-card-footer">
            <span class="update-time">更新于 {{ formatDate(brand.updated_at) }}</span>
            <div class="card-actions">
              <button class="action-btn" @click="openEdit(brand)">编辑</button>
              <button class="action-btn" @click="handleToggleActive(brand)">
                {{ brand.is_active ? '停用' : '启用' }}
              </button>
              <button class="action-btn danger" @click="confirmDelete(brand)">删除</button>
            </div>
          </div>
        </div>
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

    <div class="modal-overlay" v-if="showFormModal" @click.self="showFormModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingBrand ? '编辑品牌' : '新建品牌' }}</h3>
          <button class="modal-close" @click="showFormModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>品牌名称 *</label>
            <input type="text" v-model="brandForm.name" placeholder="请输入品牌名称（1-100字符）" maxlength="100" />
          </div>
          <div class="form-group">
            <label>品牌Logo</label>
            <div class="image-upload-area">
              <div class="image-preview" v-if="brandForm.logo_url">
                <img :src="brandForm.logo_url" class="preview-img" />
                <button class="remove-image-btn" @click="brandForm.logo_url = ''">×</button>
              </div>
              <label v-else class="upload-placeholder">
                <input type="file" accept="image/*" @change="handleImageUpload" :disabled="imageUploading" hidden />
                <div class="upload-icon">📷</div>
                <div class="upload-text">{{ imageUploading ? '上传中...' : '点击上传Logo' }}</div>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>品牌描述</label>
            <textarea
              v-model="brandForm.description"
              placeholder="请输入品牌描述（最多500字符）"
              rows="3"
              maxlength="500"
            ></textarea>
          </div>
          <div class="form-group">
            <label>采购人员</label>
            <select v-model="brandForm.purchaser_id" class="form-select">
              <option value="">请选择采购人员</option>
              <option v-for="p in purchaserCandidates" :key="p.id" :value="p.id">
                {{ p.full_name || p.username }}
              </option>
            </select>
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="brandForm.is_active" />
              启用品牌
            </label>
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

    <div class="modal-overlay" v-if="showDeleteModal" @click.self="showDeleteModal = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除品牌 <strong>"{{ deleteTarget?.name }}"</strong> 吗？此操作不可恢复。</p>
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
.brand-workspace {
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

.brand-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  min-height: 300px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0 0 16px 0;
  color: var(--text-muted);
}

.brand-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  flex: 1;
  overflow-y: auto;
}

.brand-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow var(--transition-fast);
}

.brand-card:hover {
  box-shadow: var(--shadow-hover);
}

.brand-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px;
  background-color: var(--bg-secondary);
}

.brand-logo {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.brand-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent-blue);
  color: white;
  font-size: 24px;
  font-weight: 600;
}

.brand-status {
  flex-shrink: 0;
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.inactive {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.brand-card-body {
  padding: 16px;
  flex: 1;
}

.brand-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
  min-height: 39px;
}

.brand-purchaser {
  font-size: 12px;
  color: var(--accent-blue);
  margin-bottom: 12px;
}

.brand-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-blue);
}

.brand-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.update-time {
  font-size: 11px;
  color: var(--text-muted);
}

.card-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.action-btn.danger {
  color: var(--accent-red);
}

.action-btn.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
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
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.confirm-modal {
  max-width: 400px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
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
  display: flex;
  align-items: center;
  justify-content: center;
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
  gap: 16px;
}

.modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
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

.form-group input[type="text"],
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  resize: vertical;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group textarea {
  min-height: 80px;
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.form-select:focus {
  border-color: var(--accent-blue);
}

.checkbox-group {
  flex-direction: row;
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
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.image-upload-area {
  width: 100%;
}

.image-preview {
  position: relative;
  display: inline-block;
}

.preview-img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--accent-red);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-placeholder:hover {
  border-color: var(--accent-blue);
  background-color: rgba(0, 120, 212, 0.05);
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 12px;
  color: var(--text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
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

.vxe-pager {
  margin-top: 16px;
  background-color: var(--bg-card) !important;
  border-radius: var(--radius-lg);
  padding: 12px 16px;
}
</style>

<style>
.vxe-pager {
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

.vxe-pager .vxe-pager--total {
  background-color: transparent !important;
  color: var(--text-secondary) !important;
}
</style>
