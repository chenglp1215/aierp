/**
 * 主题 Hook — 固定亮色模式
 * DESIGN.md 白色画布设计系统，暂不支持暗色模式
 */

export function useTheme() {
  // 固定亮色模式
  if (typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme') !== 'light') {
    document.documentElement.setAttribute('data-theme', 'light')
  }

  return {
    isDark: false as const,
    theme: 'light' as const,
  }
}
