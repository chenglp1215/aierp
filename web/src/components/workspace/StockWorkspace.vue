<script setup lang="ts">
defineOptions({ name: 'StockWorkspace' })

import { ref, computed, onMounted } from 'vue'
import { stockApi, warehouseApi, productApi } from '../../services/api'

interface Stock {
  id: string
  product_id: string
  product_code: string
  product_name: string
  warehouse_id: string
  warehouse_code: string
  warehouse_name: string
  quantity: number
  min_stock: number
  max_stock: number
  status: string
  created_at?: string
  updated_at?: string
}

interface Warehouse {
  id: string
  warehouse_code: string
  name: string
}

interface Product {
  id: string
  product_code: string
  name: string
  brand?: string
}

const loading = ref(false)
const stocks = ref<Stock[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterWarehouse = ref('')
const filterStatus = ref('')
const warehouses = ref<Warehouse[]>([])

const showStockModal = ref(false)
const showAdjustModal = ref(false)
const showDeleteConfirm = ref(false)
const editingStock = ref<Stock | null>(null)
const adjustTargetStock = ref<Stock | null>(null)
const deleteTargetId = ref<string | null>(null)
const formLoading = ref(false)
const adjustLoading = ref(false)
const deleteLoading = ref(false)

const productKeyword = ref('')
const productSearchResults = ref<Product[]>([])
const showProductDropdown = ref(false)
const selectedProduct = ref<Product | null>(null)

const stockForm = ref<Partial<Stock & { product_id: string; warehouse_id: string }>>({
  product_id: '',
  warehouse_id: '',
  quantity: 0,
  min_stock: 0,
  max_stock: 0
})

const adjustForm = ref({
  quantity_change: 0,
  is_add: true
})

const stockStatuses = [
  { value: 'normal', label: '正常' },
  { value: 'low_stock', label: '库存不足' },
  { value: 'out_of_stock', label: '缺货' },
  { value: 'overstock', label: '超额库存' }
]

const columns = [
  { key: 'product_code', label: '商品编码', width: '140px' },
  { key: 'product_name', label: '商品名称' },
  { key: 'warehouse_name', label: '所属仓库', width: '120px' },
  { key: 'quantity', label: '库存数量', width: '100px', align: 'right' as const },
  { key: 'min_stock', label: '最低库存', width: '100px', align: 'right' as const },
  { key: 'max_stock', label: '最高库存', width: '100px', align: 'right' as const },
  { key: 'status', label: '状态', width: '90px' }
]

const statusMap: Record<string, string> = {
  normal: '正常',
  low_stock: '库存不足',
  out_of_stock: '缺货',
  overstock: '超额'
}

const statusClassMap: Record<string, string> = {
  normal: 'normal',
  low_stock: 'warning',
  out_of_stock: 'danger',
  overstock: 'info'
}

const formatStatus = (status: string) => statusMap[status] || status
const getStatusClass = (status: string) => statusClassMap[status] || ''

const loadStocks = async () => {
  loading.value = true
  try {
    const res = await stockApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      warehouse_id: filterWarehouse.value || undefined,
      status: filterStatus.value || undefined
    })
    stocks.value = res.items.map((item: Stock) => ({
      ...item,
      status: formatStatus(item.status)
    }))
    total.value = res.total
  } catch (error) {
    console.error('加载库存列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadWarehouses = async () => {
  try {
    const res = await warehouseApi.list({ page: 1, page_size: 100 })
    warehouses.value = res.items
  } catch (error) {
    console.error('加载仓库列表失败:', error)
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadStocks()
}

const handleSearch = () => {
  page.value = 1
  loadStocks()
}

const hasActiveFilters = computed(() => {
  return !!(keyword.value || filterWarehouse.value || filterStatus.value)
})

const resetFilters = () => {
  keyword.value = ''
  filterWarehouse.value = ''
  filterStatus.value = ''
  page.value = 1
  loadStocks()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetStockForm = () => {
  stockForm.value = {
    product_id: '',
    warehouse_id: '',
    quantity: 0,
    min_stock: 0,
    max_stock: 0
  }
  editingStock.value = null
  selectedProduct.value = null
  productKeyword.value = ''
  productSearchResults.value = []
}

const searchProducts = async () => {
  if (!productKeyword.value.trim()) {
    productSearchResults.value = []
    return
  }
  try {
    const res = await productApi.search(productKeyword.value, 20)
    productSearchResults.value = res.result || []
    showProductDropdown.value = true
  } catch (error) {
    console.error('搜索商品失败:', error)
    productSearchResults.value = []
  }
}

const selectProduct = (product: Product) => {
  selectedProduct.value = product
  stockForm.value.product_id = product.id
  productKeyword.value = product.name
  showProductDropdown.value = false
}

const clearProductSelection = () => {
  selectedProduct.value = null
  stockForm.value.product_id = ''
  productKeyword.value = ''
  productSearchResults.value = []
}

const handleProductInput = () => {
  stockForm.value.product_id = ''
  selectedProduct.value = null
  searchProducts()
}

const openCreateStock = () => {
  resetStockForm()
  showStockModal.value = true
}

const openEditStock = (stock: Stock) => {
  editingStock.value = stock
  selectedProduct.value = {
    id: stock.product_id,
    product_code: stock.product_code,
    name: stock.product_name
  }
  productKeyword.value = stock.product_name
  stockForm.value = {
    product_id: stock.product_id,
    warehouse_id: stock.warehouse_id,
    quantity: stock.quantity,
    min_stock: stock.min_stock,
    max_stock: stock.max_stock
  }
  showStockModal.value = true
}

const openAdjustStock = (stock: Stock) => {
  adjustTargetStock.value = stock
  adjustForm.value = { quantity_change: 0, is_add: true }
  showAdjustModal.value = true
}

const confirmDelete = (stockId: string) => {
  deleteTargetId.value = stockId
  showDeleteConfirm.value = true
}

const handleSaveStock = async () => {
  if (!stockForm.value.product_id) {
    window.showToast('请选择商品', 'warning')
    return
  }
  if (!stockForm.value.warehouse_id) {
    window.showToast('请选择仓库', 'warning')
    return
  }
  if (stockForm.value.quantity === undefined || stockForm.value.quantity < 0) {
    window.showToast('请输入有效的库存数量', 'warning')
    return
  }

  formLoading.value = true
  try {
    if (editingStock.value) {
      await stockApi.update(editingStock.value.id, stockForm.value)
      window.showToast('库存更新成功', 'success')
      const index = stocks.value.findIndex(s => s.id === editingStock.value!.id)
      if (index !== -1) {
        stocks.value[index] = {
          ...stocks.value[index],
          ...stockForm.value,
          product_code: selectedProduct.value?.product_code || stocks.value[index].product_code,
          product_name: selectedProduct.value?.name || stocks.value[index].product_name,
          warehouse_name: warehouses.value.find(w => w.id === stockForm.value.warehouse_id)?.name || stocks.value[index].warehouse_name
        }
      }
    } else {
      await stockApi.create(stockForm.value)
      window.showToast('库存创建成功', 'success')
      loadStocks()
    }
    showStockModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleAdjustStock = async () => {
  if (!adjustTargetStock.value) return
  if (adjustForm.value.quantity_change <= 0) {
    window.showToast('请输入有效的调整数量', 'warning')
    return
  }

  adjustLoading.value = true
  try {
    await stockApi.adjust(
      adjustTargetStock.value.id,
      adjustForm.value.quantity_change,
      adjustForm.value.is_add
    )
    window.showToast('库存调整成功', 'success')
    const index = stocks.value.findIndex(s => s.id === adjustTargetStock.value!.id)
    if (index !== -1) {
      const newQuantity = adjustForm.value.is_add
        ? stocks.value[index].quantity + adjustForm.value.quantity_change
        : stocks.value[index].quantity - adjustForm.value.quantity_change
      stocks.value[index] = {
        ...stocks.value[index],
        quantity: newQuantity
      }
    }
    showAdjustModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '调整失败', 'error')
  } finally {
    adjustLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await stockApi.delete(deleteTargetId.value)
    window.showToast('库存删除成功', 'success')
    stocks.value = stocks.value.filter(s => s.id !== deleteTargetId.value)
    total.value--
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  loadStocks()
  loadWarehouses()
})
</script>

<template>
  <div class="stock-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">库存管理</h2>
      <button class="primary-btn" @click="openCreateStock">新增库存</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索商品名、商品编号..."
            v-model="keyword"
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterWarehouse" @change="handleSearch">
            <option value="">全部仓库</option>
            <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </div>
        <div class="filter-item">
          <select class="filter-select" v-model="filterStatus" @change="handleSearch">
            <option value="">全部状态</option>
            <option v-for="s in stockStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
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
        <span class="filter-tag" v-if="filterWarehouse">
          仓库: {{ warehouses.find(w => w.id === filterWarehouse)?.name }}
          <button class="tag-close" @click="filterWarehouse = ''; handleSearch()">×</button>
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
            <th v-for="col in columns" :key="col.key" :style="{ width: col.width, textAlign: col.align || 'left' }">
              {{ col.label }}
            </th>
            <th style="width: 220px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="stocks.length === 0">
            <td :colspan="columns.length + 1" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="stock in stocks" :key="stock.id">
            <td>{{ stock.product_code }}</td>
            <td>{{ stock.product_name }}</td>
            <td>{{ stock.warehouse_name }}</td>
            <td class="number-cell">{{ stock.quantity }}</td>
            <td class="number-cell">{{ stock.min_stock }}</td>
            <td class="number-cell">{{ stock.max_stock }}</td>
            <td>
              <span class="status-tag" :class="getStatusClass(stock.status)">
                {{ stock.status }}
              </span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-link" @click="openAdjustStock(stock)">调整</button>
                <button class="btn-link" @click="openEditStock(stock)">编辑</button>
                <button class="btn-link danger" @click="confirmDelete(stock.id)">删除</button>
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
      <button class="pagination-btn" :disabled="stocks.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showStockModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingStock ? '编辑库存' : '新增库存' }}</h3>
          <button class="modal-close" @click="showStockModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>商品 *</label>
            <div class="product-search-container">
              <input
                type="text"
                v-model="productKeyword"
                placeholder="搜索商品名称或编号..."
                @input="handleProductInput"
                @focus="showProductDropdown = productSearchResults.length > 0"
                @blur="showProductDropdown = false"
              />
              <button v-if="selectedProduct" class="clear-btn" @click="clearProductSelection" type="button">×</button>
              <div class="product-dropdown" v-if="showProductDropdown">
                <div
                  v-for="product in productSearchResults"
                  :key="product.id"
                  class="product-option"
                  @mousedown="selectProduct(product)"
                >
                  <span class="product-name">{{ product.name }}</span>
                  <span class="product-code">{{ product.product_code }}</span>
                </div>
                <div v-if="productSearchResults.length === 0" class="no-results">
                  未找到商品
                </div>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>仓库 *</label>
            <select v-model="stockForm.warehouse_id">
              <option value="">请选择仓库</option>
              <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>库存数量 *</label>
              <input type="number" v-model="stockForm.quantity" min="0" placeholder="请输入数量" />
            </div>
            <div class="form-group">
              <label>最低库存</label>
              <input type="number" v-model="stockForm.min_stock" min="0" placeholder="预警阈值" />
            </div>
          </div>
          <div class="form-group">
            <label>最高库存</label>
            <input type="number" v-model="stockForm.max_stock" min="0" placeholder="预警阈值" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showStockModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveStock" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showAdjustModal">
      <div class="modal">
        <div class="modal-header">
          <h3>调整库存</h3>
          <button class="modal-close" @click="showAdjustModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="adjust-info" v-if="adjustTargetStock">
            <p>商品: {{ adjustTargetStock.product_name }}</p>
            <p>仓库: {{ adjustTargetStock.warehouse_name }}</p>
            <p>当前库存: {{ adjustTargetStock.quantity }}</p>
          </div>
          <div class="form-group">
            <label>调整方式</label>
            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="adjustForm.is_add" :value="true" />
                <span>增加</span>
              </label>
              <label class="radio-label">
                <input type="radio" v-model="adjustForm.is_add" :value="false" />
                <span>减少</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>调整数量 *</label>
            <input type="number" v-model="adjustForm.quantity_change" min="1" placeholder="请输入调整数量" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAdjustModal = false">取消</button>
          <button class="btn-primary" @click="handleAdjustStock" :disabled="adjustLoading">
            {{ adjustLoading ? '处理中...' : '确认调整' }}
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
          <p>确定要删除该库存记录吗？此操作不可恢复。</p>
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
.stock-workspace {
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

.number-cell {
  text-align: right !important;
  font-family: monospace;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.warning {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

.status-tag.danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.status-tag.info {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--accent-blue);
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
  max-width: 500px;
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

.adjust-info {
  background-color: var(--bg-secondary);
  padding: 12px;
  border-radius: var(--radius-sm);
}

.adjust-info p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--text-primary);
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.radio-label input {
  width: 16px;
  height: 16px;
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

.product-search-container {
  position: relative;
}

.product-search-container input {
  width: 100%;
  padding: 10px 12px;
  padding-right: 32px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.product-search-container input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  background-color: var(--accent-red);
  color: white;
}

.product-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 240px;
  overflow-y: auto;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-hover);
  z-index: 100;
  margin-top: 4px;
}

.product-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.product-option:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.product-option .product-name {
  font-size: 14px;
  color: var(--text-primary);
}

.product-option .product-code {
  font-size: 12px;
  color: var(--text-muted);
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
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
