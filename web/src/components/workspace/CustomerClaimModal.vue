<script setup lang="ts">
import { ref } from 'vue'
import { customerApi } from '../../services/api'

const props = defineProps<{
  visible: boolean
  customerData: any | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'claim-success'): void
}>()

const loading = ref(false)

const close = () => emit('update:visible', false)

const handleClaim = async () => {
  if (!props.customerData?.id) return
  loading.value = true
  try {
    await customerApi.claim(Number(props.customerData.id))
    window.showToast('认领成功', 'success')
    emit('claim-success')
    close()
  } catch (e: any) {
    window.showToast(e.message || '认领失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="close">
    <div class="modal confirm-modal">
      <div class="modal-header">
        <h3>客户认领</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <p>确认认领以下客户？</p>
        <div class="confirm-info">
          <div><span class="label">客户名称：</span>{{ customerData?.customer_name }}</div>
          <div><span class="label">客户编码：</span>{{ customerData?.customer_code }}</div>
          <div v-if="customerData?.sales_user_name"><span class="label">当前业务员：</span>{{ customerData.sales_user_name }}</div>
        </div>
        <p class="hint">认领后客户将从公共池恢复为正常状态，您将成为该客户的业务员。</p>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="handleClaim" :disabled="loading">
          {{ loading ? '认领中...' : '确认认领' }}
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

.confirm-modal {
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
  gap: 12px;
}

.modal-body p {
  font-size: 14px;
  color: var(--color-ink);
  margin: 0;
}

.confirm-info {
  background-color: var(--color-neutral-bg);
  padding: 12px;
  border-radius: var(--radius-xs);
  font-size: 13px;
  color: var(--color-ink);
}

.confirm-info .label {
  color: var(--color-muted);
}

.hint {
  color: var(--color-warning);
  font-size: 13px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-hairline);
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