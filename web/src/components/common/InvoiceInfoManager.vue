<script setup lang="ts">
import { ref } from 'vue'
import { type InvoiceInfo } from '../../services/api'

interface Props {
  customerId: string
  invoiceInfos: InvoiceInfo[]
  readonly?: boolean
}

interface Emits {
  (e: 'add', data: InvoiceInfo): Promise<void>
  (e: 'update', invoiceId: string, data: InvoiceInfo): Promise<void>
  (e: 'delete', invoiceId: string): Promise<void>
  (e: 'set-default', invoiceId: string): Promise<void>
  (e: 'update:invoiceInfos', invoiceInfos: InvoiceInfo[]): void
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<Emits>()

const editingInvoiceId = ref<string | null>(null)
const editingInvoiceBackup = ref<InvoiceInfo | null>(null)
const isAddingNewInvoice = ref(false)
const newInvoiceForm = ref<InvoiceInfo>({
  invoice_title: '',
  tax_number: '',
  bank_name: '',
  bank_account: '',
  is_default: false
})
const formLoading = ref(false)

const startAddNew = () => {
  isAddingNewInvoice.value = true
  editingInvoiceId.value = null
  newInvoiceForm.value = {
    invoice_title: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    is_default: props.invoiceInfos.length === 0
  }
}

const cancelAddNew = () => {
  isAddingNewInvoice.value = false
  newInvoiceForm.value = {
    invoice_title: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    is_default: false
  }
}

const startEdit = (invoice: InvoiceInfo) => {
  editingInvoiceId.value = invoice.id || null
  editingInvoiceBackup.value = { ...invoice }
}

const cancelEdit = () => {
  if (editingInvoiceBackup.value) {
    const index = props.invoiceInfos.findIndex(i => i.id === editingInvoiceBackup.value!.id)
    if (index !== -1) {
      props.invoiceInfos[index] = editingInvoiceBackup.value
    }
  }
  editingInvoiceId.value = null
  editingInvoiceBackup.value = null
}

const validateNewForm = (): boolean => {
  if (!newInvoiceForm.value.invoice_title?.trim()) {
    window.showToast('请输入开票抬头', 'warning')
    return false
  }
  if (!newInvoiceForm.value.tax_number?.trim()) {
    window.showToast('请输入税号', 'warning')
    return false
  }
  return true
}

const handleAddNew = async () => {
  if (!validateNewForm()) return

  if (!props.customerId) {
    const updatedInfos = [...props.invoiceInfos]
    if (newInvoiceForm.value.is_default) {
      updatedInfos.forEach(info => info.is_default = false)
    }
    updatedInfos.push({ ...newInvoiceForm.value, id: `temp_${Date.now()}` })
    emit('update:invoiceInfos', updatedInfos)
    cancelAddNew()
    return
  }

  formLoading.value = true
  try {
    await emit('add', { ...newInvoiceForm.value })
    cancelAddNew()
  } catch (error: any) {
    window.showToast(error.message || '添加失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const validateEditForm = (invoice: InvoiceInfo): boolean => {
  if (!invoice.invoice_title?.trim()) {
    window.showToast('请输入开票抬头', 'warning')
    return false
  }
  if (!invoice.tax_number?.trim()) {
    window.showToast('请输入税号', 'warning')
    return false
  }
  return true
}

const handleSaveEdit = async (invoice: InvoiceInfo) => {
  if (!validateEditForm(invoice)) return

  if (!props.customerId) {
    const updatedInfos = props.invoiceInfos.map(i => {
      if (i.id === invoice.id) {
        return { ...i, ...invoice }
      }
      if (invoice.is_default && i.is_default) {
        return { ...i, is_default: false }
      }
      return i
    })
    emit('update:invoiceInfos', updatedInfos)
    editingInvoiceId.value = null
    editingInvoiceBackup.value = null
    return
  }

  formLoading.value = true
  try {
    await emit('update', invoice.id!, invoice)
    editingInvoiceId.value = null
    editingInvoiceBackup.value = null
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async (invoiceId: string) => {
  if (!props.customerId) {
    const updatedInfos = props.invoiceInfos.filter(i => i.id !== invoiceId)
    emit('update:invoiceInfos', updatedInfos)
    return
  }
  try {
    await emit('delete', invoiceId)
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

const handleSetDefault = async (invoiceId: string) => {
  if (!props.customerId) {
    const updatedInfos = props.invoiceInfos.map(i => ({
      ...i,
      is_default: i.id === invoiceId
    }))
    emit('update:invoiceInfos', updatedInfos)
    return
  }
  try {
    await emit('set-default', invoiceId)
  } catch (error: any) {
    window.showToast(error.message || '设置失败', 'error')
  }
}
</script>

<template>
  <div class="invoice-info-manager">
    <div class="invoice-list">
      <table class="invoice-table">
        <thead>
          <tr>
            <th>开票抬头</th>
            <th>税号</th>
            <th>开户行</th>
            <th>银行账号</th>
            <th>默认</th>
            <th v-if="!readonly">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="invoiceInfos.length === 0 && !isAddingNewInvoice">
            <td :colspan="readonly ? 5 : 6" class="empty-cell">暂无开票信息</td>
          </tr>

          <tr v-for="invoice in invoiceInfos" :key="invoice.id">
            <template v-if="editingInvoiceId === invoice.id">
              <td><input type="text" v-model="invoice.invoice_title" class="inline-input" placeholder="开票抬头" /></td>
              <td><input type="text" v-model="invoice.tax_number" class="inline-input" placeholder="税号" /></td>
              <td><input type="text" v-model="invoice.bank_name" class="inline-input" placeholder="开户行" /></td>
              <td><input type="text" v-model="invoice.bank_account" class="inline-input" placeholder="银行账号" /></td>
              <td><input type="checkbox" v-model="invoice.is_default" class="inline-checkbox" /></td>
              <td v-if="!readonly">
                <button class="btn-link" @click="handleSaveEdit(invoice)">保存</button>
                <button class="btn-link" @click="cancelEdit">取消</button>
              </td>
            </template>
            <template v-else>
              <td>{{ invoice.invoice_title }}</td>
              <td>{{ invoice.tax_number || '-' }}</td>
              <td>{{ invoice.bank_name || '-' }}</td>
              <td>{{ invoice.bank_account || '-' }}</td>
              <td>{{ invoice.is_default ? '是' : '否' }}</td>
              <td v-if="!readonly">
                <button v-if="!invoice.is_default" class="btn-link" @click="handleSetDefault(invoice.id!)">设为默认</button>
                <button class="btn-link" @click="startEdit(invoice)">编辑</button>
                <button class="btn-link danger" @click="handleDelete(invoice.id!)">删除</button>
              </td>
            </template>
          </tr>

          <tr v-if="isAddingNewInvoice">
            <td><input type="text" v-model="newInvoiceForm.invoice_title" class="inline-input" placeholder="开票抬头 *" /></td>
            <td><input type="text" v-model="newInvoiceForm.tax_number" class="inline-input" placeholder="税号 *" /></td>
            <td><input type="text" v-model="newInvoiceForm.bank_name" class="inline-input" placeholder="开户行" /></td>
            <td><input type="text" v-model="newInvoiceForm.bank_account" class="inline-input" placeholder="银行账号" /></td>
            <td><input type="checkbox" v-model="newInvoiceForm.is_default" class="inline-checkbox" /></td>
            <td v-if="!readonly">
              <button class="btn-link" @click="handleAddNew" :disabled="formLoading">保存</button>
              <button class="btn-link" @click="cancelAddNew">取消</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!readonly && !isAddingNewInvoice" class="add-section">
      <button class="btn-secondary btn-sm" @click="startAddNew">
        + 添加开票信息
      </button>
    </div>
  </div>
</template>

<style scoped>
.invoice-info-manager {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.invoice-list {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.invoice-table {
  width: 100%;
  border-collapse: collapse;
}

.invoice-table th,
.invoice-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  font-size: 13px;
}

.invoice-table th {
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.invoice-table td {
  color: var(--text-primary);
}

.invoice-table tbody tr:last-child td {
  border-bottom: none;
}

.invoice-table tbody tr:hover {
  background-color: rgba(0, 120, 212, 0.03);
}

.empty-cell {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.inline-input {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.inline-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.inline-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.add-section {
  margin-top: 4px;
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

.btn-secondary {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .invoice-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
