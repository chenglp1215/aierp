<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { productApi, uploadApi, type Product, type ProductSpec, type ProductFormData, type ProductSpecFormData } from '../../services/api'
import type { VxeTablePropTypes } from 'vxe-pc-ui'

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
const showSpecModal = ref(false)
const showDeleteConfirm = ref(false)
const showStockDetail = ref(false)
const editingProduct = ref<Product | null>(null)
const editingSpec = ref<ProductSpec | null>(null)
const selectedSpecForStock = ref<ProductSpec | null>(null)
const stockDetailLoading = ref(false)
const stockDetailData = ref<any[]>([])
const stockDetailTotal = ref(0)
const deleteTargetId = ref<string | null>(null)
const deleteTargetType = ref<'product' | 'spec'>('product')
const formLoading = ref(false)
const deleteLoading = ref(false)
const imageUploading = ref(false)

const productForm = ref<ProductFormData>({
  product_code: '',
  name: '',
  image_url: '',
  brand: '',
  category: '',
  tax_code: '',
  is_active: true
})

const specForm = ref<ProductSpecFormData>({
  spec_code: '',
  packaging: '',
  sales_spec: '',
  price: 0,
  cas_number: '',
  is_active: true
})

const verticalTableData = ref<any[]>([])
const specsListInModal = ref<ProductSpec[]>([])

const formatPrice = (price: number) => `¥${price.toFixed(2)}`

const getStockStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'normal': '正常',
    'low_stock': '低库存',
    'out_of_stock': '缺货',
    'overstock': '超库存'
  }
  return statusMap[status] || status || '-'
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
    productGroups.value = products.value.map(p => ({
      product: p,
      rowspan: p.specs?.length || 1
    }))
    total.value = res.total
    buildVerticalTableData()
  } catch (error) {
    console.error('加载商品列表失败:', error)
  } finally {
    loading.value = false
  }
}

const buildVerticalTableData = () => {
  const data: any[] = []
  for (const group of productGroups.value) {
    const specs = group.product.specs || []
    for (let i = 0; i < specs.length; i++) {
      const spec = specs[i]
      data.push({
        _id: `${group.product.id}_${spec.id}`,
        product_id: group.product.id,
        product_code: group.product.product_code,
        product_name: group.product.name,
        brand: group.product.brand,
        category: group.product.category,
        product_is_active: group.product.is_active ?? true,
        spec_id: spec.id,
        spec_code: spec.spec_code,
        packaging: spec.packaging,
        sales_spec: spec.sales_spec,
        price: spec.price,
        spec_is_active: spec.is_active,
        stock_quantity: spec.stock_quantity || 0,
        stock_status: spec.stock_status,
        isFirst: i === 0,
        rowspan: i === 0 ? specs.length : 0,
        product_rowspan: i === 0 ? specs.length : 0,
        specs_length: specs.length
      })
    }
  }
  verticalTableData.value = data
}

