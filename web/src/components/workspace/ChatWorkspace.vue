<script setup lang="ts">
defineOptions({ name: 'ChatWorkspace' })

import { ref, computed, onMounted } from 'vue'
import ChatCard from '../ChatCard.vue'
import { agentApi, chatWsService, aiToolsApi, ChatFile } from '../../services/api'

interface Agent {
  id: string
  name: string
  description?: string
  system_prompt: string
  enabled: boolean
}

interface AgentTab {
  id: string
  label: string
  icon: string
  agentName: string
  welcomeMessage: string
  placeholder: string
}

interface ToolInfo {
  name: string
  cn_name: string
  description: string
  permission_code: string
}

interface ToolCallItem {
  tool: string
  toolName: string
  args: Record<string, any>
  result?: { success: boolean; content: string; error?: string }
}

interface TabState {
  connected: boolean
  connecting: boolean
  messages: Array<{
    id: string
    type: 'user' | 'bot' | 'system'
    content: string
    timestamp: Date
    files?: ChatFile[]
    toolCalls?: ToolCallItem[]
    _pending?: boolean
  }>
  _pendingMessage?: {
    id: string
    toolCalls: ToolCallItem[]
    content: string
  }
  _waitingForResponse: boolean
}

const agents = ref<Agent[]>([])
const loading = ref(false)
const activeTabId = ref<string | null>(null)
const tabStates = ref<Map<string, TabState>>(new Map())
const toolsMap = ref<Map<string, string>>(new Map())

const iconMap: Record<string, string> = {
  '智能问答': 'chat',
  '新建订单': 'order',
  '导出报表': 'report'
}

const getDefaultIcon = (index: number): string => {
  const icons = ['chat', 'order', 'report', 'approval']
  return icons[index % icons.length]
}

const tabs = computed<AgentTab[]>(() => {
  return agents.value
    .filter(a => a.enabled)
    .map((agent, index) => ({
      id: agent.id,
      label: agent.name,
      icon: iconMap[agent.name] || getDefaultIcon(index),
      agentName: agent.name,
      welcomeMessage: agent.system_prompt || `您好！我是 ${agent.name}，请问有什么可以帮您？`,
      placeholder: '输入您的需求...'
    }))
})

const activeTab = computed(() => tabs.value.find(t => t.id === activeTabId.value) || tabs.value[0])

const initTabState = (tabId: string) => {
  if (!tabStates.value.has(tabId)) {
    console.log(`[Workspace] Initializing new state for tab: ${tabId}`)
    tabStates.value.set(tabId, {
      connected: false,
      connecting: false,
      messages: [],
      _waitingForResponse: false
    })
  } else {
    const existing = tabStates.value.get(tabId)!
    console.log(`[Workspace] Using existing state for tab: ${tabId}, connected=${existing.connected}, connecting=${existing.connecting}`)
  }
}

