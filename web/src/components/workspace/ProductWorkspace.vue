<script setup lang="ts">
defineOptions({ name: 'ProductWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { productApi } from '../../services/api'

interface Product {
  id: string
  product_code: string
  name: string
  price: number
  packaging_spec?: string
  brand?: string
  description?: string
  image_url?: string
  status: string
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const products = ref<Product[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterStatus = ref('')

const showProductModal = ref(false)
const showDeleteConfirm = ref(false)
const editingProduct = ref<Product | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const deleteLoading = ref(false)
const stats = ref({})

const productForm = ref<Partial<Product>>({
  product_code: '',
  name: '',
  price: 0,
  packaging_spec: '',
  brand: '',
  description: '',
  image_url: '',
  status: 'active'
})

const productStatuses = [
  { value: 'active', label: '上架' },
  { value: 'inactive', label: '下架' },
  { value: 'archived', label: '归档' }
]

const columns = [
  { key: 'product_code', label: '商品编号', width: '180px' },
  { key: 'name', label: '商品名称' },
  { key: 'price', label: '价格', width: '100px' },
  { key: 'packaging_spec', label: '包装规格', width: '120px' },
  { key: 'brand', label: '品牌', width: '120px' },
  { key: 'status', label: '状态', width: '80px' }
]

const statusMap: Record<string, string> = {
  active: '上架',
  inactive: '下架',
  archived: '归档'
}

const formatStatus = (status: string) => statusMap[status] || status

const formatPrice = (price: number) => {
  return `¥${price.toFixed(2)}`
}

const loadProducts = async () => {
  loading.value = true
  try {
    const res = await productApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined
    })
    products.value = res.items.map((item: Product) => ({
      ...item,
      status: formatStatus(item.status)
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载商品列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await productApi.getStats()
    stats.value = res.result
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadProducts()
}

const handleSearch = () => {
  page.value = 1
  loadProducts()
}

const hasActiveFilters = computed(() => {
  return !!(keyword.value || filterStatus.value)
})

const resetFilters = () => {
  keyword.value = ''
  filterStatus.value = ''
  page.value = 1
  loadProducts()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetProductForm = () => {
  productForm.value = {
    product_code: '',
    name: '',
    price: 0,
    packaging_spec: '',
    brand: '',
    description: '',
    image_url: '',
    status: 'active'
  }
  editingProduct.value = null
}

const openCreateProduct = () => {
  resetProductForm()
  showProductModal.value = true
}

const openEditProduct = (product: Product) => {
  editingProduct.value = product
  productForm.value = { ...product }
  showProductModal.value = true
}

const confirmDelete = (productId: string) => {
  deleteTargetId.value = productId
  showDeleteConfirm.value = true
}

const handleSaveProduct = async () => {
  if (!productForm.value.name?.trim()) {
    alert('请输入商品名称')
    return
  }
  if (!productForm.value.price || productForm.value.price < 0) {
    alert('请输入有效的商品价格')
    return
  }

  formLoading.value = true
  try {
    if (editingProduct.value) {
      await productApi.update(editingProduct.value.id, productForm.value)
      alert('商品更新成功')
    } else {
      await productApi.create(productForm.value)
      alert('商品创建成功')
    }
    showProductModal.value = false
    loadProducts()
    loadStats()
  } catch (error: any) {
    alert(error.message || '操作失败')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await productApi.delete(deleteTargetId.value)
    alert('商品删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadProducts()
    loadStats()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  loadProducts()
  loadStats()
})
</script>

<template>
  <div class="product-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">商品管理</h2>
      <button class="primary-btn" @click="openCreateProduct">新建商品</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索商品名称、编号、品牌..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in productStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
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
          状态: {{ formatStatus(filterStatus) }}
          <button class="tag-close" @click="filterStatus = ''; handleSearch()">×</button>
        </span>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" :style="{ width: col.width }">
              {{ col.label }}
            </th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="products.length === 0">
            <td :colspan="columns.length + 1" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="product in products" :key="product.id">
            <td>{{ product.product_code }}</td>
            <td>{{ product.name }}</td>
            <td class="price-cell">{{ formatPrice(product.price) }}</td>
            <td>{{ product.packaging_spec || '-' }}</td>
            <td>{{ product.brand || '-' }}</td>
            <td>
              <span class="status-tag" :class="product.status.toLowerCase()">
                {{ product.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openEditProduct(product)">编辑</button>
                <button class="btn-link danger" @click="confirmDelete(product.id)">删除</button>
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
      <button class="pagination-btn" :disabled="products.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showProductModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingProduct ? '编辑商品' : '新建商品' }}</h3>
          <button class="modal-close" @click="showProductModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>商品编号</label>
              <input type="text" v-model="productForm.product_code" placeholder="自动生成或手动输入" />
            </div>
            <div class="form-group">
              <label>商品名称 *</label>
              <input type="text" v-model="productForm.name" placeholder="请输入商品名称" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>商品价格 *</label>
              <input type="number" v-model="productForm.price" placeholder="请输入价格" min="0" step="0.01" />
            </div>
            <div class="form-group">
              <label>包装规格</label>
              <input type="text" v-model="productForm.packaging_spec" placeholder="如: 100g/罐" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>品牌</label>
              <input type="text" v-model="productForm.brand" placeholder="请输入品牌" />
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="productForm.status">
                <option v-for="s in productStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>图片URL</label>
            <input type="text" v-model="productForm.image_url" placeholder="请输入图片URL" />
          </div>
          <div class="form-group">
            <label>简介</label>
            <textarea v-model="productForm.description" placeholder="请输入商品简介" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showProductModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveProduct" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该商品吗？此操作不可恢复。</p>
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
.product-workspace {
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
  transition: all var(--transition-fast);
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

.price-cell {
  color: var(--accent-red);
  font-weight: 500;
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.inactive {
  background-color: rgba(128, 128, 128, 0.1);
  color: var(--text-muted);
}

.status-tag.archived {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

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

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
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
}
</style>
