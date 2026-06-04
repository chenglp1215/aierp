<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { customerApi, type CustomerOrderDefaults } from '../../services/api'

const props = defineProps<{
  visible: boolean
  customerData: any | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const saving = ref(false)
const shippingAddresses = ref<any[]>([])
const invoiceInfos = ref<any[]>([])

const form = reactive<CustomerOrderDefaults>({
  default_shipping_address_id: null,
  default_invoice_info_id: null,
  settlement_method: 1,
  default_tax_rate: null
})

watch(() => props.visible, async (val) => {
  if (val && props.customerData) {
    // 加载客户的收货地址和开票信息列表
    try {
      const res = await customerApi.getById(String(props.customerData.id))
      shippingAddresses.value = res?.shipping_addresses || []
      invoiceInfos.value = res?.invoice_infos || []
    } catch (e) {
      shippingAddresses.value = props.customerData.shipping_addresses || []
      invoiceInfos.value = props.customerData.invoice_infos || []
    }
    // 填充当前值
    form.default_shipping_address_id = props.customerData.default_shipping_address_id || null
    form.default_invoice_info_id = props.customerData.default_invoice_info_id || null
    form.settlement_method = props.customerData.settlement_method ?? 1
    form.default_tax_rate = props.customerData.default_tax_rate ?? null
  }
})

const close = () => emit('update:visible', false)

const handleSave = async () => {
  if (!props.customerData?.id) return
  saving.value = true
  try {
    await customerApi.setOrderDefaults(Number(props.customerData.id), { ...form })
    window.showToast('订单默认值设置成功', 'success')
    emit('saved')
    close()
  } catch (e: any) {
    window.showToast(e.message || '设置失败', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="close">
    <div class="modal defaults-modal">
      <div class="modal-header">
        <h3>订单默认值设置</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>默认收货地址</label>
          <select v-model="form.default_shipping_address_id">
            <option :value="null">请选择收货地址</option>
            <option v-for="addr in shippingAddresses" :key="addr.id" :value="Number(addr.id)">
              {{ addr.receiver }} - {{ [addr.province, addr.city, addr.district, addr.address].filter(Boolean).join('') }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>默认开票信息</label>
          <select v-model="form.default_invoice_info_id">
            <option :value="null">请选择开票信息</option>
            <option v-for="inv in invoiceInfos" :key="inv.id" :value="Number(inv.id)">
              {{ inv.invoice_title }} - {{ inv.tax_number }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>结算方式</label>
          <select v-model="form.settlement_method">
            <option :value="1">月结</option>
            <option :value="2">现结</option>
            <option :value="3">预付</option>
          </select>
        </div>
        <div class="form-group">
          <label>默认税率</label>
          <input type="number" v-model.number="form.default_tax_rate" step="0.01" min="0" max="100" placeholder="0 - 100" />
          <span class="hint">税率百分比，如 13 表示 13%</span>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="handleSave" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  box-shadow: var(--shadow-modal);
}

.defaults-modal {
  max-width: 500px;
  width: 95%;
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

.form-group input,
.form-group select {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.hint {
  font-size: 12px;
  color: var(--color-muted);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-xs);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-xs);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>