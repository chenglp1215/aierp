<script setup lang="ts">
export interface TableColumn {
  key: string
  label: string
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface TableAction {
  id: string
  label: string
  type?: 'primary' | 'danger' | 'default'
}

defineProps<{
  columns: TableColumn[]
  data: Record<string, any>[]
  actions?: TableAction[]
}>()

const emit = defineEmits<{
  action: [id: string, row: Record<string, any>]
  rowClick: [row: Record<string, any>]
}>()

const handleAction = (actionId: string, row: Record<string, any>) => {
  emit('action', actionId, row)
}
</script>

<template>
  <div class="data-table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width, textAlign: col.align || 'left' }"
          >
            {{ col.label }}
          </th>
          <th v-if="actions" class="actions-col">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in data" :key="idx" @click="$emit('rowClick', row)">
          <td
            v-for="col in columns"
            :key="col.key"
            :style="{ textAlign: col.align || 'left' }"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
          <td v-if="actions" class="actions-cell">
            <button
              v-for="action in actions"
              :key="action.id"
              class="action-btn"
              :class="action.type || 'default'"
              @click.stop="handleAction(action.id, row)"
            >
              {{ action.label }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.data-table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  padding: 12px 16px;
  background-color: var(--bg-secondary);
  color: var(--text-muted);
  font-weight: 500;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: 12px 16px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.data-table tbody tr {
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.data-table tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.03);
}

.actions-col {
  width: 120px;
  text-align: center;
}

.actions-cell {
  text-align: center;
}

.action-btn {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  margin: 0 2px;
  transition: all var(--transition-fast);
}

.action-btn.default {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.action-btn.default:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.action-btn.primary {
  background-color: var(--accent-blue);
  color: white;
  border: none;
}

.action-btn.primary:hover {
  background-color: var(--accent-blue-hover);
}

.action-btn.danger {
  background-color: var(--accent-red);
  color: white;
  border: none;
}

.action-btn.danger:hover {
  background-color: #dc2626;
}
</style>