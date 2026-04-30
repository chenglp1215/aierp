import { ref, watch } from 'vue'

export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'app-theme'

const getSavedTheme = (): boolean => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light') {
    return false
  }
  if (saved === 'dark') {
    return true
  }
  return true
}

const isDark = ref(getSavedTheme())

const applyTheme = (dark: boolean) => {
  if (document.documentElement) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
}

const setTheme = (theme: Theme) => {
  isDark.value = theme === 'dark'
}

watch(isDark, (dark) => {
  localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light')
  applyTheme(dark)
})

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => applyTheme(isDark.value))
} else {
  applyTheme(isDark.value)
}

export function useTheme() {
  return {
    isDark,
    toggleTheme,
    setTheme
  }
}
