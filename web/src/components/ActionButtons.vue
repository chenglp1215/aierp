<script setup lang="ts">
interface ActionButton {
  id: string
  label: string
  icon: string
  variant: 'primary' | 'secondary'
  badge?: string
}

const emit = defineEmits<{
  action: [id: string]
}>()

const buttons: ActionButton[] = []

const handleClick = (id: string) => {
  emit('action', id)
}
</script>

<template>
  <div class="action-buttons">
    <button
      v-for="btn in buttons"
      :key="btn.id"
      class="action-btn"
      :class="[btn.variant]"
      @click="handleClick(btn.id)"
    >
      <span class="btn-icon">
        <svg v-if="btn.icon === 'plus'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
        <svg v-else-if="btn.icon === 'download'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <svg v-else-if="btn.icon === 'check'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
        </svg>
      </span>
      <span class="btn-label">{{ btn.label }}</span>
      <span v-if="btn.badge" class="btn-badge">{{ btn.badge }}</span>
    </button>
  </div>
</template>

<style scoped>
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  background-color: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn.primary {
  background-color: var(--color-interactive);
  border-color: var(--color-interactive);
  color: white;
}

.action-btn.primary:hover {
  background-color: var(--color-interactive-hover);
}

.action-btn.secondary {
  background-color: var(--color-canvas);
}

.btn-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon svg {
  width: 100%;
  height: 100%;
}

.btn-label {
  white-space: nowrap;
}

.btn-badge {
  padding: 2px 8px;
  border-radius: 10px;
  background-color: var(--color-success);
  color: white;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>