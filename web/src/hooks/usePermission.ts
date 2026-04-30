import { ref, computed } from 'vue'
import { permissionApi } from '../services/api'

interface Permission {
  id: string
  code: string
  name: string
  type: 'menu' | 'button' | 'api'
  path?: string
  parent_id?: string | null
  children?: Permission[]
}

interface UserPermissions {
  permissions: string[]
  role_codes: string[]
}

const permissions = ref<Permission[]>([])
const userPermissions = ref<UserPermissions>({ permissions: [], role_codes: [] })
const isLoaded = ref(false)

const flattenPermissions = (perms: Permission[]): Permission[] => {
  const result: Permission[] = []
  for (const perm of perms) {
    result.push(perm)
    if (perm.children && perm.children.length > 0) {
      result.push(...flattenPermissions(perm.children))
    }
  }
  return result
}

const loadPermissions = async (forceRefresh = false) => {
  if (isLoaded.value && !forceRefresh) return

  try {
    const tree = await permissionApi.getTree()
    permissions.value = flattenPermissions(tree as Permission[])

    const userData = localStorage.getItem('user')
    if (userData) {
      const user = JSON.parse(userData)

      let permCodes: string[] = []

      if (user.permissions && Array.isArray(user.permissions)) {
        permCodes = user.permissions
      } else if (user.roles && Array.isArray(user.roles)) {
        for (const role of user.roles) {
          if (role.permissions && Array.isArray(role.permissions)) {
            for (const perm of role.permissions) {
              if (perm.code) {
                permCodes.push(perm.code)
              }
            }
          }
        }
        permCodes = [...new Set(permCodes)]
      }

      const roleCodes = (user.roles || []).map((r: any) => r.code || r).filter(Boolean)

      userPermissions.value = {
        permissions: permCodes,
        role_codes: roleCodes
      }
    }

    isLoaded.value = true
  } catch (error) {
    console.error('加载权限失败:', error)
  }
}

export const refreshPermissions = async () => {
  isLoaded.value = false
  return loadPermissions(true)
}

const hasPermission = (code: string): boolean => {
  if (userPermissions.value.role_codes.includes('super_admin')) {
    return true
  }
  return userPermissions.value.permissions.includes(code)
}

const hasAnyPermission = (codes: string[]): boolean => {
  if (userPermissions.value.role_codes.includes('super_admin')) {
    return true
  }
  return codes.some(code => userPermissions.value.permissions.includes(code))
}

const hasAllPermissions = (codes: string[]): boolean => {
  if (userPermissions.value.role_codes.includes('super_admin')) {
    return true
  }
  return codes.every(code => userPermissions.value.permissions.includes(code))
}

const getMenuPermissions = computed(() => {
  return permissions.value.filter(p => p.type === 'menu')
})

const getButtonPermissions = computed(() => {
  return permissions.value.filter(p => p.type === 'button')
})

const isMenuVisible = (menuCode: string): boolean => {
  return hasPermission(menuCode)
}

const isButtonVisible = (buttonCode: string): boolean => {
  return hasPermission(buttonCode)
}

const clearPermissions = () => {
  permissions.value = []
  userPermissions.value = { permissions: [], role_codes: [] }
  isLoaded.value = false
}

const updateUserPermissions = (perms: string[], roleCodes: string[]) => {
  userPermissions.value = { permissions: perms, role_codes: roleCodes }
}

export const usePermission = () => {
  return {
    permissions,
    userPermissions,
    isLoaded,
    loadPermissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    getMenuPermissions,
    getButtonPermissions,
    isMenuVisible,
    isButtonVisible,
    clearPermissions,
    updateUserPermissions
  }
}

export const MENU_PERMISSION_MAP: Record<string, string> = {
  'dashboard': 'dashboard.view',
  'chat': 'chat.view',
  'sales': 'order.menu',
  'sales-order': 'order.view',
  'sales-contract': 'order.view',
  'sales-return': 'order.view',
  'inventory': 'inventory.menu',
  'inventory-stock': 'stock.view',
  'inventory-check': 'inventory.check.view',
  'warehouse': 'warehouse.menu',
  'warehouse-list': 'warehouse.view',
  'stock': 'stock.menu',
  'stock-list': 'stock.view',
  'finance': 'finance.menu',
  'finance-invoice': 'finance.invoice.view',
  'finance-payment': 'finance.payment.view',
  'finance-report': 'finance.report.view',
  'crm': 'customer.menu',
  'product': 'product.menu',
  'system': 'system.menu',
  'system-account': 'user.menu',
  'system-intelligent': 'intelligent.settings.view',
  'system-user': 'user.menu',
  'system-role': 'role.menu',
  'system-permission': 'permission.menu'
}

export const BUTTON_PERMISSION_MAP: Record<string, string> = {
  'create': 'create',
  'edit': 'edit',
  'delete': 'delete',
  'view': 'view',
  'export': 'export',
  'import': 'import',
  'reset-password': 'reset-password',
  'enable': 'enable',
  'disable': 'disable'
}
