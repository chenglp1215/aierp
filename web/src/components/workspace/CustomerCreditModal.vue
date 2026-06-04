<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { customerApi, type CustomerCredit } from '../../services/api'

const props = defineProps<{
  visible: boolean
  customerData: any | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const saving = ref(false)

const form = reactive<CustomerCredit>({
  credit_days: 0,
  credit_limit: 0
})

watch(() => props.visible, (val) => {
  if (val && props.customerData) {
    form.credit_days = props.customerData.credit_days ?? 0
    form.credit_limit = props.customerData.credit_limit ?? 0
  }
})

const close = () => emit('update:visible', false)

const handleSave = async () => {
  if (!props.customerData?.id) return
  if (form.credit_days < 0) {
    window.showToast('账期天数不能为负数', 'warning')
    return
  }
  if (form.credit_limit < 0) {
    window.showToast('信用额度不能为负数', 'warning')
    return
  }

  saving.value = true
  try {
    await customerApi.setCredit(Number(props.customerData.id), { credit_days: form.credit_days, credit_limit: form.credit_limit })
    window.showToast('账期额度设置成功', 'success')
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
    <div class="modal credit-modal">
      <div class="modal-header">
        <h3>账期额度设置</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="current-status" v-if="customerData">
          <span>当前超账期状态：</span>
          <span :class="{ 'text-danger': customerData.is_overdue === 1 }">
            {{ customerData.is_overdue === 1 ? '是' : '否' }}
          </span>
        </div>
        <div class="form-group">
          <label>账期天数</label>
          <input type="number" v-model.number="form.credit_days" min="0" placeholder="请输入账期天数" />
          <span class="hint">0表示不限制账期</span>
        </div>
        <div class="form-group">
          <label>信用额度</label>
          <input type="number" v-model.number="form.credit_limit" min="0" step="0.01" placeholder="请输入信用额度" />
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

.credit-modal {
  max-width: 420px;
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

.current-status {
  background-color: var(--color-neutral-bg);
  padding: 10px 12px;
  border-radius: var(--radius-xs);
  font-size: 13px;
  color: var(--color-ink);
}

.text-danger {
  color: var(--color-danger);
  font-weight: 600;
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

.form-group input {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus {
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