const connectTab = async (tabId: string) => {
  initTabState(tabId)
  const state = tabStates.value.get(tabId)!

  if (state.connecting) {
    console.log(`[Workspace] Tab ${tabId} already connecting`)
    return
  }

  // 检查是否已经连接
  if (chatWsService.isConnected(tabId)) {
    console.log(`[Workspace] Tab ${tabId} already connected (checked via service)`)
    state.connected = true
    state.connecting = false
    return
  }

  console.log(`[Workspace] Starting connection to tab: ${tabId}`)
  state.connecting = true
  state.connected = false // 重置连接状态

  try {
    await chatWsService.connect(tabId)

    chatWsService.onMessage(tabId, (msg) => {
      const tabState = tabStates.value.get(tabId)
      if (!tabState) return

      if (msg.type === 'tool_call_start') {
        if (!tabState._pendingMessage) {
          tabState._pendingMessage = {
            id: Math.random().toString(36).substring(2, 15),
            toolCalls: [],
            content: ''
          }
          tabState.messages.push({
            id: tabState._pendingMessage.id,
            type: 'bot',
            content: '',
            timestamp: new Date(),
            toolCalls: [],
            _pending: true
          })
        }
        const toolName = getToolName(msg.tool || '')
        tabState._pendingMessage.toolCalls.push({
          tool: msg.tool || '',
          toolName: toolName,
          args: msg.args || {},
          result: undefined
        })
        const pendingMsg = tabState.messages.find(m => m.id === tabState._pendingMessage!.id)
        if (pendingMsg && pendingMsg.toolCalls) {
          pendingMsg.toolCalls.push({
            tool: msg.tool || '',
            toolName: toolName,
            args: msg.args || {},
            result: undefined
          })
        }
      } else if (msg.type === 'tool_call_end') {
        if (tabState._pendingMessage && tabState._pendingMessage.toolCalls.length > 0) {
          const lastTool = tabState._pendingMessage.toolCalls[tabState._pendingMessage.toolCalls.length - 1]
          if (lastTool.result === undefined) {
            lastTool.result = {
              success: msg.success ?? false,
              content: msg.content || '',
              error: msg.error
            }
          }
        }
        const pendingMsg = tabState.messages.find(m => m._pending)
        if (pendingMsg && pendingMsg.toolCalls && pendingMsg.toolCalls.length > 0) {
          const lastTool = pendingMsg.toolCalls[pendingMsg.toolCalls.length - 1]
          if (lastTool.result === undefined) {
            lastTool.result = {
              success: msg.success ?? false,
              content: msg.content || '',
              error: msg.error
            }
          }
        }
      } else if (msg.type === 'system' || msg.type === 'text') {
        let toolCalls: ToolCallItem[] = []
        if (tabState._pendingMessage) {
          toolCalls = tabState._pendingMessage.toolCalls
          tabState._pendingMessage = undefined
        }
        const pendingMsg = tabState.messages.find(m => m._pending)
        if (pendingMsg) {
          pendingMsg.content = msg.content || ''
          pendingMsg.toolCalls = toolCalls
          pendingMsg._pending = false
        } else {
          tabState.messages.push({
            id: Math.random().toString(36).substring(2, 15),
            type: 'bot',
            content: msg.content || '',
            timestamp: new Date(),
            files: msg.files,
            toolCalls: toolCalls
          })
        }
        tabState._waitingForResponse = false
      } else if (msg.type === 'error') {
        let toolCalls: ToolCallItem[] = []
        if (tabState._pendingMessage) {
          toolCalls = tabState._pendingMessage.toolCalls
          tabState._pendingMessage = undefined
        }
        const pendingMsg = tabState.messages.find(m => m._pending)
        if (pendingMsg) {
          pendingMsg.content = `[错误] ${msg.content}`
          pendingMsg.toolCalls = toolCalls
          pendingMsg._pending = false
        } else {
          tabState.messages.push({
            id: Math.random().toString(36).substring(2, 15),
            type: 'bot',
            content: `[错误] ${msg.content}`,
            timestamp: new Date(),
            toolCalls: toolCalls
          })
        }
        tabState._waitingForResponse = false
      }
    })

    state.connected = true
    console.log(`[Workspace] Connected to tab: ${tabId}`)
  } catch (error) {
    console.error(`[Workspace] Failed to connect tab ${tabId}:`, error)
    state.connected = false
    // 连接失败时，重置连接状态，允许重试
    state.connecting = false
  } finally {
    // 只有在连接成功时才设置connecting为false
    if (state.connected) {
      state.connecting = false
    }
  }
}

const handleTabSwitch = async (tabId: string) => {
  if (activeTabId.value === tabId) {
    console.log(`[Workspace] Tab ${tabId} already active, skip`)
    return
  }

  console.log(`[Workspace] Switching to tab: ${tabId}, current activeTabId: ${activeTabId.value}`)
  activeTabId.value = tabId
  initTabState(tabId)

  const state = tabStates.value.get(tabId)!
  console.log(`[Workspace] Tab ${tabId} state: connected=${state.connected}, connecting=${state.connecting}`)

  // 无论连接状态如何，都尝试连接（除了chat标签）
  console.log(`[Workspace] Triggering connect for tab: ${tabId}`)
  await connectTab(tabId)
}

