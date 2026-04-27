<script setup lang="ts">
import { computed, ref } from 'vue'

export interface AgentDataField {
  display_name?: string
  value?: any
  display_value?: any
  options?: Array<{ value: string; display_value: string }>
}

export interface AgentDataItem {
  [key: string]: AgentDataField | string | any
}

export interface AgentData {
  type?: 'list' | 'form' | 'info'
  data?: AgentDataItem[] | AgentDataItem
  [key: string]: any
}

export interface AgentResponse {
  text?: string
  related_data?: {
    type: 'list' | 'form' | 'info'
    data: AgentDataItem[] | AgentDataItem
  }
  next_step?: string[]
}

const props = defineProps<{
  response: AgentResponse
}>()

const emit = defineEmits<{
  action: [step: string, selectedData?: string]
}>()

const selectedRows = ref<Set<number>>(new Set())

const getDisplayName = (field: AgentDataField | string | any): string => {
  if (!field) return ''
  if (typeof field === 'string') return field
  if (typeof field === 'object' && 'display_name' in field) return String(field.display_name || '')
  if (typeof field === 'object' && 'name' in field) return String((field as any).name || '')
  return String(field)
}

const getValue = (field: AgentDataField | string | any): string => {
  if (!field) return ''
  if (typeof field === 'string') return field
  if (typeof field === 'object') {
    if ('display_value' in field && field.display_value !== undefined) return String(field.display_value)
    if ('value' in field && field.value !== undefined) return String(field.value)
    return JSON.stringify(field)
  }
  return String(field)
}

const listHeaders = computed(() => {
  if (!effectiveListData.value.length) return []
  const firstItem = effectiveListData.value[0]
  if (!firstItem) return []
  return Object.keys(firstItem)
})

const listHeaderDisplayNames = computed(() => {
  if (!effectiveListData.value.length) return []
  const firstItem = effectiveListData.value[0]
  if (!firstItem) return []
  return listHeaders.value.map(key => {
    const field = firstItem[key]
    return getDisplayName(field) || key
  })
})

const listItems = computed(() => {
  if (!effectiveListData.value.length) return []
  return effectiveListData.value.map(item => {
    return listHeaders.value.map(key => {
      const field = item[key]
      return getValue(field)
    })
  })
})

const listRawItems = computed(() => {
  return effectiveListData.value
})

const infoItems = computed(() => {
  const data = resolvedData.value
  if (!data || typeof data !== 'object') return []
  if (data.type !== 'info') return []
  const infoData = data.data
  if (!infoData) return []
  if (Array.isArray(infoData)) {
    return infoData.map(item => ({
      label: getDisplayName(item) || String((item as any).name || ''),
      value: getValue(item)
    }))
  }
  return [{
    label: getDisplayName(infoData) || String((infoData as any).name || ''),
    value: getValue(infoData)
  }]
})

const formItems = computed(() => {
  const data = resolvedData.value
  if (!data || typeof data !== 'object') return []
  if (data.type !== 'form') return []
  const formData = data.data
  if (!formData || !Array.isArray(formData)) return []
  return formData.map((item, idx) => {
    const name = item.name as string || String(idx)
    return {
      name,
      label: getDisplayName(item) || name,
      value: item.options ? '' : getValue(item),
      options: item.options
    }
  })
})

const formValues = ref<Record<string, string>>({})

const isSelected = (index: number) => selectedRows.value.has(index)

const toggleSelect = (index: number) => {
  if (selectedRows.value.has(index)) {
    selectedRows.value.delete(index)
  } else {
    selectedRows.value.add(index)
  }
  selectedRows.value = new Set(selectedRows.value)
}

const getSelectedDataText = (): string => {
  if (selectedRows.value.size === 0) return ''
  const selectedItems = Array.from(selectedRows.value).map(idx => listRawItems.value[idx])
  const headerNames = listHeaderDisplayNames.value
  const headers = listHeaders.value

  return selectedItems.map(item => {
    return headers.map((key, i) => {
      const field = item[key]
      const value = getValue(field)
      return `${headerNames[i]}: ${value}`
    }).join('\n')
  }).join('\n')
}

const getFormDataText = (): string => {
  const data = resolvedData.value
  if (!data || data.type !== 'form' || !Array.isArray(data.data)) return ''

  return data.data.map((item, idx) => {
    const name = item.name as string || String(idx)
    const value = formValues.value[name] ?? getValue(item)
    const label = getDisplayName(item) || name
    return `${label}: ${value}`
  }).join('\n')
}

const handleAction = (step: string) => {
  const isList = resolvedType.value === 'list'
  const hasSelection = selectedRows.value.size > 0

  if (isList && !hasSelection) {
    alert('请先选中要操作的数据')
    return
  }

  const selectedText = getSelectedDataText()
  const formText = getFormDataText()
  const combinedText = formText ? `表单数据：${formText}` : ''
  emit('action', step, combinedText || selectedText || undefined)
}

