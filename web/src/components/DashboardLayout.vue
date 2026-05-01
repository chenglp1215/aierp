<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SidebarNav from './SidebarNav.vue'
import DashboardHeader from './DashboardHeader.vue'
import DashboardFooter from './DashboardFooter.vue'
import ActionButtons from './ActionButtons.vue'
import Toast from './common/Toast.vue'
import DashboardWorkspace from './workspace/DashboardWorkspace.vue'
import ChatWorkspace from './workspace/ChatWorkspace.vue'
import SalesWorkspace from './workspace/SalesWorkspace.vue'
import SalesOrderList from './workspace/SalesOrderList.vue'
import ProcurementOrderList from './workspace/ProcurementOrderList.vue'
import ReceivableList from './workspace/ReceivableList.vue'
import InventoryWorkspace from './workspace/InventoryWorkspace.vue'
import FinanceWorkspace from './workspace/FinanceWorkspace.vue'
import CrmWorkspace from './workspace/CrmWorkspace.vue'
import ProductWorkspace from './workspace/ProductWorkspace.vue'
import CategoryWorkspace from './workspace/CategoryWorkspace.vue'
import BrandWorkspace from './workspace/BrandWorkspace.vue'
import AccountManagement from './workspace/AccountManagement.vue'
import IntelligentSettings from './workspace/IntelligentSettings.vue'
import WarehouseWorkspace from './workspace/WarehouseWorkspace.vue'
import CustomerDiscountWorkspace from './workspace/CustomerDiscountWorkspace.vue'
import { authApi } from '../services/api'
import { usePermission, MENU_PERMISSION_MAP } from '../hooks'

const router = useRouter()
const { loadPermissions, hasPermission } = usePermission()
const toastRef = ref<InstanceType<typeof Toast> | null>(null)

interface Tab {
  id: string
  label: string
  closable: boolean
}

const isMobileMenuOpen = ref(false)
const activeTabId = ref('dashboard')
const inventoryDrillDownData = ref<{ warehouseId?: string; warehouseName?: string } | null>(null)
const customerDiscountDrillDownData = ref<{ customerId?: string; customerName?: string } | null>(null)
const openTabs = ref<Tab[]>([
  { id: 'dashboard', label: '工作台', closable: false },
  { id: 'chat', label: '智能助手', closable: false }
])

const defaultTabs: Tab[] = [
  { id: 'dashboard', label: '工作台', closable: false },
  { id: 'chat', label: '智能助手', closable: false }
]

const handleNavigate = (id: string, extraData?: Record<string, any>) => {
  const permCode = MENU_PERMISSION_MAP[id]
  if (permCode && !hasPermission(permCode)) {
    return
  }

  if (extraData?.warehouseId) {
    inventoryDrillDownData.value = {
      warehouseId: extraData.warehouseId,
      warehouseName: extraData.warehouseName || ''
    }
    const label = extraData.warehouseName ? `${extraData.warehouseName} - 库存` : '库存管理'
    const tabExists = openTabs.value.find(t => t.id === 'inventory-drilldown')
    if (!tabExists) {
      openTabs.value.push({ id: 'inventory-drilldown', label, closable: true })
    }
    activeTabId.value = 'inventory-drilldown'
    return
  }

  if (extraData?.customerId) {
    customerDiscountDrillDownData.value = {
      customerId: extraData.customerId,
      customerName: extraData.customerName || ''
    }
    const label = extraData.customerName ? `${extraData.customerName} - 折扣设置` : '折扣设置'
    const tabExists = openTabs.value.find(t => t.id === 'customer-discount-drilldown')
    if (!tabExists) {
      openTabs.value.push({ id: 'customer-discount-drilldown', label, closable: true })
    }
    activeTabId.value = 'customer-discount-drilldown'
    return
  }

  const tabExists = openTabs.value.find(t => t.id === id)
  if (!tabExists) {
    const labelMap: Record<string, string> = {
      'dashboard': '工作台',
      'chat': '智能助手',
      'sales-order': '销售订单',
      'procurement-order': '采购单',
      'finance-receivable': '应收款',
      'sales': '销售管理',
      'sales-contract': '销售合同',
      'sales-return': '退货管理',
      'warehouse-list': '仓库管理',
      'inventory-stock': '库存管理',
      'inventory-check': '库存盘点',
      'finance-invoice': '发票管理',
      'finance-payment': '付款管理',
      'finance-report': '财务报表',
      'crm': '客户管理',
      'product': '商品管理',
      'category': '分类管理',
      'brand': '品牌管理',
      'product-list': '产品管理',
      'system-account': '账号管理',
      'system-intelligent': '智能设置'
    }
    const label = labelMap[id] || id
    openTabs.value.push({ id, label, closable: true })
  }
  activeTabId.value = id
}

