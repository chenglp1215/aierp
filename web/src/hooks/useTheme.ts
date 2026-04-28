import { ref, watch, onMounted } from 'vue'

export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'app-theme'

const isDark = ref(true)

const initTheme = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') {
    isDark.value = saved === 'dark'
  }
}

const applyTheme = (dark: boolean) => {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
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
}, { immediate: true })

onMounted(() => {
  initTheme()
  applyTheme(isDark.value)
})

export function useTheme() {
  return {
    isDark,
    toggleTheme,
    setTheme
  }
}
