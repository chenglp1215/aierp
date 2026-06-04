<script setup lang="ts">
import { ref } from 'vue'
import { type ShippingAddress } from '../../services/api'
import ProvinceCitySelector from './ProvinceCitySelector.vue'

interface Props {
  customerId: string
  shippingAddresses: ShippingAddress[]
  readonly?: boolean
}

interface Emits {
  (e: 'add', data: ShippingAddress): Promise<void>
  (e: 'update', addressId: string, data: ShippingAddress): Promise<void>
  (e: 'delete', addressId: string): Promise<void>
  (e: 'set-default', addressId: string): Promise<void>
  (e: 'update:shippingAddresses', addresses: ShippingAddress[]): void
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<Emits>()

const editingAddressId = ref<string | null>(null)
const editingAddressBackup = ref<ShippingAddress | null>(null)
const isAddingNewAddress = ref(false)
const newAddressForm = ref<ShippingAddress>({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  address: '',
  is_default: false
})
const formLoading = ref(false)

const provinceCityValueForNew = ref({
  province: '',
  city: ''
})

const startAddNew = () => {
  isAddingNewAddress.value = true
  editingAddressId.value = null
  newAddressForm.value = {
    receiver: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    address: '',
    is_default: props.shippingAddresses.length === 0
  }
  provinceCityValueForNew.value = {
    province: '',
    city: ''
  }
}

const cancelAddNew = () => {
  isAddingNewAddress.value = false
  newAddressForm.value = {
    receiver: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    address: '',
    is_default: false
  }
}

const startEdit = (addr: ShippingAddress) => {
  editingAddressId.value = addr.id || null
  editingAddressBackup.value = { ...addr }
}

const cancelEdit = () => {
  if (editingAddressBackup.value) {
    const index = props.shippingAddresses.findIndex(a => a.id === editingAddressBackup.value!.id)
    if (index !== -1) {
      props.shippingAddresses[index] = editingAddressBackup.value
    }
  }
  editingAddressId.value = null
  editingAddressBackup.value = null
}

const validateNewForm = (): boolean => {
  if (!newAddressForm.value.receiver?.trim()) {
    window.showToast('请输入收货人姓名', 'warning')
    return false
  }
  if (!newAddressForm.value.phone?.trim()) {
    window.showToast('请输入收货电话', 'warning')
    return false
  }
  if (!newAddressForm.value.province?.trim()) {
    window.showToast('请选择收货省份', 'warning')
    return false
  }
  if (!newAddressForm.value.city?.trim()) {
    window.showToast('请选择收货城市', 'warning')
    return false
  }
  if (!newAddressForm.value.address?.trim()) {
    window.showToast('请输入详细地址', 'warning')
    return false
  }
  return true
}

const handleAddNew = async () => {
  if (!validateNewForm()) return

  if (!props.customerId) {
    const updatedAddresses = [...props.shippingAddresses]
    if (newAddressForm.value.is_default) {
      updatedAddresses.forEach(addr => addr.is_default = false)
    }
    updatedAddresses.push({ ...newAddressForm.value, id: `temp_${Date.now()}` })
    emit('update:shippingAddresses', updatedAddresses)
    cancelAddNew()
    return
  }

  formLoading.value = true
  try {
    await emit('add', { ...newAddressForm.value })
    cancelAddNew()
  } catch (error: any) {
    window.showToast(error.message || '添加失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const validateEditForm = (addr: ShippingAddress): boolean => {
  if (!addr.receiver?.trim()) {
    window.showToast('请输入收货人姓名', 'warning')
    return false
  }
  if (!addr.phone?.trim()) {
    window.showToast('请输入收货电话', 'warning')
    return false
  }
  if (!addr.province?.trim()) {
    window.showToast('请选择收货省份', 'warning')
    return false
  }
  if (!addr.city?.trim()) {
    window.showToast('请选择收货城市', 'warning')
    return false
  }
  if (!addr.address?.trim()) {
    window.showToast('请输入详细地址', 'warning')
    return false
  }
  return true
}

const handleSaveEdit = async (addr: ShippingAddress) => {
  if (!validateEditForm(addr)) return

  if (!props.customerId) {
    const updatedAddresses = props.shippingAddresses.map(a => {
      if (a.id === addr.id) {
        return { ...a, ...addr }
      }
      if (addr.is_default && a.is_default) {
        return { ...a, is_default: false }
      }
      return a
    })
    emit('update:shippingAddresses', updatedAddresses)
    editingAddressId.value = null
    editingAddressBackup.value = null
    return
  }

  formLoading.value = true
  try {
    await emit('update', addr.id!, addr)
    editingAddressId.value = null
    editingAddressBackup.value = null
  } catch (error: any) {
    window.showToast(error.message || '更新失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async (addressId: string) => {
  if (!props.customerId) {
    const updatedAddresses = props.shippingAddresses.filter(a => a.id !== addressId)
    emit('update:shippingAddresses', updatedAddresses)
    return
  }
  try {
    await emit('delete', addressId)
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

const handleSetDefault = async (addressId: string) => {
  if (!props.customerId) {
    const updatedAddresses = props.shippingAddresses.map(a => ({
      ...a,
      is_default: a.id === addressId
    }))
    emit('update:shippingAddresses', updatedAddresses)
    return
  }
  try {
    await emit('set-default', addressId)
  } catch (error: any) {
    window.showToast(error.message || '设置失败', 'error')
  }
}

const getProvinceCityForEdit = (addr: ShippingAddress) => ({
  province: addr.province || '',
  city: addr.city || ''
})

const setProvinceCityForEdit = (addr: ShippingAddress, val: { province?: string; city?: string }) => {
  addr.province = val.province || ''
  addr.city = val.city || ''
}
</script>

<template>
  <div class="shipping-address-manager">
    <div class="address-list">
      <table class="address-table">
        <thead>
          <tr>
            <th>收货人</th>
            <th>电话</th>
            <th>省份</th>
            <th>城市</th>
            <th>详细地址</th>
            <th>默认</th>
            <th v-if="!readonly">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="shippingAddresses.length === 0 && !isAddingNewAddress">
            <td :colspan="readonly ? 6 : 7" class="empty-cell">暂无收货地址</td>
          </tr>

          <tr v-for="addr in shippingAddresses" :key="addr.id">
            <template v-if="editingAddressId === addr.id">
              <td><input type="text" v-model="addr.receiver" class="inline-input" placeholder="收货人" /></td>
              <td><input type="text" v-model="addr.phone" class="inline-input" placeholder="电话" /></td>
              <td colspan="2">
                <ProvinceCitySelector
                  :model-value="getProvinceCityForEdit(addr)"
                  @update:model-value="setProvinceCityForEdit(addr, $event)"
                  :placeholder="{ province: '省份', city: '城市' }"
                />
              </td>
              <td><input type="text" v-model="addr.address" class="inline-input" placeholder="详细地址" /></td>
              <td><input type="checkbox" v-model="addr.is_default" class="inline-checkbox" /></td>
              <td v-if="!readonly">
                <button class="btn-link" @click="handleSaveEdit(addr)">保存</button>
                <button class="btn-link" @click="cancelEdit">取消</button>
              </td>
            </template>
            <template v-else>
              <td>{{ addr.receiver }}</td>
              <td>{{ addr.phone }}</td>
              <td>{{ addr.province || '-' }}</td>
              <td>{{ addr.city || '-' }}</td>
              <td>{{ [addr.province, addr.city, addr.district, addr.address].filter(Boolean).join('') }}</td>
              <td>{{ addr.is_default ? '是' : '否' }}</td>
              <td v-if="!readonly">
                <button v-if="!addr.is_default" class="btn-link" @click="handleSetDefault(addr.id!)">设为默认</button>
                <button class="btn-link" @click="startEdit(addr)">编辑</button>
                <button class="btn-link danger" @click="handleDelete(addr.id!)">删除</button>
              </td>
            </template>
          </tr>

          <tr v-if="isAddingNewAddress">
            <td><input type="text" v-model="newAddressForm.receiver" class="inline-input" placeholder="收货人 *" /></td>
            <td><input type="text" v-model="newAddressForm.phone" class="inline-input" placeholder="电话 *" /></td>
            <td colspan="2">
              <ProvinceCitySelector
                v-model="provinceCityValueForNew"
                @update:model-value="(val: any) => {
                  newAddressForm.province = val.province || ''
                  newAddressForm.city = val.city || ''
                }"
                :placeholder="{ province: '省份 *', city: '城市 *' }"
              />
            </td>
            <td><input type="text" v-model="newAddressForm.address" class="inline-input" placeholder="详细地址 *" /></td>
            <td><input type="checkbox" v-model="newAddressForm.is_default" class="inline-checkbox" /></td>
            <td v-if="!readonly">
              <button class="btn-link" @click="handleAddNew" :disabled="formLoading">保存</button>
              <button class="btn-link" @click="cancelAddNew">取消</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!readonly && !isAddingNewAddress" class="add-section">
      <button class="btn-secondary btn-sm" @click="startAddNew">
        + 添加收货地址
      </button>
    </div>
  </div>
</template>

<style scoped>
.shipping-address-manager {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.address-list {
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.address-table {
  width: 100%;
  border-collapse: collapse;
}

.address-table th,
.address-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
  font-size: 13px;
}

.address-table th {
  font-weight: 500;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.address-table td {
  color: var(--color-ink);
}

.address-table tbody tr:last-child td {
  border-bottom: none;
}

.address-table tbody tr:hover {
  background-color: rgba(24, 99, 220, 0.06);
}

.empty-cell {
  text-align: center;
  padding: 24px;
  color: var(--color-muted);
  background-color: var(--color-neutral-bg);
}

.inline-input {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  font-size: 13px;
}

.inline-input:focus {
  outline: none;
  border-color: var(--color-interactive);
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

.btn-secondary {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 13px;
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .address-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
