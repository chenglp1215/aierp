<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { productApi, uploadApi, categoryApi, brandApi, type Product, type ProductSpec, type ProductFormData, type ProductSpecFormData, type CategoryTreeNode, type Brand } from '../../services/api'

type SpanMethod = (params: { row: any; columnIndex: number }) => { rowspan: number; colspan: number } | void

interface ProductGroup {
  product: Product
  rowspan: number
}

const loading = ref(false)
const products = ref<Product[]>([])
const productGroups = ref<ProductGroup[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const stats = ref({ total: 0, total_stock: 0, total_specs: 0 })

const showProductModal = ref(false)
const showSpecManageModal = ref(false)
const showDeleteConfirm = ref(false)
const showStockDetail = ref(false)
const editingProduct = ref<Product | null>(null)
const managingProduct = ref<Product | null>(null)
const selectedSpecForStock = ref<ProductSpec | null>(null)
const stockDetailLoading = ref(false)
const stockDetailData = ref<any[]>([])
const stockDetailTotal = ref(0)
const deleteTargetId = ref<string | null>(null)
const deleteTargetType = ref<'product' | 'spec'>('product')
const formLoading = ref(false)
const deleteLoading = ref(false)
const imageUploading = ref(false)

const categories = ref<CategoryTreeNode[]>([])
const categoriesLoading = ref(false)

const brands = ref<Brand[]>([])
const brandsLoading = ref(false)

const filterBrandId = ref('')
const filterCategoryId = ref('')

const brandOptions = computed(() => {
  return brands.value.filter(b => b.is_active !== false).map(b => ({ id: b.id, name: b.name }))
})

const flatCategories = computed(() => {
  const result: { id: string; name: string; level: number }[] = []
  const flatten = (nodes: CategoryTreeNode[], level = 1) => {
    for (const node of nodes) {
      result.push({ id: node.id, name: node.name, level })
      if (node.children?.length) {
        flatten(node.children, level + 1)
      }
    }
  }
  flatten(categories.value)
  return result
})

const loadCategories = async () => {
  categoriesLoading.value = true
  try {
    const res = await categoryApi.list()
    categories.value = res || []
  } catch (error) {
    console.error('加载分类失败:', error)
  } finally {
    categoriesLoading.value = false
  }
}

const loadBrands = async () => {
  brandsLoading.value = true
  try {
    const res = await brandApi.getAll()
    brands.value = res || []
  } catch (error) {
    console.error('加载品牌失败:', error)
  } finally {
    brandsLoading.value = false
  }
}

const productForm = ref<ProductFormData>({
  product_code: '',
  name: '',
  image_url: '',
  brand_id: '',
  category_id: '',
  tax_code: '',
  is_active: true
})

const verticalTableData = ref<any[]>([])

const formatPrice = (price: number) => `¥${(price || 0).toFixed(2)}`

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
      keyword: keyword.value || undefined,
      brand_id: filterBrandId.value || undefined,
      category_id: filterCategoryId.value || undefined
    })
    products.value = res.items || res.result?.items || []
    productGroups.value = products.value.map(p => ({
      product: p,
      rowspan: p.specs?.length || 1
    }))
    total.value = res.total || res.result?.total || 0
    buildVerticalTableData()
  } catch (error) {
    console.error('加载产品列表失败:', error)
  } finally {
    loading.value = false
  }
}

const computeStockQuantity = (spec: ProductSpec): number => {
  if (!spec.stock_status || spec.stock_status.length === 0) return 0
  return spec.stock_status.reduce((sum, stock) => sum + (stock.quantity || 0), 0)
}

