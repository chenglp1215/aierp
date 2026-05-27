<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import type { Ref } from 'vue'
import { usePermission, refreshPermissions, MENU_PERMISSION_MAP } from '../hooks'

interface MenuItem {
  id: string
  label: string
  icon: string
  badge?: number
  children?: MenuItem[]
}

const emit = defineEmits<{
  navigate: [id: string]
  'warehouse-navigate': [id: string, extraData?: Record<string, any>]
}>()

// 注入侧边栏收起状态
const isCollapsed = inject<Ref<boolean>>('sidebarCollapsed', ref(false))
const toggleSidebar = inject<() => void>('toggleSidebar', () => {})

const { loadPermissions, hasPermission } = usePermission()
const activeMenu = ref('dashboard')
const expandedMenus = ref<string[]>(['sales'])

const allMenuItems: MenuItem[] = [
  { id: 'dashboard', label: '工作台', icon: 'dashboard' },
  { id: 'chat', label: '智能助手', icon: 'chat' },
  {
    id: 'sales',
    label: '销售管理',
    icon: 'sales',
    children: [
      { id: 'sales-order', label: '销售订单', icon: 'order' },
      { id: 'sales-contract', label: '销售合同', icon: 'contract' },
      { id: 'sales-return', label: '退货管理', icon: 'return' }
    ]
  },
  {
    id: 'purchase',
    label: '采购管理',
    icon: 'purchase',
    children: [
      { id: 'purchase-order', label: '采购单', icon: 'purchase-order' },
      { id: 'supplier', label: '供应商', icon: 'supplier' }
    ]
  },
  {
    id: 'inventory',
    label: '库存管理',
    icon: 'inventory',
    children: [
      { id: 'warehouse-list', label: '仓库管理', icon: 'warehouse' },
      { id: 'inventory-stock', label: '库存管理', icon: 'stock' },
      { id: 'pending-outbound', label: '出库管理', icon: 'outbound' }
    ]
  },
  {
    id: 'finance',
    label: '财务管理',
    icon: 'finance',
    children: [
      { id: 'finance-invoice', label: '发票管理', icon: 'invoice' },
      { id: 'finance-payment', label: '付款管理', icon: 'payment' },
      { id: 'finance-report', label: '财务报表', icon: 'report' }
    ]
  },
  { id: 'crm', label: '客户管理', icon: 'crm' },
  {
    id: 'product',
    label: '商品管理',
    icon: 'product',
    children: [
      { id: 'category', label: '分类管理', icon: 'category' },
      { id: 'brand', label: '品牌管理', icon: 'brand' },
      { id: 'product-list', label: '产品管理', icon: 'product-list' }
    ]
  },
  {
    id: 'system',
    label: '系统设置',
    icon: 'settings',
    children: [
      { id: 'system-account', label: '账号管理', icon: 'account' },
      { id: 'system-intelligent', label: '智能设置', icon: 'intelligent' }
    ]
  }
]

const visibleMenuItems = computed(() => {
  return filterVisibleMenus(allMenuItems)
})

const filterVisibleMenus = (items: MenuItem[]): MenuItem[] => {
  const result: MenuItem[] = []
  for (const item of items) {
    const permCode = MENU_PERMISSION_MAP[item.id]
    const hasDirectPermission = !permCode || hasPermission(permCode)
    const visibleChildren = item.children ? filterVisibleMenus(item.children) : undefined
    const hasVisibleChildren = visibleChildren && visibleChildren.length > 0

    if (hasDirectPermission || hasVisibleChildren) {
      result.push({
        ...item,
        children: visibleChildren && visibleChildren.length > 0 ? visibleChildren : item.children
      })
    }
  }
  return result
}

const toggleExpand = (id: string) => {
  const idx = expandedMenus.value.indexOf(id)
  if (idx > -1) {
    expandedMenus.value.splice(idx, 1)
  } else {
    expandedMenus.value.push(id)
  }
}

const handleMenuClick = (item: MenuItem) => {
  if (item.children) {
    // 收起状态下点击有子菜单的项，先展开侧边栏
    if (isCollapsed.value) {
      toggleSidebar()
    }
    toggleExpand(item.id)
  } else {
    activeMenu.value = item.id
    emit('navigate', item.id)
  }
}

