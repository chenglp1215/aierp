<script setup lang="ts">
import { ref, watch } from 'vue'
import { authApi } from '../services/api'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

interface UserData {
  id: number
  username: string
  email: string
  phone?: string
  full_name?: string
  roles?: Array<{ id: number; name: string; code: string }>
}

const loading = ref(false)
const saving = ref(false)
const userData = ref<UserData | null>(null)
const email = ref('')
const newPassword = ref('')

const loadUserData = async () => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return

  try {
    const user = JSON.parse(userStr)
    loading.value = true
    const res = await authApi.getUser(String(user.id))
    userData.value = res
    email.value = res.email || ''
    newPassword.value = ''
  } catch (error) {
    console.error('加载用户信息失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!userData.value) return

  if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    window.showToast('请输入有效的邮箱地址', 'warning')
    return
  }

  if (newPassword.value && newPassword.value.length < 6) {
    window.showToast('密码长度不能少于6位', 'warning')
    return
  }

  saving.value = true
  try {
    const data: any = {
      email: email.value || undefined
    }
    if (newPassword.value) {
      data.new_password = newPassword.value
    }
    await authApi.updateUser(String(userData.value.id), data)
    window.showToast('保存成功', 'success')
    emit('saved')
    emit('close')
  } catch (error: any) {
    window.showToast(error.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  emit('close')
}

watch(() => props.visible, (val) => {
  if (val) {
    loadUserData()
  }
})
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="handleClose">
    <div class="modal">
      <div class="modal-header">
        <h3>用户设置</h3>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div v-if="loading" class="loading-cell">加载中...</div>
        <template v-else-if="userData">
          <div class="form-row">
            <div class="form-group">
              <label>用户名</label>
              <input type="text" :value="userData.username" disabled />
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="email" v-model="email" placeholder="请输入邮箱" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>手机</label>
              <input type="text" :value="userData.phone || '-'" disabled />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input type="text" :value="userData.full_name || '-'" disabled />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>角色</label>
              <input type="text" :value="userData.roles?.map(r => r.name).join(', ') || '-'" disabled />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input type="password" v-model="newPassword" placeholder="留空则不修改" autocomplete="new-password" />
            </div>
          </div>
        </template>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="handleClose">取消</button>
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
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 600px;
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

.form-group input {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-group input:focus {
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

.loading-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}
</style>