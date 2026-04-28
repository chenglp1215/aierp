<script setup lang="ts">
import { ref, computed } from 'vue'

export interface ToolCallData {
  tool: string
  toolName?: string
  args: Record<string, any>
  result?: {
    success: boolean
    content: string
    error?: string
  }
}

const props = withDefaults(defineProps<{
  toolCall: ToolCallData
  index: number
}>(), {
})

const isExpanded = ref(false)

const displayName = computed(() => {
  return props.toolCall.toolName || props.toolCall.tool || '未知工具'
})

const statusIcon = computed(() => {
  if (!props.toolCall.result) return '⏳'
  return props.toolCall.result.success ? '✓' : '✗'
})

const statusClass = computed(() => {
  if (!props.toolCall.result) return 'pending'
  return props.toolCall.result.success ? 'success' : 'error'
})

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const formatArgs = computed(() => {
  try {
    return JSON.stringify(props.toolCall.args, null, 2)
  } catch {
    return String(props.toolCall.args)
  }
})

const formatResult = computed(() => {
  if (!props.toolCall.result) return '执行中...'
  if (props.toolCall.result.success) {
    try {
      const parsed = JSON.parse(props.toolCall.result.content)
      return JSON.stringify(parsed, null, 2)
    } catch {
      return props.toolCall.result.content
    }
  }
  return props.toolCall.result.error || '执行失败'
})
</script>

<template>
  <div :class="['tool-call-item', statusClass]">
    <div class="tool-header" @click="toggleExpanded">
      <div class="tool-info">
        <span class="tool-index">#{{ index + 1 }}</span>
        <span class="tool-icon">
          <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
            <path d="M22 9V7h-2V5c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-2h2v-2h-2v-2h2v-2h-2V9h2zm-4 10H4V5h14v14zM6 13h5v4H6zm6-6h4v3h-4zm0 4h4v6h-4zm6-4h5v2h-5zm0 4h5v2h-5z"/>
          </svg>
        </span>
        <span class="tool-name">{{ displayName }}</span>
      </div>
      <div class="tool-status">
        <span :class="['status-badge', statusClass]">{{ statusIcon }}</span>
        <svg
          :class="['expand-icon', { expanded: isExpanded }]"
          viewBox="0 0 24 24"
          fill="currentColor"
          width="16"
          height="16"
        >
          <path d="M7 10l5 5 5-5z"/>
        </svg>
      </div>
    </div>

    <div v-if="isExpanded" class="tool-details">
      <div class="detail-section">
        <div class="section-label">
          <svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
            <path d="M3 3h18v2H3zm0 16h18v2H3zm0-8h18v2H3z"/>
          </svg>
          调用参数
        </div>
        <pre class="code-block">{{ formatArgs }}</pre>
      </div>

      <div class="detail-section">
        <div class="section-label">
          <svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          返回结果
        </div>
        <pre :class="['code-block', statusClass]">{{ formatResult }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-call-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  margin-top: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.03);
  transition: all var(--transition-fast);
}

.tool-call-item:hover {
  border-color: var(--accent-blue);
}

.tool-call-item.success {
  border-left: 3px solid var(--accent-green);
}

.tool-call-item.error {
  border-left: 3px solid var(--accent-red);
}

.tool-call-item.pending {
  border-left: 3px solid var(--accent-yellow, #f59e0b);
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  background: rgba(0, 120, 212, 0.05);
}

.tool-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-index {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  min-width: 20px;
}

.tool-icon {
  display: flex;
  align-items: center;
  color: var(--accent-blue);
}

.tool-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.success {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent-yellow, #f59e0b);
}

.expand-icon {
  color: var(--text-muted);
  transition: transform var(--transition-fast);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.tool-details {
  border-top: 1px solid var(--border-color);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.code-block {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.code-block.success {
  border-left: 3px solid var(--accent-green);
}

.code-block.error {
  border-left: 3px solid var(--accent-red);
}
</style>
