<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: string
  color?: 'blue' | 'green' | 'red' | 'yellow'
}>()
</script>

<template>
  <div class="stat-card">
    <div class="stat-header">
      <span class="stat-title">{{ title }}</span>
      <span v-if="icon" class="stat-icon" :class="color || 'blue'">
        <svg v-if="icon === 'order'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        <svg v-else-if="icon === 'money'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>
        </svg>
        <svg v-else-if="icon === 'product'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 2H4c-1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-1-2-2-2zm-1 14H5V9h14v7zm1-5H4V4h16v3z"/>
        </svg>
        <svg v-else-if="icon === 'user'" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
      </span>
    </div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="subtitle || trendValue" class="stat-footer">
      <span v-if="subtitle" class="stat-subtitle">{{ subtitle }}</span>
      <span v-if="trendValue" class="stat-trend" :class="trend">
        {{ trend === 'up' ? '↑' : trend === 'down' ? '↓' : '' }} {{ trendValue }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.stat-title {
  font-size: 13px;
  color: var(--text-muted);
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.blue { background-color: rgba(0, 120, 212, 0.15); color: var(--accent-blue); }
.stat-icon.green { background-color: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
.stat-icon.red { background-color: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
.stat-icon.yellow { background-color: rgba(245, 158, 11, 0.15); color: var(--accent-yellow); }

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.stat-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-trend {
  font-size: 12px;
  font-weight: 500;
}

.stat-trend.up { color: var(--accent-green); }
.stat-trend.down { color: var(--accent-red); }
.stat-trend.neutral { color: var(--text-muted); }
</style>