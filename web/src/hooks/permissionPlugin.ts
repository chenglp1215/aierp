import type { App, Directive } from 'vue'
import { usePermission } from './usePermission'

export const vPermission: Directive = {
  mounted(el: HTMLElement, binding) {
    const { hasPermission } = usePermission()
    const permissionCode = binding.value as string

    if (permissionCode && !hasPermission(permissionCode)) {
      el.parentNode?.removeChild(el)
    }
  },
  updated(el: HTMLElement, binding) {
    const { hasPermission } = usePermission()
    const permissionCode = binding.value as string

    if (permissionCode && !hasPermission(permissionCode)) {
      el.parentNode?.removeChild(el)
    }
  }
}

export const vHasAnyPermission: Directive = {
  mounted(el: HTMLElement, binding) {
    const { hasAnyPermission } = usePermission()
    const permissionCodes = binding.value as string[]

    if (permissionCodes && !hasAnyPermission(permissionCodes)) {
      el.parentNode?.removeChild(el)
    }
  }
}

export const vHasAllPermissions: Directive = {
  mounted(el: HTMLElement, binding) {
    const { hasAllPermissions } = usePermission()
    const permissionCodes = binding.value as string[]

    if (permissionCodes && !hasAllPermissions(permissionCodes)) {
      el.parentNode?.removeChild(el)
    }
  }
}

export const permissionDirectivePlugin = {
  install(app: App) {
    app.directive('permission', vPermission)
    app.directive('has-any-permission', vHasAnyPermission)
    app.directive('has-all-permissions', vHasAllPermissions)
  }
}

export { usePermission, refreshPermissions, MENU_PERMISSION_MAP, BUTTON_PERMISSION_MAP } from './usePermission'
