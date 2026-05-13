<script setup lang="ts">
defineOptions({ name: 'CustomerDiscountWorkspace' })

import { ref, computed, onMounted, onUnmounted, onActivated } from 'vue'
import { customerDiscountApi, brandApi } from '../../services/api'

// ==================== Props ====================
const props = defineProps<{
  customerId?: string
  customerName?: string
}>()

const emit = defineEmits<{
  back: []
  navigate: [id: string, extraData?: Record<string, any>]
}>()

// ==================== 列表相关 ====================
const loading = ref(false)
const discounts = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

// ==================== 弹窗相关 ====================
const showAddModal = ref(false)
const formLoading = ref(false)
const brands = ref<any[]>([])

// ==================== 表单数据 ====================
const discountForm = ref({
  brand_id: '',
  discount_value: 0.85,
  is_active: true
})

// ==================== 计算属性 ====================
const customerTitle = computed(() => {
  return props.customerName ? `${props.customerName} - 折扣设置` : '折扣设置'
})

// ==================== 加载数据 ====================
const loadDiscounts = async () => {
  if (!props.customerId) return
  
  loading.value = true
  try {
    const res = await customerDiscountApi.list({
      page: page.value,
      page_size: pageSize.value,
      customer_id: props.customerId
    })
    discounts.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载折扣列表失败:', error)
    window.showToast('加载折扣列表失败', 'error')
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

// ==================== 分页处理 ====================
const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadDiscounts()
}

// ==================== 弹窗操作 ====================
const openAddModal = () => {
  discountForm.value = {
    brand_id: '',
    discount_value: 0.85,
    is_active: true
  }
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
}

// ==================== 保存折扣 ====================
const validateForm = (): boolean => {
  if (!discountForm.value.brand_id) {
    window.showToast('请选择品牌', 'warning')
    return false
  }
  if (!discountForm.value.discount_value || discountForm.value.discount_value <= 0 || discountForm.value.discount_value > 1) {
    window.showToast('折扣值必须在0-1之间', 'warning')
    return false
  }
  return true
}

const handleSaveDiscount = async () => {
  if (!validateForm()) return
  if (!props.customerId) return

  formLoading.value = true
  try {
    const data = {
      customer_id: props.customerId,
      brand_id: discountForm.value.brand_id,
      discount_value: discountForm.value.discount_value,
      is_active: discountForm.value.is_active
    }

    await customerDiscountApi.create(data)
    window.showToast('折扣添加成功', 'success')
    closeAddModal()
    loadDiscounts()
  } catch (error: any) {
    window.showToast(error.message || '添加折扣失败', 'error')
  } finally {
    formLoading.value = false
  }
}

// ==================== 删除折扣 ====================
const handleDelete = async (discountId: string) => {
  if (!confirm('确定要删除这个折扣配置吗？')) return

  try {
    await customerDiscountApi.delete(discountId)
    window.showToast('折扣删除成功', 'success')
    loadDiscounts()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

// ==================== 切换状态 ====================
const handleToggleStatus = async (discount: any) => {
  try {
    await customerDiscountApi.toggleStatus(discount.id, !discount.is_active)
    window.showToast(discount.is_active ? '折扣已停用' : '折扣已启用', 'success')
    loadDiscounts()
  } catch (error: any) {
    window.showToast(error.message || '状态切换失败', 'error')
  }
}

// ==================== 返回操作 ====================
const handleBack = () => {
  emit('back')
}

// ==================== 生命周期 ====================
// 使用 onActivated 确保每次进入页面都会加载数据（KeepAlive 缓存时有效）
onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
  loadDiscounts()
  loadBrands()
})

onActivated(() => {
  if (props.customerId) {
    loadDiscounts()
    loadBrands()
  }
})

// 键盘事件
const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    closeAddModal()
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})

// ==================== 工具函数 ====================
const formatDiscount = (value: number) => {
  return `${(value * 100).toFixed(0)}%`
}
</script>

<template>
  <div class="customer-discount-workspace">
    <!-- 页面标题 -->
    <div class="workspace-header">
      <div class="header-left">
        <button class="back-btn" @click="handleBack">
          <span class="back-icon">←</span> 返回客户列表
        </button>
        <h2 class="workspace-title">{{ customerTitle }}</h2>
      </div>
      <div class="header-actions">
        <button class="icon-btn" @click="loadDiscounts" title="刷新">
          <span class="refresh-icon">↻</span>
        </button>
        <button class="primary-btn" @click="openAddModal">添加折扣</button>
      </div>
    </div>

    <!-- 折扣列表 -->
    <div class="table-section" style="position: relative;">
      <div v-if="loading" class="table-loading-overlay">
        <div class="table-loading-content">加载中...</div>
      </div>
      <vxe-table
        :data="discounts"
        :column-config="{ resizable: true }"
      >
        <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center col--header-center" />
        <vxe-column field="brand_name" title="品牌" min-width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            {{ row.brand_name || row.brand_id }}
          </template>
        </vxe-column>
        <vxe-column field="discount_value" title="折扣" min-width="100" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="discount-value">{{ formatDiscount(row.discount_value) }}</span>
          </template>
        </vxe-column>
        <vxe-column field="is_active" title="状态" min-width="80" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="status-tag" :class="row.is_active ? 'active' : 'inactive'">
              {{ row.is_active ? '生效' : '停用' }}
            </span>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="180" fixed="right" class-name="col--center col--header-center">
          <template #default="{ row }">
            <span class="action-btns">
              <button class="btn-link" @click="handleToggleStatus(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </button>
              <button class="btn-link danger" @click="handleDelete(row.id)">删除</button>
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

    <!-- 添加折扣弹窗 -->
    <div class="modal-overlay" v-if="showAddModal" @click.self="closeAddModal">
      <div class="modal add-modal">
        <div class="modal-header">
          <h3>添加折扣</h3>
          <button class="modal-close" @click="closeAddModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>品牌 <span class="required">*</span></label>
            <select v-model="discountForm.brand_id">
              <option value="">请选择品牌</option>
              <option v-for="brand in brands" :key="brand.id" :value="brand.id">
                {{ brand.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>折扣值 <span class="required">*</span></label>
            <div class="discount-input-group">
              <input
                type="number"
                v-model.number="discountForm.discount_value"
                step="0.01"
                min="0"
                max="1"
                placeholder="请输入折扣值（0-1之间）"
              />
              <span class="discount-hint">如：0.85 表示 85 折</span>
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="discountForm.is_active" />
              <span>启用折扣</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeAddModal">取消</button>
          <button class="btn-primary" @click="handleSaveDiscount" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.customer-discount-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background-color: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.refresh-icon {
  font-size: 18px;
  line-height: 1;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background-color: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.back-icon {
  font-size: 16px;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
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

.discount-value {
  font-weight: 600;
  color: var(--accent-blue);
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
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
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
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.add-modal {
  max-width: 500px;
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
  gap: 16px;
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

.discount-input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.discount-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
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
</style>