const verticalSpanMethod: VxeTablePropTypes.SpanMethod = ({ row, columnIndex }) => {
  const productCols = [0, 1, 2, 3, 4, 10]
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
  try {
    const res = await productApi.getStats()
    stats.value = res.result
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
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
  page.value = 1
  loadProducts()
}

const hasActiveFilters = computed(() => !!keyword.value)

const resetProductForm = () => {
  productForm.value = { product_code: '', name: '', image_url: '', brand: '', category: '', tax_code: '', is_active: true }
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
    brand: product.brand,
    category: product.category,
    tax_code: product.tax_code || '',
    is_active: product.is_active ?? true
  }
  specsListInModal.value = [...(product.specs || [])]
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
    buildVerticalTableData()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const editingSpecId = ref<string | null>(null)
const isAddingNewSpec = ref(false)
const newSpecForm = ref({
  spec_code: '',
  packaging: '',
  sales_spec: '',
  price: 0,
  cas_number: '',
  is_active: true
})
const editingSpecBackup = ref<any>(null)

const addNewSpecInModal = () => {
  isAddingNewSpec.value = true
  editingSpecId.value = null
  newSpecForm.value = {
    spec_code: '',
    packaging: '',
    sales_spec: '',
    price: 0,
    cas_number: '',
    is_active: true
  }
}

const cancelAddNewSpec = () => {
  isAddingNewSpec.value = false
  newSpecForm.value = {
    spec_code: '',
    packaging: '',
    sales_spec: '',
    price: 0,
    cas_number: '',
    is_active: true
  }
}

const confirmAddNewSpec = () => {
  if (!newSpecForm.value.price || newSpecForm.value.price < 0) {
    window.showToast('请输入有效的价格', 'warning')
    return
  }
  const newSpec: ProductSpec = {
    id: `temp_${Date.now()}`,
    product_id: editingProduct.value!.id,
    spec_code: newSpecForm.value.spec_code,
    packaging: newSpecForm.value.packaging,
    sales_spec: newSpecForm.value.sales_spec,
    price: newSpecForm.value.price,
    cas_number: newSpecForm.value.cas_number,
    is_active: newSpecForm.value.is_active
  }
  specsListInModal.value.push(newSpec)
  isAddingNewSpec.value = false
}

const startEditSpec = (spec: ProductSpec) => {
  editingSpecId.value = spec.id
  editingSpecBackup.value = { ...spec }
}

const cancelEditSpec = () => {
  if (editingSpecBackup.value) {
    const index = specsListInModal.value.findIndex(s => s.id === editingSpecBackup.value.id)
    if (index !== -1) {
      specsListInModal.value[index] = editingSpecBackup.value
    }
  }
  editingSpecId.value = null
  editingSpecBackup.value = null
}

const saveSpecFromRow = (spec: ProductSpec) => {
  if (!spec.price || spec.price < 0) {
    window.showToast('请输入有效的价格', 'warning')
    return
  }
  editingSpecId.value = null
  editingSpecBackup.value = null
}

const deleteSpecInModal = (specId: string) => {
  const index = specsListInModal.value.findIndex(s => s.id === specId)
  if (index !== -1) {
    specsListInModal.value.splice(index, 1)
  }
}

const handleSaveProductWithSpecs = async () => {
  if (!productForm.value.name?.trim()) {
    window.showToast('请输入商品名称', 'warning')
    return
  }
  const specCodes = specsListInModal.value
    .map(spec => spec.spec_code)
    .filter(code => code && code.trim())
  if (specCodes.length !== new Set(specCodes).size) {
    window.showToast('同一商品下的规格编号不能重复', 'warning')
    return
  }
  formLoading.value = true
  try {
    const formDataWithSpecs: ProductFormData = {
      ...productForm.value,
      specs: specsListInModal.value.map(spec => ({
        id: spec.id && !spec.id.toString().startsWith('temp_') ? spec.id : undefined,
        spec_code: spec.spec_code,
        packaging: spec.packaging,
        sales_spec: spec.sales_spec,
        price: spec.price,
        cas_number: spec.cas_number,
        is_active: spec.is_active
      }))
    }
    if (editingProduct.value) {
      await productApi.update(editingProduct.value.id, formDataWithSpecs)
      window.showToast('商品更新成功', 'success')
    } else {
      await productApi.create(formDataWithSpecs)
      window.showToast('商品创建成功', 'success')
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

const confirmDeleteProduct = (row: any) => {
  deleteTargetId.value = row.product_id
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
      products.value = products.value.filter(p => p.id !== deleteTargetId.value)
      total.value--
    } else {
      await productApi.deleteSpec(deleteTargetId.value)
      window.showToast('规格删除成功', 'success')
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
    buildVerticalTableData()
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

const openCreateSpec = (row: any) => {
  resetSpecForm()
  editingSpec.value = { id: row.product_id, product_id: row.product_id } as ProductSpec
  showSpecModal.value = true
}

const openEditSpec = (row: any) => {
  const spec = products.value
    .flatMap(p => p.specs || [])
    .find(s => s.id === row.spec_id)
  if (!spec) return
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

const confirmDeleteSpec = (row: any) => {
  deleteTargetId.value = row.spec_id
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
      await productApi.updateSpec(editingSpec.value.id, specForm.value)
      window.showToast('规格更新成功', 'success')
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
      await productApi.createSpec(productId!, specForm.value)
      window.showToast('规格创建成功', 'success')
      loadProducts()
    }
    showSpecModal.value = false
    loadStats()
    buildVerticalTableData()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleToggleSpecActive = async (row: any) => {
  const spec = products.value
    .flatMap(p => p.specs || [])
    .find(s => s.id === row.spec_id)
  if (!spec) return
  const newStatus = !spec.is_active
  try {
    await productApi.toggleSpecActive(spec.id, newStatus)
    window.showToast(`规格已${newStatus ? '激活' : '停用'}`, 'success')
    for (const product of products.value) {
      if (product.specs) {
        const specItem = product.specs.find(s => s.id === spec.id)
        if (specItem) {
          specItem.is_active = newStatus
          break
        }
      }
    }
    buildVerticalTableData()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  }
}

const openStockDetail = async (row: any) => {
  const spec = products.value
    .flatMap(p => p.specs || [])
    .find(s => s.id === row.spec_id)
  if (spec) {
    selectedSpecForStock.value = spec
    showStockDetail.value = true
    stockDetailLoading.value = true
    stockDetailData.value = []
    try {
      const res = await productApi.getSpecStockDetail(spec.id)
      if (res.result) {
        stockDetailData.value = res.result.items || []
        stockDetailTotal.value = res.result.total_quantity || 0
      }
    } catch (error) {
      console.error('加载库存详情失败:', error)
    } finally {
      stockDetailLoading.value = false
    }
  }
}

onMounted(() => {
  loadProducts()
  loadStats()
  document.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})

const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    showProductModal.value = false
  }
}
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
        <vxe-column field="product_code" title="商品编号" width="130" class-name="col--center" />
        <vxe-column field="product_name" title="商品名称" min-width="180" class-name="col--center" />
        <vxe-column field="brand" title="品牌" width="100" class-name="col--center" />
        <vxe-column field="category" title="分类" width="100" class-name="col--center" />
        <vxe-column field="spec_code" title="规格编号" width="130" />
        <vxe-column field="packaging" title="包装" width="100" />
        <vxe-column field="sales_spec" title="销售规格" width="120" />
        <vxe-column field="price" title="价格" width="100" />
        <vxe-column field="stock_quantity" title="库存" width="80">
          <template #default="{ row }">
            <button class="stock-link" @click.stop="openStockDetail(row)">{{ row.stock_quantity || 0 }}</button>
          </template>
        </vxe-column>
        <vxe-column field="product_is_active" title="商品有效" width="80" class-name="col--center">
          <template #default="{ row }">
            <span :class="['active-tag', row.product_is_active ? 'active' : '']">{{ row.product_is_active ? '在售' : '停用' }}</span>
          </template>
        </vxe-column>
        <vxe-column field="spec_is_active" title="规格有效" width="80" class-name="col--center">
          <template #default="{ row }">
            <span :class="['active-tag', row.spec_is_active ? 'active' : '']">{{ row.spec_is_active ? '在售' : '停用' }}</span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="220" fixed="right" class-name="col--center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="openEditProduct(row)">编辑</button>
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

    <div class="modal-overlay" v-if="showProductModal">
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
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="productForm.is_active" />
                是否有效
              </label>
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
          <div class="specs-section" v-if="editingProduct">
            <div class="specs-section-header">
              <h4>商品规格列表</h4>
              <button class="btn-secondary btn-sm" @click="addNewSpecInModal">添加规格</button>
            </div>
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
                    <td><input type="text" v-model="spec.spec_code" class="inline-input" placeholder="自动生成或手动输入" /></td>
                    <td><input type="text" v-model="spec.packaging" class="inline-input" placeholder="包装" /></td>
                    <td><input type="text" v-model="spec.sales_spec" class="inline-input" placeholder="销售规格" /></td>
                    <td><input type="number" v-model="spec.price" class="inline-input" placeholder="0.00" min="0" step="0.01" /></td>
                    <td><input type="text" v-model="spec.cas_number" class="inline-input" placeholder="CAS号" /></td>
                    <td><input type="checkbox" v-model="spec.is_active" class="inline-checkbox" /></td>
                    <td>
                      <button class="btn-link" @click="cancelEditSpec">取消</button>
                      <button class="btn-link" @click="saveSpecFromRow(spec)">保存</button>
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
                      <button class="btn-link danger" @click="deleteSpecInModal(spec.id)">删除</button>
                    </td>
                  </template>
                </tr>
                <tr v-if="isAddingNewSpec">
                  <td><input type="text" v-model="newSpecForm.spec_code" class="inline-input" placeholder="自动生成或手动输入" /></td>
                  <td><input type="text" v-model="newSpecForm.packaging" class="inline-input" placeholder="包装" /></td>
                  <td><input type="text" v-model="newSpecForm.sales_spec" class="inline-input" placeholder="销售规格" /></td>
                  <td><input type="number" v-model="newSpecForm.price" class="inline-input" placeholder="0.00" min="0" step="0.01" /></td>
                  <td><input type="text" v-model="newSpecForm.cas_number" class="inline-input" placeholder="CAS号" /></td>
                  <td><input type="checkbox" v-model="newSpecForm.is_active" class="inline-checkbox" /></td>
                  <td>
                    <button class="btn-link" @click="cancelAddNewSpec">取消</button>
                    <button class="btn-link" @click="confirmAddNewSpec">保存</button>
                  </td>
                </tr>
                <tr v-if="specsListInModal.length === 0 && !isAddingNewSpec">
                  <td colspan="7" class="specs-empty">暂无规格，请添加规格</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showProductModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveProductWithSpecs" :disabled="formLoading">
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
            <p class="stock-total">总库存数量: <strong>{{ stockDetailTotal || selectedSpecForStock?.stock_quantity || 0 }}</strong></p>
          </div>
          <div v-if="stockDetailLoading" class="stock-loading">加载中...</div>
          <table v-else-if="stockDetailData.length > 0" class="stock-detail-table">
            <thead>
              <tr>
                <th>仓库</th>
                <th>仓库编号</th>
                <th>数量</th>
                <th>最小库存</th>
                <th>最大库存</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in stockDetailData" :key="item.id">
                <td>{{ item.warehouse_name || '-' }}</td>
                <td>{{ item.warehouse_code || '-' }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ item.min_stock ?? '-' }}</td>
                <td>{{ item.max_stock ?? '-' }}</td>
                <td>{{ getStockStatusText(item.status) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-cell">暂无数据</div>
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

.price-text {
  color: var(--accent-red);
  font-weight: 500;
}

.stock-link {
  background: transparent;
  color: var(--accent-blue);
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  border: none;
  font-size: inherit;
}

.stock-link:hover {
  color: var(--accent-blue-hover);
}

.active-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.active-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
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
  max-width: 1000px;
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

.specs-section {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-top: 8px;
}

.specs-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.specs-section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.specs-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
}

.specs-table th,
.specs-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  font-size: 13px;
}

.specs-table th {
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.specs-table td {
  color: var(--text-primary);
}

.specs-table tbody tr:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

.specs-table td .inline-input {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.specs-table td .inline-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.specs-table td .inline-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.specs-empty {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.action-btns {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: center;
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

.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.stock-loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

@media (max-width: 1024px) {
  .form-row.three-col {
    grid-template-columns: repeat(2, 1fr);
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

[data-theme="light"] .vxe-pager {
  background-color: #ffffff !important;
  border-top: 1px solid #e5e7eb;
}

[data-theme="light"] .vxe-pager * {
  background-color: inherit !important;
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
