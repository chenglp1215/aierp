import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

const toasts = ref<ToastItem[]>([])
let toastId = 0

export function useToast() {
  const addToast = (message: string, type: ToastItem['type'] = 'info') => {
    const id = ++toastId
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      removeToast(id)
    }, 3000)
    return id
  }

  const removeToast = (id: number) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const success = (message: string) => addToast(message, 'success')
  const error = (message: string) => addToast(message, 'error')
  const warning = (message: string) => addToast(message, 'warning')
  const info = (message: string) => addToast(message, 'info')

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info
  }
}