const handleTabClick = (tabId: string) => {
  activeTabId.value = tabId
}

const handleTabClose = (tabId: string) => {
  const idx = openTabs.value.findIndex(t => t.id === tabId)
  if (idx > -1) {
    openTabs.value.splice(idx, 1)
    if (activeTabId.value === tabId && openTabs.value.length > 0) {
      activeTabId.value = openTabs.value[Math.max(0, idx - 1)].id
    }
  }
}

const handleAction = (id: string) => {
  console.log('Action:', id)
}

const handleLogout = () => {
  const keysToRemove = ['token', 'user', 'token_expires_at', 'remembered_username', 'remembered_password']
  keysToRemove.forEach(key => localStorage.removeItem(key))
  window.location.replace(window.location.origin + '/login')
}

const handleInventoryBack = () => {
  const idx = openTabs.value.findIndex(t => t.id === 'inventory-drilldown')
  if (idx > -1) {
    openTabs.value.splice(idx, 1)
  }
  inventoryDrillDownData.value = null
  activeTabId.value = 'warehouse-list'
}

const handleCustomerDiscountBack = () => {
  const idx = openTabs.value.findIndex(t => t.id === 'customer-discount-drilldown')
  if (idx > -1) {
    openTabs.value.splice(idx, 1)
  }
  customerDiscountDrillDownData.value = null
  activeTabId.value = 'crm'
}

const handleBack = () => {
  if (activeTabId.value === 'customer-discount-drilldown') {
    handleCustomerDiscountBack()
  } else if (activeTabId.value === 'inventory-drilldown') {
    handleInventoryBack()
  }
}

const handleSettings = () => {
  console.log('Settings')
}

const currentWorkspace = computed(() => {
  const id = activeTabId.value
  if (id === 'dashboard') return DashboardWorkspace
  if (id === 'chat') return ChatWorkspace
  if (id === 'sales-order') return SalesOrderList
  if (id === 'procurement-order') return ProcurementOrderList
  if (id === 'finance-receivable') return ReceivableList
  if (id.startsWith('sales')) return SalesWorkspace
  if (id === 'warehouse-list') return WarehouseWorkspace
  if (id === 'inventory-stock') return InventoryWorkspace
  if (id === 'inventory-drilldown') return InventoryWorkspace
  if (id.startsWith('inventory')) return InventoryWorkspace
  if (id.startsWith('finance')) return FinanceWorkspace
  if (id === 'crm') return CrmWorkspace
  if (id === 'category') return CategoryWorkspace
  if (id === 'brand') return BrandWorkspace
  if (id === 'product-list') return ProductWorkspace
  if (id === 'product') return ProductWorkspace
  if (id === 'system-account') return AccountManagement
  if (id === 'system-intelligent') return IntelligentSettings
  if (id === 'customer-discount-drilldown') return CustomerDiscountWorkspace
  return DashboardWorkspace
})

const currentBreadcrumb = computed(() => {
  return openTabs.value.find(t => t.id === activeTabId.value)?.label || '首页'
})

