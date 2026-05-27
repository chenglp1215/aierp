<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../services/api'
import { useTheme } from '../hooks'

const router = useRouter()
useTheme()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const rememberMe = ref(false)

onMounted(() => {
  const savedUsername = localStorage.getItem('remembered_username')
  const savedPassword = localStorage.getItem('remembered_password')
  if (savedUsername) {
    username.value = savedUsername
    rememberMe.value = true
  }
  if (savedPassword && savedUsername) {
    password.value = savedPassword
  }
})

const validateForm = (): boolean => {
  if (!username.value.trim()) {
    error.value = '请输入用户名'
    return false
  }
  if (!password.value) {
    error.value = '请输入密码'
    return false
  }
  if (password.value.length < 6) {
    error.value = '密码长度不能少于6位'
    return false
  }
  return true
}

const handleLogin = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await authApi.login({
      username: username.value.trim(),
      password: password.value
    })

    if (rememberMe.value) {
      localStorage.setItem('remembered_username', username.value.trim())
      localStorage.setItem('remembered_password', password.value)
    } else {
      localStorage.removeItem('remembered_username')
      localStorage.removeItem('remembered_password')
    }

    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    localStorage.setItem('token_expires_at', String(Date.now() + response.expires_in * 1000))

    router.push('/dashboard')
  } catch (err: any) {
    error.value = err.message || '登录失败，请检查用户名和密码'
    password.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-background">
      <div class="bg-gradient"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-area">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
          </div>
          <h1>AI MDR 平台</h1>
        </div>
        <p class="subtitle">智能销售助手</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"></path>
            </svg>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              :disabled="loading"
              autocomplete="username"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"></path>
            </svg>
            <input
              id="password"
              v-model="password"
              type="password"
              placeholder="请输入密码"
              :disabled="loading"
              autocomplete="current-password"
            />
          </div>
        </div>

        <div class="form-options">
          <label class="checkbox-wrapper">
            <input type="checkbox" v-model="rememberMe" :disabled="loading" />
            <span class="checkmark"></span>
            <span class="checkbox-label">记住密码</span>
          </label>
        </div>

        <div v-if="error" class="error-message">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"></path>
          </svg>
          <span>{{ error }}</span>
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>

      <div class="login-footer">
        <p>智能 · 高效 · 安全</p>
      </div>
    </div>

    <div class="login-tips">
      <p>默认账号: admin / admin123</p>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--color-canvas) 0%, var(--color-neutral-bg) 50%, var(--color-canvas) 100%);
}

[data-theme="light"] .bg-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 120, 212, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 120, 212, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

.login-card {
  position: relative;
  z-index: 1;
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-hairline);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--color-interactive) 0%, #764ba2 100%);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink);
  margin: 0;
}

.subtitle {
  font-size: 14px;
  color: var(--color-muted);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-muted);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 20px;
  height: 20px;
  color: var(--color-muted);
  pointer-events: none;
}

.form-group input {
  width: 100%;
  padding: 14px 16px 14px 44px;
  background: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--color-ink);
  transition: all var(--transition-fast);
}

.form-group input::placeholder {
  color: var(--color-muted);
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-interactive);
  box-shadow: 0 0 0 3px rgba(24, 99, 220, 0.15);
}

.form-group input:disabled {
  background-color: var(--color-canvas);
  cursor: not-allowed;
  opacity: 0.7;
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -8px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.checkbox-wrapper input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: relative;
  width: 18px;
  height: 18px;
  background: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.checkbox-wrapper:hover .checkmark {
  border-color: var(--color-interactive);
}

.checkbox-wrapper input:checked ~ .checkmark {
  background: var(--color-interactive);
  border-color: var(--color-interactive);
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-wrapper input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-label {
  font-size: 13px;
  color: var(--color-muted);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.error-message svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  background: linear-gradient(135deg, var(--color-interactive) 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-top: 8px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(24, 99, 220, 0.4);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-hairline);
}

.login-footer p {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

.login-tips {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1;
}

.login-tips p {
  font-size: 12px;
  color: var(--color-muted);
  margin: 0;
}

@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
    margin: 16px;
    max-width: calc(100% - 32px);
  }

  .login-header h1 {
    font-size: 24px;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
  }

  .logo-icon svg {
    width: 24px;
    height: 24px;
  }
}
</style>