const isExpanded = (id: string) => expandedMenus.value.includes(id)
const isActive = (id: string) => activeMenu.value === id

onMounted(async () => {
  await loadPermissions()
  window.addEventListener('user-updated', handleUserUpdated)
  window.addEventListener('storage', handleStorageChange)
})

onUnmounted(() => {
  window.removeEventListener('user-updated', handleUserUpdated)
  window.removeEventListener('storage', handleStorageChange)
})

const handleUserUpdated = async () => {
  await refreshPermissions()
}

const handleStorageChange = async (event: StorageEvent) => {
  if (event.key === 'user') {
    await refreshPermissions()
  }
}
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="brand">
        <svg class="brand-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        <span class="brand-text" v-show="!isCollapsed">ERP</span>
      </div>
      <div class="user-role" v-show="!isCollapsed">Administrator</div>
      <button class="collapse-btn" @click="toggleSidebar" :title="isCollapsed ? '展开菜单' : '收起菜单'">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path v-if="!isCollapsed" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
          <path v-else d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <template v-for="item in visibleMenuItems" :key="item.id">
        <div
          class="nav-item"
          :class="{ active: isActive(item.id), expanded: isExpanded(item.id) }"
          @click="handleMenuClick(item)"
          :title="isCollapsed ? item.label : ''"
        >
          <span class="nav-icon">
            <svg v-if="item.icon === 'dashboard'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
            </svg>
            <svg v-else-if="item.icon === 'chat'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            </svg>
            <svg v-else-if="item.icon === 'procurement'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/>
            </svg>
            <svg v-else-if="item.icon === 'sales'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 4H5c-1.11 0-2 .9-2 2v12c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.89-2-2-2zm0 14H5V8h14v10z"/>
            </svg>
            <svg v-else-if="item.icon === 'purchase'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
            <svg v-else-if="item.icon === 'inventory'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 2H4c-1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-1-2-2-2zm-1 14H5V9h14v7zm1-5H4V4h16v3z"/>
            </svg>
            <svg v-else-if="item.icon === 'finance'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>
            </svg>

            <svg v-else-if="item.icon === 'crm'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
            <svg v-else-if="item.icon === 'product'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/>
            </svg>
            <svg v-else-if="item.icon === 'settings'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
            </svg>
          </span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.children" class="nav-arrow" :class="{ rotated: isExpanded(item.id) }">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 10l5 5 5-5z"/>
            </svg>
          </span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </div>

        <div v-if="item.children && isExpanded(item.id)" class="submenu">
          <div
            v-for="child in item.children"
            :key="child.id"
            class="nav-item submenu-item"
            :class="{ active: isActive(child.id) }"
            @click="handleMenuClick(child)"
            :title="isCollapsed ? child.label : ''"
          >
            <span class="nav-icon small">
              <svg v-if="child.icon === 'order'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
              </svg>
              <svg v-else-if="child.icon === 'supplier'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
              </svg>
              <svg v-else-if="child.icon === 'contract'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
              </svg>
              <svg v-else-if="child.icon === 'return'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 7v4H5.83l3.58-3.59L8 6l-6 6 6 6 1.41-1.41L5.83 13H21V7z"/>
              </svg>
              <svg v-else-if="child.icon === 'purchase-order'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.11 0-2 .89-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.11-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
              </svg>
              <svg v-else-if="child.icon === 'stock'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-1-2-2-2zm-1 14H5V9h14v7zm1-5H4V4h16v3z"/>
              </svg>
              <svg v-else-if="child.icon === 'warehouse'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3zm0 2.84L18 12v8h-2v-6H8v6H6v-8l6-6.16z"/>
              </svg>
              <svg v-else-if="child.icon === 'check'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
              <svg v-else-if="child.icon === 'transfer'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
              </svg>
              <svg v-else-if="child.icon === 'invoice'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 17H6v-2h12v2zm0-4H6v-2h12v2zm0-4H6V7h12v2zM3 22l4-4 4 4 8-8V2H11v6L3 22z"/>
              </svg>
              <svg v-else-if="child.icon === 'payment'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>
              </svg>
              <svg v-else-if="child.icon === 'report'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
              </svg>
              <svg v-else-if="child.icon === 'account'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
              <svg v-else-if="child.icon === 'intelligent'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0C18.32 15.65 19 14.08 19 12.1h2c0 1.98-.88 4.55-2.64 6.29-3.51 3.48-9.21 3.48-12.72 0-3.5-3.47-3.53-9.11-.02-12.58s9.14-3.47 12.65 0L21 3v7.12zM12.5 8v4.25l3.5 2.08-.72 1.21L11 13V8h1.5z"/>
              </svg>
              <svg v-else-if="child.icon === 'category'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l-5.5 9h11L12 2zm0 3.84L13.93 9h-3.87L12 5.84zM17.5 13c-2.49 0-4.5 2.01-4.5 4.5s2.01 4.5 4.5 4.5 4.5-2.01 4.5-4.5-2.01-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5zM3 21.5h8v-8H3v8zm2-6h4v4H5v-4z"/>
              </svg>
              <svg v-else-if="child.icon === 'brand'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58s1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41s-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/>
              </svg>
              <svg v-else-if="child.icon === 'outbound'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>
              </svg>
              <svg v-else-if="child.icon === 'product-list'" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 6h-2c0-2.21-1.79-4-4-4S8 3.79 8 6H6c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6-2c1.1 0 2 .9 2 2h-4c0-1.1.9-2 2-2zm6 16H6V8h2v2c0 .55.45 1 1 1s1-.45 1-1V8h4v2c0 .55.45 1 1 1s1-.45 1-1V8h2v12z"/>
              </svg>
            </span>
            <span class="nav-label">{{ child.label }}</span>
          </div>
        </div>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <span class="search-text">Search</span>
        <span class="search-shortcut">Ctrl+K</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background-color: var(--color-sidebar-bg);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: width var(--transition-normal);
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  position: relative;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  width: 28px;
  height: 28px;
  color: var(--color-interactive);
}