const keepAliveList = computed(() => {
  const names = ['DashboardWorkspace', 'ChatWorkspace', 'SalesWorkspace', 'SalesOrderList', 'ProcurementOrderList', 'ReceivableList', 'InventoryWorkspace', 'FinanceWorkspace', 'CrmWorkspace', 'ProductWorkspace', 'CategoryWorkspace', 'BrandWorkspace', 'AccountManagement', 'IntelligentSettings', 'WarehouseWorkspace', 'CustomerDiscountWorkspace']
  return names
})

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const initDefaultTabs = () => {
  const visibleDefaults = defaultTabs.filter(tab => {
    const permCode = MENU_PERMISSION_MAP[tab.id]
    return !permCode || hasPermission(permCode)
  })
  openTabs.value = visibleDefaults
  if (visibleDefaults.length > 0) {
    activeTabId.value = visibleDefaults[0].id
  }
}

const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
  if (toastRef.value) {
    (toastRef.value as any)[type](message)
  }
}

window.showToast = showToast

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }

  try {
    await loadPermissions()
    initDefaultTabs()
    const userInfo = await authApi.getMe()
    if (userInfo) {
      localStorage.setItem('user', JSON.stringify(userInfo))
      window.dispatchEvent(new Event('user-updated'))
    }
  } catch (error) {
    const keysToRemove = ['token', 'user', 'token_expires_at']
    keysToRemove.forEach(key => localStorage.removeItem(key))
    router.push('/login')
  }

  // 监听折扣导航事件
  window.addEventListener('navigate-to-discount', (event: any) => {
    const { customerId, customerName } = event.detail
    handleNavigate('customer-discount-drilldown', { customerId, customerName })
  })
})
</script>

<template>
  <div class="app-layout">
    <SidebarNav
      :class="{ open: isMobileMenuOpen }"
      @navigate="handleNavigate"
      @warehouse-navigate="handleNavigate"
    />

    <div
      v-if="isMobileMenuOpen"
      class="mobile-overlay"
      @click="toggleMobileMenu"
    ></div>

    <main class="main-content">
      <div class="fixed-header">
        <DashboardHeader @logout="handleLogout" @settings="handleSettings">
          <template #breadcrumb>
            <nav class="breadcrumb">
              <span class="breadcrumb-item">{{ currentBreadcrumb }}</span>
            </nav>
          </template>
        </DashboardHeader>

        <div class="tabs-bar">
          <div class="tabs-list">
            <button
              v-for="tab in openTabs"
              :key="tab.id"
              class="tab-item"
              :class="{ active: activeTabId === tab.id }"
              @click="handleTabClick(tab.id)"
            >
              <span class="tab-label">{{ tab.label }}</span>
              <button
                v-if="tab.closable"
                class="tab-close"
                @click.stop="handleTabClose(tab.id)"
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </button>
          </div>
          <div class="tabs-actions">
            <ActionButtons @action="handleAction" />
          </div>
        </div>
      </div>

      <div class="content-area">
        <KeepAlive :include="keepAliveList">
          <component 
            :is="currentWorkspace" 
            :key="activeTabId" 
            v-bind="activeTabId === 'inventory-drilldown' ? inventoryDrillDownData : activeTabId === 'customer-discount-drilldown' ? customerDiscountDrillDownData : {}" 
            @back="handleBack" 
            @navigate="handleNavigate" 
          />
        </KeepAlive>
      </div>

      <DashboardFooter />
    </main>
    <Toast ref="toastRef" />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  background-color: var(--bg-primary);
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.fixed-header {
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 50;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-item {
  font-size: 14px;
  color: var(--text-primary);
}

.tabs-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  height: 44px;
}

.tabs-list {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  flex: 1;
}

.tabs-list::-webkit-scrollbar {
  display: none;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.tab-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
  background-color: rgba(0, 120, 212, 0.1);
}

.tab-close {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all var(--transition-fast);
}

.tab-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.tab-close svg {
  width: 12px;
  height: 12px;
}

.tabs-actions {
  padding-left: 16px;
}

.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 90;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }

  .tabs-bar {
    flex-direction: column;
    height: auto;
    padding: 12px 16px;
    gap: 12px;
  }

  .tabs-list {
    width: 100%;
  }

  .tabs-actions {
    width: 100%;
    padding-left: 0;
  }

  .content-area {
    padding: 20px;
  }

  .mobile-overlay {
    display: block;
  }
}
</style>
