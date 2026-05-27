<script setup lang="ts">
defineOptions({ name: 'IntelligentSettings' })

import { ref } from 'vue'
import LlmSettings from './LlmSettings.vue'
import KnowledgeBaseSettings from './KnowledgeBaseSettings.vue'
import McpSettings from './McpSettings.vue'
import SkillsSettings from './SkillsSettings.vue'
import AgentSettings from './AgentSettings.vue'

type TabKey = 'llm' | 'knowledge-base' | 'mcp' | 'skills' | 'agent'

const activeTab = ref<TabKey>('llm')

const tabs: { key: TabKey; label: string }[] = [
  { key: 'llm', label: 'LLM 设置' },
  { key: 'knowledge-base', label: '知识库设置' },
  { key: 'mcp', label: 'MCP 设置' },
  { key: 'skills', label: 'Skills 设置' },
  { key: 'agent', label: 'Agent 设置' }
]

const switchTab = (key: TabKey) => {
  activeTab.value = key
}
</script>

<template>
  <div class="intelligent-settings">
    <div class="settings-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="settings-content">
      <LlmSettings v-if="activeTab === 'llm'" />
      <KnowledgeBaseSettings v-if="activeTab === 'knowledge-base'" />
      <McpSettings v-if="activeTab === 'mcp'" />
      <SkillsSettings v-if="activeTab === 'skills'" />
      <AgentSettings v-if="activeTab === 'agent'" />
    </div>
  </div>
</template>

<style scoped>
.intelligent-settings {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
}

.settings-tabs {
  display: flex;
  gap: 8px;
  background-color: var(--color-canvas);
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.tab-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.tab-btn.active {
  background-color: var(--color-interactive);
  color: white;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
}
</style>