.brand-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-inverse);
}

.user-role {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-muted);
  padding-left: 38px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  position: relative;
  color: var(--color-muted);
}

.nav-item:hover {
  background-color: var(--color-sidebar-hover);
}

.nav-item.active {
  background-color: var(--color-sidebar-active);
  color: var(--color-text-inverse);
}

.nav-item.active .nav-icon {
  color: var(--color-interactive);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon.small {
  width: 16px;
  height: 16px;
}

.nav-icon svg {
  width: 100%;
  height: 100%;
}

.nav-label {
  flex: 1;
  font-size: 14px;
}

.nav-arrow {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition-fast);
}

.nav-arrow svg {
  width: 18px;
  height: 18px;
}

.nav-arrow.rotated {
  transform: rotate(180deg);
}

.nav-badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background-color: var(--color-danger);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submenu {
  padding-left: 20px;
  overflow: hidden;
}

.submenu-item {
  padding: 10px 16px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background-color: rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.search-box:hover {
  background-color: rgba(0, 0, 0, 0.06);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: var(--color-muted);
}

.search-text {
  flex: 1;
  font-size: 13px;
  color: var(--color-muted);
}

.search-shortcut {
  font-size: 11px;
  color: var(--color-muted);
  padding: 2px 6px;
  background-color: rgba(0, 0, 0, 0.06);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform var(--transition-normal);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .collapse-btn {
    display: none;
  }
}

.collapse-btn {
  position: absolute;
  top: 20px;
  right: -12px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--color-sidebar-bg);
  border: 1px solid rgba(0, 0, 0, 0.1);
  color: var(--color-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  z-index: 10;
}

.collapse-btn:hover {
  background-color: var(--color-interactive);
  color: var(--color-text-inverse);
  border-color: var(--color-interactive);
}

.collapse-btn svg {
  width: 16px;
  height: 16px;
}

.sidebar.collapsed .nav-label,
.sidebar.collapsed .nav-arrow,
.sidebar.collapsed .nav-badge,
.sidebar.collapsed .user-role,
.sidebar.collapsed .search-text,
.sidebar.collapsed .search-shortcut {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.sidebar.collapsed .submenu {
  display: none;
}

.sidebar.collapsed .sidebar-footer {
  padding: 12px;
}

.sidebar.collapsed .search-box {
  justify-content: center;
  padding: 10px;
}
</style>