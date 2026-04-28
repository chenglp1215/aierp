<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { productApi, uploadApi, type Product, type ProductSpec, type ProductFormData, type ProductSpecFormData } from '../../services/api'

const loading = ref(false)
const products = ref<Product[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const expandedProducts = ref<Set<string>>(new Set())
const stats = ref({ total: 0, total_stock: 0, total_specs: 0 })

const showProductModal = ref(false)
const showSpecModal = ref(false)
const showDeleteConfirm = ref(false)
const showStockDetail = ref(false)
const editingProduct = ref<Product | null>(null)
const editingSpec = ref<ProductSpec | null>(null)
const selectedSpecForStock = ref<ProductSpec | null>(null)
const deleteTargetId = ref<string | null>(null)
const deleteTargetType = ref<'product' | 'spec'>('product')
const formLoading = ref(false)
const deleteLoading = ref(false)
const imageUploading = ref(false)
const showActiveOnly = ref(false)

const productForm = ref<ProductFormData>({
  product_code: '',
  name: '',
  image_url: '',
  brand: '',
  category: '',
  tax_code: ''
})

const specForm = ref<ProductSpecFormData>({
  spec_code: '',
  packaging: '',
  sales_spec: '',
  price: 0,
  cas_number: '',
  is_active: true
})

const productFormRef = ref<HTMLFormElement | null>(null)
const specFormRef = ref<HTMLFormElement | null>(null)

const specColumns = [
  { key: 'spec_code', label: '规格编号', width: '140px' },
  { key: 'packaging', label: '包装', width: '100px' },
  { key: 'sales_spec', label: '销售规格', width: '120px' },
  { key: 'price', label: '价格', width: '100px' },
  { key: 'cas_number', label: 'CAS号', width: '100px' },
  { key: 'stock', label: '库存', width: '80px' },
  { key: 'is_active', label: '有效', width: '60px' }
]

const stockStatusMap: Record<string, { label: string; class: string }> = {
  normal: { label: '正常', class: 'normal' },
  low_stock: { label: '库存不足', class: 'low-stock' },
  out_of_stock: { label: '缺货', class: 'out-of-stock' },
  overstock: { label: '库存过剩', class: 'overstock' }
}

const formatPrice = (price: number) => `¥${price.toFixed(2)}`

const formatStockStatus = (status: string | undefined) => {
  if (!status) return '-'
  const info = stockStatusMap[status]
  return info ? info.label : status
}

const getStockStatusClass = (status: string | undefined) => {
  if (!status) return ''
  const info = stockStatusMap[status]
  return info ? info.class : ''
}

const toggleExpand = (productId: string) => {
  if (expandedProducts.value.has(productId)) {
    expandedProducts.value.delete(productId)
  } else {
    expandedProducts.value.add(productId)
  }
}

const isExpanded = (productId: string) => expandedProducts.value.has(productId)

const isAllExpanded = ref(true)

const toggleAll = () => {
  if (isAllExpanded.value) {
    expandedProducts.value.clear()
  } else {
    products.value.forEach(p => expandedProducts.value.add(p.id))
  }
  isAllExpanded.value = !isAllExpanded.value
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  imageUploading.value = true
  try {
    const res = await uploadApi.upload(file, file.name)
    productForm.value.image_url = res.file_url
  } catch (error: any) {
    window.showToast(error.message || '图片上传失败', 'error')
  } finally {
    imageUploading.value = false
    target.value = ''
  }
}

const loadProducts = async () => {
  loading.value = true
  try {
    const res = await productApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined
    })
    products.value = res.items
    total.value = res.total
    if (isAllExpanded.value) {
      products.value.forEach(p => expandedProducts.value.add(p.id))
    }
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

const resetFilters = () => {
  keyword.value = ''
  page.value = 1
  loadProducts()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const hasActiveFilters = computed(() => !!keyword.value)

const resetProductForm = () => {
  productForm.value = { product_code: '', name: '', image_url: '', brand: '', category: '', tax_code: '' }
  editingProduct.value = null
}

const openCreateProduct = () => {
  resetProductForm()
  showProductModal.value = true
}

const openEditProduct = (product: Product) => {
  editingProduct.value = product
  productForm.value = {
    product_code: product.product_code,
    name: product.name,
    image_url: product.image_url,
    brand: product.brand || '',
    category: product.category || '',
    tax_code: product.tax_code || ''
  }
  showProductModal.value = true
}

const handleSaveProduct = async () => {
  if (!productForm.value.name?.trim()) {
    window.showToast('请输入商品名称', 'warning')
    return
  }
  formLoading.value = true
  try {
    if (editingProduct.value) {
      await productApi.update(editingProduct.value.id, productForm.value)
      window.showToast('商品更新成功', 'success')
      // 直接更新列表中对应项
      const index = products.value.findIndex(p => p.id === editingProduct.value!.id)
      if (index !== -1) {
        products.value[index] = {
          ...products.value[index],
          ...productForm.value
        }
      }
    } else {
      await productApi.create(productForm.value)
      window.showToast('商品创建成功', 'success')
      loadProducts()
    }
    showProductModal.value = false
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDeleteProduct = (productId: string) => {
  deleteTargetId.value = productId
  deleteTargetType.value = 'product'
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  deleteLoading.value = true
  try {
    if (deleteTargetType.value === 'product') {
      await productApi.delete(deleteTargetId.value)
      window.showToast('商品删除成功', 'success')
      // 直接从列表中移除
      products.value = products.value.filter(p => p.id !== deleteTargetId.value)
      total.value--
    } else {
      await productApi.deleteSpec(deleteTargetId.value)
      window.showToast('规格删除成功', 'success')
      // 从对应商品的 specs 中移除
      for (const product of products.value) {
        if (product.specs) {
          const specIndex = product.specs.findIndex(s => s.id === deleteTargetId.value)
          if (specIndex !== -1) {
            product.specs.splice(specIndex, 1)
            break
          }
        }
      }
    }
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const resetSpecForm = () => {
  specForm.value = {
    spec_code: '',
    packaging: '',
    sales_spec: '',
    price: 0,
    cas_number: '',
    is_active: true
  }
  editingSpec.value = null
}

const openCreateSpec = (productId: string) => {
  resetSpecForm()
  editingSpec.value = { id: productId } as ProductSpec
  showSpecModal.value = true
}

const openEditSpec = (spec: ProductSpec) => {
  editingSpec.value = spec
  specForm.value = {
    spec_code: spec.spec_code,
    packaging: spec.packaging,
    sales_spec: spec.sales_spec,
    price: spec.price,
    cas_number: spec.cas_number,
    is_active: spec.is_active
  }
  showSpecModal.value = true
}

const confirmDeleteSpec = (specId: string) => {
  deleteTargetId.value = specId
  deleteTargetType.value = 'spec'
  showDeleteConfirm.value = true
}

const handleSaveSpec = async () => {
  if (!specForm.value.price || specForm.value.price < 0) {
    window.showToast('请输入有效的价格', 'warning')
    return
  }
  if (!editingSpec.value?.product_id && !editingSpec.value?.id) {
    window.showToast('无效的商品关联', 'warning')
    return
  }
  formLoading.value = true
  try {
    const productId = editingSpec.value!.product_id || editingSpec.value!.id
    if (editingSpec.value && 'spec_code' in editingSpec.value) {
      // 编辑已有规格
      const res = await productApi.updateSpec(editingSpec.value.id, specForm.value)
      window.showToast('规格更新成功', 'success')
      // 直接更新列表中对应规格
      for (const product of products.value) {
        if (product.specs) {
          const specIndex = product.specs.findIndex(s => s.id === editingSpec.value!.id)
          if (specIndex !== -1) {
            product.specs[specIndex] = {
              ...product.specs[specIndex],
              ...specForm.value
            }
            break
          }
        }
      }
    } else {
      // 新建规格
      await productApi.createSpec(productId!, specForm.value)
      window.showToast('规格创建成功', 'success')
      loadProducts()
    }
    showSpecModal.value = false
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleToggleSpecActive = async (spec: ProductSpec) => {
  const newStatus = !spec.is_active
  try {
    await productApi.toggleSpecActive(spec.id, newStatus)
    window.showToast(`规格已${newStatus ? '激活' : '停用'}`, 'success')
    // 直接更新规格的 is_active 状态
    for (const product of products.value) {
      if (product.specs) {
        const specItem = product.specs.find(s => s.id === spec.id)
        if (specItem) {
          specItem.is_active = newStatus
          break
        }
      }
    }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  }
}

const openStockDetail = (spec: ProductSpec) => {
  selectedSpecForStock.value = spec
  showStockDetail.value = true
}

const getFilteredSpecs = (specs: ProductSpec[]) => {
  if (showActiveOnly.value) {
    return specs.filter(s => s.is_active)
  }
  return specs
}

onMounted(() => {
  products.value.forEach(p => expandedProducts.value.add(p.id))
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
            placeholder="搜索商品名称、编号..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="resetFilters" v-if="hasActiveFilters">重置</button>
      </div>
    </div>

    <div class="table-section">
      <div class="table-toolbar">
        <label class="checkbox-label">
          <input type="checkbox" v-model="showActiveOnly" />
          <span class="toggle-switch"></span>
          <span>只查看有效</span>
        </label>
        <button class="toggle-all-btn" @click="toggleAll">
          {{ isAllExpanded ? '全部收起' : '全部展开' }}
        </button>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 40px"></th>
            <th style="width: 140px">商品编号</th>
            <th style="width: 200px">商品名称</th>
            <th style="width: 80px">品牌</th>
            <th style="width: 80px">分类</th>
            <th style="width: 100px">税务编码</th>
            <th style="width: 80px">规格数</th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr>
              <td colspan="8" class="loading-cell">加载中...</td>
            </tr>
          </template>
          <template v-else-if="products.length === 0">
            <tr>
              <td colspan="8" class="empty-cell">暂无数据</td>
            </tr>
          </template>
          <template v-else>
            <template v-for="product in products" :key="product.id">
              <tr class="product-row" :class="{ expanded: isExpanded(product.id) }">
                <td class="expand-cell">
                  <button class="expand-btn" @click="toggleExpand(product.id)">
                    <span class="expand-icon" :class="{ rotated: isExpanded(product.id) }">▶</span>
                  </button>
                </td>
                <td class="code-cell">{{ product.product_code }}</td>
                <td class="name-cell">
                  <span class="product-name">{{ product.name }}</span>
                </td>
                <td>{{ product.brand || '-' }}</td>
                <td>{{ product.category || '-' }}</td>
                <td>{{ product.tax_code || '-' }}</td>
                <td class="spec-count-cell">
                  <span class="spec-badge">{{ product.specs?.length || 0 }}</span>
                </td>
                <td class="actions-cell">
                  <button class="btn-link" @click="openCreateSpec(product.id)">添加规格</button>
                  <button class="btn-link" @click="openEditProduct(product)">编辑</button>
                  <button class="btn-link danger" @click="confirmDeleteProduct(product.id)">删除</button>
                </td>
              </tr>
              <tr v-if="isExpanded(product.id)" class="spec-row">
                <td colspan="8" class="spec-cell">
                  <div class="spec-table-wrapper">
                    <table class="spec-table">
                      <thead>
                        <tr>
                          <th v-for="col in specColumns" :key="col.key" :style="{ width: col.width }">
                            {{ col.label }}
                          </th>
                          <th style="width: 140px">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-if="!product.specs || product.specs.length === 0">
                          <td :colspan="specColumns.length + 1" class="empty-spec-cell">
                            暂无规格，点击"添加规格"创建
                          </td>
                        </tr>
                        <tr v-for="spec in getFilteredSpecs(product.specs)" :key="spec.id" :class="{ inactive: !spec.is_active }">
                          <td>{{ spec.spec_code }}</td>
                          <td>{{ spec.packaging || '-' }}</td>
                          <td>{{ spec.sales_spec || '-' }}</td>
                          <td class="price-cell">{{ formatPrice(spec.price) }}</td>
                          <td>{{ spec.cas_number || '-' }}</td>
                          <td>
                            <span class="stock-link" @click="openStockDetail(spec)">{{ spec.stock_quantity || 0 }}</span>
                          </td>
                          <td>
                            <span class="active-tag" :class="{ active: spec.is_active }">
                              {{ spec.is_active ? '有效' : '无效' }}
                            </span>
                          </td>
                          <td class="spec-actions">
                            <button class="btn-link" @click="openEditSpec(spec)">编辑</button>
                            <button class="btn-link" @click="handleToggleSpecActive(spec)">
                              {{ spec.is_active ? '停用' : '激活' }}
                            </button>
                            <button class="btn-link danger" @click="confirmDeleteSpec(spec.id)">删除</button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="products.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showProductModal" @click.self="showProductModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingProduct ? '编辑商品' : '新建商品' }}</h3>
          <button class="modal-close" @click="showProductModal = false">×</button>
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
              <label>品牌</label>
              <input type="text" v-model="productForm.brand" placeholder="品牌名称" />
            </div>
            <div class="form-group">
              <label>分类</label>
              <input type="text" v-model="productForm.category" placeholder="商品分类" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>税务编码</label>
              <input type="text" v-model="productForm.tax_code" placeholder="税务编码" />
            </div>
          </div>
          <div class="form-group">
            <label>商品图片</label>
            <div class="image-upload-area">
              <div class="image-preview" v-if="productForm.image_url">
                <img :src="productForm.image_url" class="preview-img" />
                <button class="remove-image-btn" @click="productForm.image_url = ''">×</button>
              </div>
              <label v-else class="upload-placeholder">
                <input type="file" accept="image/*" @change="handleImageUpload" :disabled="imageUploading" hidden />
                <div class="upload-icon">📷</div>
                <div class="upload-text">{{ imageUploading ? '上传中...' : '点击上传图片' }}</div>
              </label>
            </div>
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

    <div class="modal-overlay" v-if="showSpecModal" @click.self="showSpecModal = false">
      <div class="modal spec-modal">
        <div class="modal-header">
          <h3>{{ editingSpec && 'spec_code' in editingSpec ? '编辑规格' : '添加规格' }}</h3>
          <button class="modal-close" @click="showSpecModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row three-col">
            <div class="form-group">
              <label>规格编号</label>
              <input type="text" v-model="specForm.spec_code" placeholder="自动生成或手动输入" />
            </div>
            <div class="form-group">
              <label>价格 *</label>
              <input type="number" v-model="specForm.price" placeholder="0.00" min="0" step="0.01" />
            </div>
            <div class="form-group">
              <label>CAS号</label>
              <input type="text" v-model="specForm.cas_number" placeholder="CAS号" />
            </div>
          </div>
          <div class="form-row three-col">
            <div class="form-group">
              <label>包装</label>
              <input type="text" v-model="specForm.packaging" placeholder="如: 100g/罐" />
            </div>
            <div class="form-group">
              <label>销售规格</label>
              <input type="text" v-model="specForm.sales_spec" placeholder="如: 100g*24罐/箱" />
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="specForm.is_active" />
                是否有效
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showSpecModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveSpec" :disabled="formLoading">
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
          <p>确定要删除该{{ deleteTargetType === 'product' ? '商品及其所有规格' : '规格' }}吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showStockDetail" @click.self="showStockDetail = false">
      <div class="modal stock-detail-modal">
        <div class="modal-header">
          <h3>库存详情 - {{ selectedSpecForStock?.spec_code }}</h3>
          <button class="modal-close" @click="showStockDetail = false">×</button>
        </div>
        <div class="modal-body">
          <div class="stock-detail-info">
            <p class="stock-total">总库存数量: <strong>{{ selectedSpecForStock?.stock_quantity || 0 }}</strong></p>
          </div>
          <table class="stock-detail-table">
            <thead>
              <tr>
                <th>仓库</th>
                <th>批次号</th>
                <th>数量</th>
                <th>最小库存</th>
                <th>最大库存</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showStockDetail = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-workspace {
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

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-toolbar .checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
}

.table-toolbar input[type="checkbox"] {
  display: none;
}

.table-toolbar .toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  background-color: var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.table-toolbar .toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background-color: white;
  border-radius: 50%;
  transition: transform var(--transition-fast);
}

.table-toolbar input[type="checkbox"]:checked + .toggle-switch {
  background-color: var(--accent-blue);
}

.table-toolbar input[type="checkbox"]:checked + .toggle-switch::after {
  transform: translateX(16px);
}

.toggle-all-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 12px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-all-btn:hover {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 8px 12px;
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

.product-row {
  transition: background-color var(--transition-fast);
}

.product-row:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

.product-row.expanded {
  background-color: rgba(0, 120, 212, 0.08);
}

.expand-cell {
  width: 40px;
  text-align: center;
}

.expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.expand-btn:hover {
  color: var(--accent-blue);
}

.expand-icon {
  display: inline-block;
  transition: transform var(--transition-fast);
  font-size: 10px;
}

.expand-icon.rotated {
  transform: rotate(90deg);
}

.code-cell {
  font-family: monospace;
  color: var(--text-secondary);
}

.name-cell .product-name {
  font-weight: 500;
}

.spec-count-cell {
  text-align: center;
}

.spec-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.actions-cell {
  white-space: nowrap;
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

.spec-row {
  background-color: var(--bg-secondary);
}

.spec-cell {
  padding: 0 !important;
}

.spec-table-wrapper {
  padding: 12px 20px;
}

.spec-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
}

.spec-table th,
.spec-table td {
  padding: 6px 10px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
}

.spec-table th {
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  font-weight: 500;
}

.spec-table tr.inactive {
  opacity: 0.6;
}

.spec-table tr:hover {
  background-color: rgba(0, 120, 212, 0.03);
}

.empty-spec-cell {
  text-align: center;
  padding: 24px !important;
  color: var(--text-muted);
}

.price-cell {
  color: var(--accent-red);
  font-weight: 500;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-qty {
  font-weight: 500;
}

.status-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
}

.status-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.low-stock {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

.status-tag.out-of-stock {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.status-tag.overstock {
  background-color: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.active-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.active-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.spec-actions {
  white-space: nowrap;
}

.stock-link {
  color: var(--accent-blue);
  cursor: pointer;
  text-decoration: underline;
}

.stock-link:hover {
  color: var(--accent-blue-hover);
}

.stock-detail-modal {
  max-width: 700px;
}

.stock-detail-info {
  margin-bottom: 16px;
  padding: 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.stock-total {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}

.stock-total strong {
  font-size: 18px;
  color: var(--accent-red);
}

.stock-detail-table {
  width: 100%;
  border-collapse: collapse;
}

.stock-detail-table th,
.stock-detail-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.stock-detail-table th {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.stock-detail-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
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

.modal.spec-modal {
  max-width: 800px;
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

.form-row.three-col {
  grid-template-columns: repeat(3, 1fr);
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

.form-group label.checkbox-label {
  flex-direction: row;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group input[type="checkbox"] {
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

@media (max-width: 1024px) {
  .form-row.three-col {
    grid-template-columns: repeat(2, 1fr);
  }

  .spec-table-wrapper {
    overflow-x: auto;
  }

  .spec-table {
    min-width: 900px;
  }
}

@media (max-width: 768px) {
  .form-row,
  .form-row.three-col {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }

  .stats-bar {
    flex-wrap: wrap;
  }
}
</style>
