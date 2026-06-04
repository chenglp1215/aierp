<script setup lang="ts">
import { ref, watch } from 'vue'
import { customerApi } from '../../services/api'

const props = defineProps<{
  visible: boolean
  customerData: any | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const saving = ref(false)
const memberAccount = ref('')

watch(() => props.visible, (val) => {
  if (val && props.customerData) {
    memberAccount.value = props.customerData.member_account || ''
  }
})

const close = () => emit('update:visible', false)

const handleSave = async () => {
  if (!props.customerData?.id) return
  if (!memberAccount.value.trim()) {
    window.showToast('会员账号不能为空', 'warning')
    return
  }

  saving.value = true
  try {
    await customerApi.registerMember(Number(props.customerData.id), { member_account: memberAccount.value.trim() })
    window.showToast('会员账号设置成功', 'success')
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
    <div class="modal member-modal">
      <div class="modal-header">
        <h3>注册会员</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="current-info" v-if="customerData?.member_account">
          <span>当前会员账号：</span>
          <span class="current-value">{{ customerData.member_account }}</span>
        </div>
        <div class="form-group">
          <label>会员账号 <span class="required">*</span></label>
          <input v-model="memberAccount" placeholder="请输入会员账号" maxlength="100" />
          <span class="hint">会员账号用于登录商城，不可与其他客户重复</span>
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

.member-modal {
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

.current-info {
  background-color: var(--color-neutral-bg);
  padding: 10px 12px;
  border-radius: var(--radius-xs);
  font-size: 13px;
  color: var(--color-ink);
}

.current-value {
  color: var(--color-interactive);
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

.form-group .required {
  color: var(--color-danger);
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