const buildVerticalTableData = () => {
  const data: any[] = []
  for (const group of productGroups.value) {
    const specs = group.product.specs || []
    if (specs.length === 0) {
      data.push({
        _id: `${group.product.id}_empty`,
        product_id: group.product.id,
        product_code: group.product.product_code,
        product_name: group.product.name,
        brand_name: group.product.brand_name,
        category: group.product.category_name || '-',
        product_is_active: group.product.is_active ?? true,
        spec_id: '',
        spec_code: '-',
        packaging: '-',
        sales_spec: '-',
        price: 0,
        spec_is_active: false,
        stock_quantity: 0,
        stock_status: [],
        isFirst: true,
        rowspan: 1,
        product_rowspan: 1,
        specs_length: 0
      })
    } else {
      for (let i = 0; i < specs.length; i++) {
        const spec = specs[i]
        data.push({
          _id: `${group.product.id}_${spec.id}`,
          product_id: group.product.id,
          product_code: group.product.product_code,
          product_name: group.product.name,
          brand_name: group.product.brand_name,
          category: group.product.category_name || '-',
          product_is_active: group.product.is_active ?? true,
          spec_id: spec.id,
          spec_code: spec.spec_code || '-',
          packaging: spec.packaging || '-',
          sales_spec: spec.sales_spec || '-',
          price: spec.price,
          spec_is_active: spec.is_active,
          stock_quantity: computeStockQuantity(spec),
          stock_status: spec.stock_status || [],
          isFirst: i === 0,
          rowspan: i === 0 ? specs.length : 0,
          product_rowspan: i === 0 ? specs.length : 0,
          specs_length: specs.length
        })
      }
    }
  }
  verticalTableData.value = data
}

const verticalSpanMethod: SpanMethod = ({ row, columnIndex }) => {
  const productCols = [0, 1, 2, 3, 4, 5]
  const actionCol = 12
  if (productCols.includes(columnIndex) && row.isFirst) {
    return { rowspan: row.rowspan, colspan: 1 }
  }
  if (productCols.includes(columnIndex) || (columnIndex === actionCol && !row.isFirst)) {
    return { rowspan: 0, colspan: 0 }
  }
  if (columnIndex === actionCol && row.isFirst) {
    return { rowspan: row.rowspan, colspan: 1 }
  }
}

const seqMethod = ({ row }: { row: any }) => {
  if (!row.isFirst) return 0
  const firstRows = verticalTableData.value.filter(r => r.isFirst)
  return firstRows.findIndex(r => r._id === row._id) + 1 + (page.value - 1) * pageSize.value
}

const loadStats = async () => {
  stats.value = { total: 0, total_stock: 0, total_specs: 0 }
}

const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadProducts()
}

const handleSearch = () => {
  page.value = 1
  loadProducts()
}

const resetFilters = () => {
  keyword.value = ''
  filterBrandId.value = ''
  filterCategoryId.value = ''
  page.value = 1
  loadProducts()
}

const hasActiveFilters = computed(() => !!(keyword.value || filterBrandId.value || filterCategoryId.value))

const resetProductForm = () => {
  productForm.value = { product_code: '', name: '', image_url: '', brand_id: '', category_id: '', tax_code: '', is_active: true }
  editingProduct.value = null
}

const openCreateProduct = () => {
  resetProductForm()
  showProductModal.value = true
}

const openEditProduct = (row: any) => {
  const product = products.value.find(p => p.id === row.product_id)
  if (!product) return
  editingProduct.value = product
  productForm.value = {
    product_code: product.product_code,
    name: product.name,
    image_url: product.image_url || '',
    brand_id: product.brand_id,
    category_id: product.category_id,
    tax_code: product.tax_code || '',
    is_active: product.is_active ?? true
  }
  showProductModal.value = true
}

