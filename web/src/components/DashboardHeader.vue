<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import UserSettingsDialog from './UserSettingsDialog.vue'

const emit = defineEmits<{
  logout: []
}>()

const showUserMenu = ref(false)
const showSettingsDialog = ref(false)
const userName = ref('')
const userRole = ref('')

const getUserFromStorage = () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      userName.value = user.username || '用户'
      userRole.value = user.roles?.[0]?.name || user.roles?.[0]?.code || 'User'
    } catch {
      userName.value = '用户'
      userRole.value = 'User'
    }
  }
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
}

const handleLogout = () => {
  showUserMenu.value = false
  emit('logout')
}

const handleSettings = () => {
  showUserMenu.value = false
  showSettingsDialog.value = true
}

const handleSettingsClose = () => {
  showSettingsDialog.value = false
}

const handleSettingsSaved = () => {
  window.dispatchEvent(new CustomEvent('user-updated'))
}

onMounted(() => {
  getUserFromStorage()
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('user-updated', handleUserUpdated)
  window.addEventListener('storage', handleStorageChange)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('user-updated', handleUserUpdated)
  window.removeEventListener('storage', handleStorageChange)
})

const handleUserUpdated = () => {
  getUserFromStorage()
}

const handleStorageChange = (event: StorageEvent) => {
  if (event.key === 'user') {
    getUserFromStorage()
  }
}
</script>

<template>
  <header class="dashboard-header">
    <div class="header-left">
      <slot name="breadcrumb"></slot>
    </div>

    <div class="header-right">
      <button class="header-action-btn" title="消息">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
        </svg>
        <span class="notification-badge">3</span>
      </button>

      <button class="header-action-btn" title="帮助">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
        </svg>
      </button>

      <div class="user-menu-container">
        <button class="user-btn" @click="toggleUserMenu">
          <div class="user-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div class="user-info">
            <span class="user-name">{{ userName }}</span>
            <span class="user-role">{{ userRole }}</span>
          </div>
          <svg class="dropdown-arrow" :class="{ rotated: showUserMenu }" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 10l5 5 5-5z"/>
          </svg>
        </button>

        <div v-if="showUserMenu" class="user-dropdown">
          <button class="dropdown-item" @click="handleSettings">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
            </svg>
            <span>设置</span>
          </button>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item logout" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
            </svg>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>

    <UserSettingsDialog
      :visible="showSettingsDialog"
      @close="handleSettingsClose"
      @saved="handleSettingsSaved"
    />
  </header>
</template>

<style scoped>
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background-color: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-action-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.header-action-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-ink);
}

.header-action-btn svg {
  width: 20px;
  height: 20px;
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background-color: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-menu-container {
  position: relative;
  margin-left: 8px;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--color-ink);
  transition: background-color var(--transition-fast);
}

.user-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-interactive), #005a9e);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.user-avatar svg {
  width: 100%;
  height: 100%;
  color: white;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-ink);
}

.user-role {
  font-size: 11px;
  color: var(--color-muted);
}

.dropdown-arrow {
  width: 18px;
  height: 18px;
  color: var(--color-muted);
  transition: transform var(--transition-fast);
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  z-index: 200;
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  background-color: transparent;
  color: var(--color-ink);
  font-size: 13px;
  transition: background-color var(--transition-fast);
}

.dropdown-item:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.dropdown-item svg {
  width: 18px;
  height: 18px;
  color: var(--color-muted);
}

.dropdown-item.logout {
  color: var(--color-danger);
}

.dropdown-item.logout svg {
  color: var(--color-danger);
}

.dropdown-divider {
  height: 1px;
  background-color: var(--color-hairline);
  margin: 4px 0;
}
</style>