const handleMessageFromCard = (message: string, agentId: string, files?: ChatFile[]) => {
  const tabState = tabStates.value.get(agentId)
  if (!tabState) return

  const userMessage = {
    id: Math.random().toString(36).substring(2, 15),
    type: 'user' as const,
    content: message,
    timestamp: new Date(),
    files: files
  }
  tabState.messages.push(userMessage)
  tabState._waitingForResponse = true

  chatWsService.sendMessage(agentId, message, files)
}

const loadAgents = async () => {
  loading.value = true
  try {
    const res = await agentApi.list({ page_size: 100 })
    agents.value = res.items || []
    if (agents.value.length > 0 && !activeTabId.value) {
      const firstTab = agents.value.filter(a => a.enabled)[0]
      if (firstTab) {
        const tabId = firstTab.id
        activeTabId.value = tabId
        initTabState(tabId)

        const state = tabStates.value.get(tabId)!
        if (tabId === 'chat') {
          if (state.messages.length === 0) {
            state.messages.push({
              id: Math.random().toString(36).substring(2, 15),
              type: 'bot',
              content: firstTab.system_prompt || `您好！我是 ${firstTab.name}，请问有什么可以帮您？`,
              timestamp: new Date()
            })
          }
        } else if (!state.connected && !state.connecting) {
          await connectTab(tabId)
        }
      }
    }
  } catch (error) {
    console.error('加载 Agent 列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTools = async () => {
  try {
    const res = await aiToolsApi.listTools()
    if (res.items) {
      res.items.forEach((tool: ToolInfo) => {
        toolsMap.value.set(tool.name, tool.cn_name || tool.name)
      })
    }
  } catch (error) {
    console.error('加载工具列表失败:', error)
  }
}

const getToolName = (tool: string): string => {
  return toolsMap.value.get(tool) || tool
}

const getTabIcon = (tab: AgentTab) => {
  const icons: Record<string, string> = {
    chat: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z',
    order: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 15h8v2H8v-2zm0-4h8v2H8v-2z',
    report: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z',
    approval: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'
  }
  return icons[tab.icon] || icons.chat
}

onMounted(() => {
  loadTools()
  loadAgents()
})
</script>

<template>
  <div class="chat-workspace">
    <div class="workspace-tabs" v-if="!loading">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTabId === tab.id }]"
        @click="handleTabSwitch(tab.id)"
      >
        <svg class="tab-icon" viewBox="0 0 24 24" fill="currentColor">
          <path :d="getTabIcon(tab)" />
        </svg>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>
    <div v-else class="loading-tabs">
      <span>加载中...</span>
    </div>

    <ChatCard
      v-if="activeTab"
      class="chat-card-container"
      :agent-name="activeTab.agentName"
      :welcome-message="activeTab.welcomeMessage"
      :placeholder="activeTab.placeholder"
      :agent-id="activeTab.id"
      :tab-state="tabStates.get(activeTab.id)"
      :is-active="activeTabId === activeTab.id"
      @send="handleMessageFromCard"
      @connect="connectTab"
    />
  </div>
</template>

<style scoped>
.chat-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  max-width: 66.67%;
}

@media (max-width: 1024px) {
  .chat-workspace {
    max-width: 100%;
  }
}

.workspace-tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.tab-btn.active {
  background-color: var(--accent-blue);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 120, 212, 0.3);
}

.tab-icon {
  width: 18px;
  height: 18px;
}

.loading-tabs {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: var(--text-muted);
  font-size: 14px;
}

@media (max-width: 640px) {
  .tab-label {
    display: none;
  }

  .tab-btn {
    padding: 10px 12px;
  }

  .tab-icon {
    width: 20px;
    height: 20px;
  }
}

.chat-card-container {
  flex: 1;
  min-height: 0;
}
</style>