const handleSaveProduct = async () => {
  if (!productForm.value.name?.trim()) {
    window.showToast('请输入产品名称', 'warning')
    return
  }
  formLoading.value = true
  try {
    if (editingProduct.value) {
      await productApi.update(editingProduct.value.id, productForm.value)
      window.showToast('产品更新成功', 'success')
    } else {
      await productApi.create(productForm.value)
      window.showToast('产品创建成功', 'success')
    }
    showProductModal.value = false
    loadProducts()
    loadStats()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const openSpecManage = async (row: any) => {
  const product = products.value.find(p => p.id === row.product_id)
  if (!product) return
  managingProduct.value = product
  await loadProductSpecs()
  showSpecManageModal.value = true
}

const specsListInModal = ref<ProductSpec[]>([])
const loadProductSpecs = async () => {
  if (!managingProduct.value) return
  try {
    const res = await productApi.getSpecs(managingProduct.value.id)
    console.log('规格列表API响应:', res)
    const items = res.items ?? res.result?.items ?? res.result
    specsListInModal.value = Array.isArray(items) ? items : []
  } catch (error) {
    console.error('加载规格列表失败:', error)
    console.error('当前商品规格缓存:', managingProduct.value.specs)
    specsListInModal.value = managingProduct.value.specs || []
  }
}

const editingSpecId = ref<string | null>(null)
const editingSpecForm = ref<ProductSpecFormData>({
  spec_code: '',
  packaging: '',
  sales_spec: '',
  price: 0,
  cas_number: '',
  is_active: true
})

const startEditSpec = (spec: ProductSpec) => {
  editingSpecId.value = spec.id
  editingSpecForm.value = {
    spec_code: spec.spec_code || '',
    packaging: spec.packaging || '',
    sales_spec: spec.sales_spec || '',
    price: spec.price || 0,
    cas_number: spec.cas_number || '',
    is_active: spec.is_active ?? true
  }
}

const cancelEditSpec = () => {
  editingSpecId.value = null
  editingSpecForm.value = { spec_code: '', packaging: '', sales_spec: '', price: 0, cas_number: '', is_active: true }
}

const handleUpdateSpec = async () => {
  if (!editingSpecId.value) return
  if (!editingSpecForm.value.price || editingSpecForm.value.price < 0) {
    window.showToast('请输入有效的价格', 'warning')
    return
  }
  formLoading.value = true
  try {
    await productApi.updateSpec(editingSpecId.value, editingSpecForm.value)
    window.showToast('规格更新成功', 'success')
    editingSpecId.value = null
    editingSpecForm.value = { spec_code: '', packaging: '', sales_spec: '', price: 0, cas_number: '', is_active: true }
    await loadProductSpecs()
    loadProducts()
  } catch (error: any) {
    window.showToast(error.message || '更新规格失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const newSpecForm = ref<ProductSpecFormData>({
  spec_code: '',
  packaging: '',
  sales_spec: '',
  price: 0,
  cas_number: '',
  is_active: true
})
const isAddingSpec = ref(false)

const showAddSpecForm = () => {
  isAddingSpec.value = true
  newSpecForm.value = { spec_code: '', packaging: '', sales_spec: '', price: 0, cas_number: '', is_active: true }
}

const cancelAddSpec = () => {
  isAddingSpec.value = false
  newSpecForm.value = { spec_code: '', packaging: '', sales_spec: '', price: 0, cas_number: '', is_active: true }
}

const handleCreateSpec = async () => {
  if (!managingProduct.value) return
  if (!newSpecForm.value.price || newSpecForm.value.price < 0) {
    window.showToast('请输入有效的价格', 'warning')
    return
  }
  formLoading.value = true
  try {
    await productApi.createSpec(managingProduct.value.id, newSpecForm.value)
    window.showToast('规格创建成功', 'success')
    isAddingSpec.value = false
    newSpecForm.value = { spec_code: '', packaging: '', sales_spec: '', price: 0, cas_number: '', is_active: true }
    await loadProductSpecs()
    loadProducts()
  } catch (error: any) {
    window.showToast(error.message || '创建规格失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const confirmDeleteProduct = (row: any) => {
  deleteTargetId.value = row.product_id
  deleteTargetType.value = 'product'
  showDeleteConfirm.value = true
}

const confirmDeleteSpec = (spec: ProductSpec) => {
  if (!spec.id) {
    window.showToast('规格ID不存在，无法删除', 'error')
    return
  }
  deleteTargetId.value = spec.id
  deleteTargetType.value = 'spec'
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  deleteLoading.value = true
  try {
    if (deleteTargetType.value === 'product') {
      await productApi.delete(deleteTargetId.value)
      window.showToast('产品删除成功', 'success')
      products.value = products.value.filter(p => p.id !== deleteTargetId.value)
      productGroups.value = products.value.map(p => ({
        product: p,
        rowspan: p.specs?.length || 1
      }))
      total.value--
    } else {
      await productApi.deleteSpec(deleteTargetId.value)
      window.showToast('规格删除成功', 'success')
      await loadProductSpecs()
      await loadProducts()
    }
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadStats()
    buildVerticalTableData()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const openStockDetail = async (row: any) => {
  const spec = products.value
    .flatMap(p => p.specs || [])
    .find(s => s.id === row.spec_id)
  if (spec) {
    selectedSpecForStock.value = spec
    showStockDetail.value = true
    stockDetailLoading.value = false
    stockDetailData.value = spec.stock_status || []
    stockDetailTotal.value = computeStockQuantity(spec)
  }
}

onMounted(() => {
  loadProducts()
  loadStats()
  loadCategories()
  loadBrands()
  document.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})

const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    showProductModal.value = false
    showSpecManageModal.value = false
  }
}
</script>

<template>
  <div class="product-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">产品管理</h2>
      <div class="header-actions">
        <button class="primary-btn" @click="openCreateProduct">新建产品</button>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索产品名称、编号..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filterBrandId" class="filter-select">
          <option value="">全部品牌</option>
          <option v-for="brand in brandOptions" :key="brand.id" :value="brand.id">{{ brand.name }}</option>
        </select>
        <select v-model="filterCategoryId" class="filter-select">
          <option value="">全部分类</option>
          <option v-for="cat in flatCategories" :key="cat.id" :value="cat.id">{{ '　'.repeat(cat.level - 1) }}{{ cat.name }}</option>
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
        :data="verticalTableData"
        :column-config="{ resizable: true }"
        :span-method="verticalSpanMethod"
        :seq-config="{ seqMethod: seqMethod }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
        <vxe-column field="product_code" title="产品编号" min-width="100" class-name="col--center" />
        <vxe-column field="product_name" title="产品名称" min-width="150" class-name="col--center" />
        <vxe-column field="brand_name" title="品牌" min-width="80" class-name="col--center" />
        <vxe-column field="category" title="分类" min-width="80" class-name="col--center" />
        <vxe-column field="product_is_active" title="产品有效" min-width="60" class-name="col--center">
          <template #default="{ row }">
            <span :class="['active-tag', row.product_is_active ? 'active' : '']">{{ row.product_is_active ? '在售' : '停用' }}</span>
          </template>
        </vxe-column>
        <vxe-column field="spec_code" title="规格编号" min-width="100" />
        <vxe-column field="packaging" title="包装" min-width="80" />
        <vxe-column field="sales_spec" title="销售规格" min-width="100" />
        <vxe-column field="price" title="价格" min-width="80" />
        <vxe-column field="stock_quantity" title="库存" min-width="60">
          <template #default="{ row }">
            <button class="stock-link" @click.stop="openStockDetail(row)">{{ row.stock_quantity || 0 }}</button>
          </template>
        </vxe-column>
        <vxe-column field="spec_is_active" title="规格有效" min-width="60" class-name="col--center">
          <template #default="{ row }">
            <span :class="['active-tag', row.spec_is_active ? 'active' : '']">{{ row.spec_is_active ? '在售' : '停用' }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="240" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns" v-if="row.isFirst">
              <button class="btn-link" @click="openEditProduct(row)">编辑</button>
              <button class="btn-link" @click="openSpecManage(row)">管理规格</button>
              <button class="btn-link danger" @click="confirmDeleteProduct(row)">删除</button>
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

    <!-- 商品编辑弹窗 -->
    <div class="modal-overlay" v-if="showProductModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingProduct ? '编辑产品' : '新建产品' }}</h3>
          <button class="modal-close" @click="showProductModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>产品编号</label>
              <input type="text" v-model="productForm.product_code" placeholder="自动生成或手动输入" />
            </div>
            <div class="form-group">
              <label>产品名称 *</label>
              <input type="text" v-model="productForm.name" placeholder="请输入产品名称" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>品牌</label>
              <select v-model="productForm.brand_id" class="form-select" :disabled="brandsLoading">
                <option value="">请选择品牌</option>
                <option v-for="brand in brandOptions" :key="brand.id" :value="brand.id">
                  {{ brand.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>分类</label>
              <select v-model="productForm.category_id" class="form-select" :disabled="categoriesLoading">
                <option value="">请选择分类</option>
                <option v-for="cat in flatCategories" :key="cat.id" :value="cat.id">
                  {{ '　'.repeat(cat.level - 1) }}{{ cat.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>税务编码</label>
              <input type="text" v-model="productForm.tax_code" placeholder="税务编码" />
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="productForm.is_active" />
                是否有效
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>产品图片</label>
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

    <!-- 规格管理弹窗 -->
    <div class="modal-overlay" v-if="showSpecManageModal">
      <div class="modal spec-manage-modal">
        <div class="modal-header">
          <h3>规格管理 - {{ managingProduct?.name }}</h3>
          <button class="modal-close" @click="showSpecManageModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="spec-manage-header">
            <button class="btn-secondary btn-sm" @click="showAddSpecForm" v-if="!isAddingSpec">
              添加规格
            </button>
          </div>

          <!-- 添加规格表单 -->
          <div v-if="isAddingSpec" class="spec-add-form">
            <div class="form-row three-col">
              <div class="form-group">
                <label>规格编号</label>
                <input type="text" v-model="newSpecForm.spec_code" placeholder="自动生成或手动输入" />
              </div>
              <div class="form-group">
                <label>价格 *</label>
                <input type="number" v-model="newSpecForm.price" placeholder="0.00" min="0" step="0.01" />
              </div>
              <div class="form-group">
                <label>CAS号</label>
                <input type="text" v-model="newSpecForm.cas_number" placeholder="CAS号" />
              </div>
            </div>
            <div class="form-row three-col">
              <div class="form-group">
                <label>包装</label>
                <input type="text" v-model="newSpecForm.packaging" placeholder="如: 100g/罐" />
              </div>
              <div class="form-group">
                <label>销售规格</label>
                <input type="text" v-model="newSpecForm.sales_spec" placeholder="如: 100g*24罐/箱" />
              </div>
              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="newSpecForm.is_active" />
                  是否有效
                </label>
              </div>
            </div>
            <div class="spec-form-actions">
              <button class="btn-primary btn-sm" @click="handleCreateSpec" :disabled="formLoading">
                {{ formLoading ? '创建中...' : '确认添加' }}
              </button>
              <button class="btn-secondary btn-sm" @click="cancelAddSpec">取消</button>
            </div>
          </div>

          <!-- 规格列表 -->
          <table class="specs-table">
            <thead>
              <tr>
                <th>规格编号</th>
                <th>包装</th>
                <th>销售规格</th>
                <th>价格</th>
                <th>CAS号</th>
                <th>有效</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="spec in specsListInModal" :key="spec.id">
                <template v-if="editingSpecId === spec.id">
                  <td><input type="text" v-model="editingSpecForm.spec_code" class="inline-input" /></td>
                  <td><input type="text" v-model="editingSpecForm.packaging" class="inline-input" /></td>
                  <td><input type="text" v-model="editingSpecForm.sales_spec" class="inline-input" /></td>
                  <td><input type="number" v-model="editingSpecForm.price" class="inline-input" min="0" step="0.01" /></td>
                  <td><input type="text" v-model="editingSpecForm.cas_number" class="inline-input" /></td>
                  <td><input type="checkbox" v-model="editingSpecForm.is_active" class="inline-checkbox" /></td>
                  <td>
                    <button class="btn-link" @click="handleUpdateSpec" :disabled="formLoading">保存</button>
                    <button class="btn-link" @click="cancelEditSpec">取消</button>
                  </td>
                </template>
                <template v-else>
                  <td>{{ spec.spec_code || '-' }}</td>
                  <td>{{ spec.packaging || '-' }}</td>
                  <td>{{ spec.sales_spec || '-' }}</td>
                  <td>{{ formatPrice(spec.price) }}</td>
                  <td>{{ spec.cas_number || '-' }}</td>
                  <td>{{ spec.is_active ? '是' : '否' }}</td>
                  <td>
                    <button class="btn-link" @click="startEditSpec(spec)">编辑</button>
                    <button class="btn-link danger" @click="confirmDeleteSpec(spec)">删除</button>
                  </td>
                </template>
              </tr>
              <tr v-if="specsListInModal.length === 0 && !isAddingSpec">
                <td colspan="7" class="specs-empty">暂无规格</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showSpecManageModal = false">关闭</button>
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
          <p>确定要删除该{{ deleteTargetType === 'product' ? '产品及其所有规格' : '规格' }}吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 库存详情弹窗 -->
    <div class="modal-overlay" v-if="showStockDetail" @click.self="showStockDetail = false">
      <div class="modal stock-detail-modal">
        <div class="modal-header">
          <h3>库存详情 - {{ selectedSpecForStock?.spec_code }}</h3>
          <button class="modal-close" @click="showStockDetail = false">×</button>
        </div>
        <div class="modal-body">
          <div class="stock-detail-info">
            <p class="stock-total">总库存数量: <strong>{{ stockDetailTotal || 0 }}</strong></p>
          </div>
          <div v-if="stockDetailLoading" class="stock-loading">加载中...</div>
          <table v-else-if="stockDetailData.length > 0" class="stock-detail-table">
            <thead>
              <tr>
                <th>仓库</th>
                <th>数量</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in stockDetailData" :key="item.warehouse_id">
                <td>{{ item.warehouse_name || '-' }}</td>
                <td>{{ item.quantity || 0 }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-cell">暂无库存数据</div>
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
  color: var(--color-ink);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
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

.stock-link {
  background: transparent;
  color: var(--color-interactive);
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  border: none;
  font-size: inherit;
}

.stock-link:hover {
  color: var(--color-interactive-hover);
}

.active-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  background-color: var(--color-danger-bg);
  color: var(--color-danger);
}

.active-tag.active {
  background-color: var(--color-success-bg);
  color: var(--color-success);
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
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.modal.spec-manage-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--color-hairline);
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
  gap: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-hairline);
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
  color: var(--color-muted);
}

.form-group label.checkbox-label {
  flex-direction: row;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding-top: 24px;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.form-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.form-select {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 14px;
  width: 100%;
}

.form-select:focus {
  outline: none;
  border-color: var(--color-interactive);
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
  border: 1px solid var(--color-hairline);
}

.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--color-danger);
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
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-placeholder:hover {
  border-color: var(--color-interactive);
  background-color: rgba(0, 0, 0, 0.03);
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 12px;
  color: var(--color-muted);
}

.spec-manage-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.spec-add-form {
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
}

.spec-form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 12px;
}

.specs-table {
  width: 100%;
  border-collapse: collapse;
}

.specs-table th,
.specs-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 13px;
}

.specs-table th {
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.specs-table td {
  color: var(--color-ink);
}

.specs-table tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.specs-table .inline-input {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.specs-table .inline-input:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.specs-table .inline-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.specs-empty {
  text-align: center;
  padding: 20px;
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
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-danger {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-danger);
  color: white;
  font-size: 14px;
  border: none;
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

.stock-detail-modal {
  max-width: 700px;
}

.stock-detail-info {
  margin-bottom: 16px;
}

.stock-total {
  font-size: 14px;
  color: var(--color-ink);
}

.stock-total strong {
  color: var(--color-interactive);
  font-size: 18px;
}

.stock-detail-table {
  width: 100%;
  border-collapse: collapse;
}

.stock-detail-table th,
.stock-detail-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 13px;
}

.stock-detail-table th {
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.stock-detail-table td {
  color: var(--color-ink);
}

.empty-cell {
  text-align: center;
  padding: 20px;
  color: var(--color-muted);
  font-size: 13px;
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
}
</style>