const isValidResponse = computed(() => {
  return props.response && typeof props.response === 'object'
})

const resolvedData = computed(() => {
  if (!props.response) return null
  if (props.response.related_data) {
    return props.response.related_data
  }
  if (props.response.data) {
    return props.response.data
  }
  return null
})

const resolvedType = computed(() => {
  const data = resolvedData.value
  if (!data || typeof data !== 'object') return null
  return data.type || null
})

const effectiveListData = computed(() => {
  const data = resolvedData.value
  if (!data || typeof data !== 'object') return []
  if (data.type !== 'list') return []
  if (!Array.isArray(data.data)) return []
  return data.data
})
</script>

<template>
  <div v-if="isValidResponse" class="agent-data-display">
    <div v-if="resolvedType === 'list' && effectiveListData.length > 0" class="data-list-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="checkbox-col"></th>
            <th v-for="(name, index) in listHeaderDisplayNames" :key="listHeaders[index]">
              {{ name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in listItems" :key="rowIndex" :class="{ selected: isSelected(rowIndex) }">
            <td class="checkbox-col">
              <input
                type="checkbox"
                :checked="isSelected(rowIndex)"
                @change="toggleSelect(rowIndex)"
              />
            </td>
            <td v-for="(cell, cellIndex) in row" :key="cellIndex">
              {{ cell || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="resolvedType === 'info' && infoItems.length > 0" class="data-info-container">
      <div class="info-item" v-for="(item, idx) in infoItems" :key="idx">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </div>

    <div v-else-if="resolvedType === 'form' && formItems.length > 0" class="data-form-container">
      <div class="form-item" v-for="(item, idx) in formItems" :key="idx">
        <label class="form-label">{{ item.label }}</label>
        <div class="form-control">
          <select v-if="item.options?.length" class="form-select">
            <option v-for="opt in item.options" :key="opt.value" :value="opt.value">
              {{ opt.display_value || opt.value }}
            </option>
          </select>
          <input
            v-else-if="!item.value"
            type="text"
            class="form-input"
            v-model="formValues[item.name]"
            placeholder="请输入"
          />
          <span v-else class="form-value">{{ item.value }}</span>
        </div>
      </div>
    </div>

    <div v-else-if="resolvedData && Object.keys(resolvedData).length > 0" class="data-fallback">
      <div class="fallback-title">数据 (type: {{ resolvedType }})</div>
      <pre class="fallback-content">{{ JSON.stringify(resolvedData, null, 2) }}</pre>
    </div>

    <div v-if="response.next_step?.length" class="agent-next-step">
      <span class="next-step-label">推荐操作：</span>
      <div class="next-step-buttons">
        <button
          v-for="(step, idx) in response.next_step"
          :key="idx"
          class="next-step-btn"
          @click="handleAction(step)"
        >
          {{ step }}
        </button>
      </div>
    </div>
  </div>
  <div v-else class="data-error">
    <span class="error-text">数据格式异常</span>
    <pre class="fallback-content">{{ JSON.stringify(response, null, 2) }}</pre>
  </div>
</template>

<style scoped>
.agent-data-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-list-container {
  overflow-x: auto;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  background-color: var(--bg-secondary);
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.checkbox-col {
  width: 40px;
  text-align: center;
  padding: 10px 8px !important;
}

.checkbox-col input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent-blue);
}

.data-table tbody tr.selected {
  background-color: rgba(0, 120, 212, 0.1);
}

.data-table td {
  padding: 10px 14px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.data-table tbody tr:hover {
  background-color: rgba(0, 120, 212, 0.05);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-info-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.info-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  min-width: 100px;
  font-weight: 500;
  color: var(--text-muted);
}

.info-value {
  flex: 1;
  color: var(--text-primary);
  word-break: break-word;
}

.data-form-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  font-weight: 500;
  color: var(--text-muted);
  font-size: 13px;
}

.form-control {
  width: 100%;
}

.form-select {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.form-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-input::placeholder {
  color: var(--text-muted);
}

.form-value {
  color: var(--text-primary);
  font-size: 13px;
}

.data-fallback {
  padding: 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.fallback-title {
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-size: 12px;
}

.fallback-content {
  margin: 0;
  padding: 8px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.agent-next-step {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.next-step-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}

.next-step-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.next-step-btn {
  padding: 8px 16px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.next-step-btn:hover {
  background-color: var(--accent-blue-hover);
  transform: translateY(-1px);
}

.next-step-btn:active {
  transform: translateY(0);
}

.data-error {
  padding: 12px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid var(--accent-red);
}

.error-text {
  color: var(--accent-red);
  font-size: 13px;
}
</style>
