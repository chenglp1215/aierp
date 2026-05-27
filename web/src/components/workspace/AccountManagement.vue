<script setup lang="ts">
defineOptions({ name: 'AccountManagement' })

import { ref } from 'vue'
import UserManagement from './UserManagement.vue'
import RoleManagement from './RoleManagement.vue'
import PermissionManagement from './PermissionManagement.vue'

type TabType = 'user' | 'role' | 'permission'

const activeTab = ref<TabType>('user')

const tabs: { key: TabType; label: string }[] = [
  { key: 'user', label: '用户管理' },
  { key: 'role', label: '角色管理' },
  { key: 'permission', label: '权限管理' }
]

const switchTab = (tab: TabType) => {
  activeTab.value = tab
}
</script>

<template>
  <div class="account-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">账号管理</h2>
    </div>

    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <UserManagement v-if="activeTab === 'user'" />
      <RoleManagement v-if="activeTab === 'role'" />
      <PermissionManagement v-if="activeTab === 'permission'" />
    </div>
  </div>
</template>

<style scoped>
.account-workspace {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
}

.tabs-bar {
  display: flex;
  gap: 4px;
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 8px;
  box-shadow: var(--shadow-card);
}

.tab-btn {
  padding: 10px 24px;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-ink);
  background-color: rgba(0, 0, 0, 0.03);
}

.tab-btn.active {
  background-color: var(--color-interactive);
  color: white;
}

.tab-content {
  min-height: 400px;
}
</style>
