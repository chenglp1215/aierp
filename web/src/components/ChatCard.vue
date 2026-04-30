<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { chatWsService, ChatMessage, uploadApi, ChatFile } from '../services/api'
import ToolCallItem, { type ToolCallData } from './ToolCallItem.vue'
import AgentDataDisplay, { type AgentResponse } from './AgentDataDisplay.vue'

const props = withDefaults(defineProps<{
  agentName?: string
  welcomeMessage?: string
  placeholder?: string
  agentId?: string
  tabState?: {
    connected: boolean
    connecting: boolean
    messages: Array<{
      id: string
      type: 'user' | 'bot' | 'system'
      content: string
      timestamp: Date
      files?: ChatFile[]
      toolCalls?: ToolCallData[]
      _pending?: boolean
      userName?: string
      userAvatar?: string
    }>
    _waitingForResponse?: boolean
  }
  isActive?: boolean
  userName?: string
  userAvatar?: string
}>(), {
  agentName: 'ERP 智能助手',
  welcomeMessage: '您好！我是 ERP 智能助手，可以帮您查询订单、客户、库存、财务等业务数据，请问有什么可以帮您？',
  placeholder: '输入您的需求，例如：查询本月销售额最高的10家客户',
  agentId: 'chat',
  isActive: false,
  userName: '用户',
  userAvatar: ''
})

const emit = defineEmits<{
  send: [message: string, agentId: string, files?: ChatFile[], userName?: string, userAvatar?: string]
  connect: [agentId: string]
}>()

const parseAgentResponse = (content: string): AgentResponse | null => {
  if (!content) return null
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object' && (parsed.text || parsed.related_data || parsed.next_step)) {
      return parsed as AgentResponse
    }
  } catch {}
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      if (parsed && typeof parsed === 'object' && (parsed.text || parsed.related_data || parsed.next_step)) {
        return parsed as AgentResponse
      }
    }
  } catch {}
  return null
}

const isAgentResponse = (content: string): boolean => {
  return parseAgentResponse(content) !== null
}

const message = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const mode = ref<'chat' | 'task'>('chat')
const taskMessages = ref<{ text: string; files: ChatFile[] }[]>([])
const localMessages = ref<Array<{
  id: string
  type: 'user' | 'bot' | 'system'
  content: string
  timestamp: Date
  files?: ChatFile[]
  toolCalls?: ToolCallData[]
  _pending?: boolean
  userName?: string
  userAvatar?: string
}>>([])

const pendingBotMessage = ref<{
  id: string
  toolCalls: ToolCallData[]
  content: string
} | null>(null)

const getLastBotMessage = () => {
  const messages = props.tabState?.messages || localMessages.value
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].type === 'bot') {
      return messages[i]
    }
  }
  return null
}

const updateLastBotMessage = (content: string, toolCalls?: ToolCallData[]) => {
  const lastBot = getLastBotMessage()
  if (lastBot) {
    lastBot.content = content
    if (toolCalls !== undefined) {
      lastBot.toolCalls = toolCalls
    }
    return true
  }
  return false
}

const pendingFiles = ref<ChatFile[]>([])
const isUploading = ref(false)
const uploadError = ref('')
const previewVisible = ref(false)
const previewImage = ref('')

const fileInputRef = ref<HTMLInputElement | null>(null)

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const ALLOWED_DOCUMENT_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain',
  'text/markdown'
]
const MAX_FILE_SIZE = 10 * 1024 * 1024

let unsubscribe: (() => void) | null = null

const generateId = () => Math.random().toString(36).substring(2, 15)

const addBotMessage = (content: string, toolCalls?: ToolCallData[]) => {
  localMessages.value.push({
    id: generateId(),
    type: 'bot',
    content,
    timestamp: new Date(),
    toolCalls: toolCalls || []
  })
}

const handleToolCallStart = (tool: string, args: Record<string, any>) => {
  if (!pendingBotMessage.value) {
    const lastBot = getLastBotMessage()
    pendingBotMessage.value = {
      id: lastBot?.id || generateId(),
      toolCalls: lastBot?.toolCalls ? [...lastBot.toolCalls] : [],
      content: lastBot?.content || ''
    }
  }
  pendingBotMessage.value.toolCalls.push({
    tool,
    args,
    result: undefined
  })
}

const handleToolCallEnd = (success: boolean, content: string, error?: string) => {
  if (!pendingBotMessage.value || pendingBotMessage.value.toolCalls.length === 0) return

  const lastToolCall = pendingBotMessage.value.toolCalls[pendingBotMessage.value.toolCalls.length - 1]
  if (lastToolCall && lastToolCall.result === undefined) {
    lastToolCall.result = { success, content, error }
  }
}

const handleMessage = (msg: ChatMessage) => {
  switch (msg.type) {
    case 'system':
    case 'text':
      isLoading.value = false
      if (msg.content) {
        if (pendingBotMessage.value) {
          pendingBotMessage.value.content = msg.content
          addBotMessage(pendingBotMessage.value.content, pendingBotMessage.value.toolCalls)
          pendingBotMessage.value = null
        } else {
          const updated = updateLastBotMessage(msg.content)
          if (!updated) {
            addBotMessage(msg.content)
          }
        }
      }
      break
    case 'pong':
      console.log('[Chat] Pong received')
      break
    case 'tool_call_start':
      handleToolCallStart(msg.tool || '', msg.args || {})
      break
    case 'tool_call_end':
      handleToolCallEnd(msg.success ?? false, msg.content || '', msg.error)
      break
    case 'error':
      isLoading.value = false
      if (pendingBotMessage.value) {
        pendingBotMessage.value.content = `[错误] ${msg.content}`
        addBotMessage(pendingBotMessage.value.content, pendingBotMessage.value.toolCalls)
        pendingBotMessage.value = null
      } else {
        const updated = updateLastBotMessage(`[错误] ${msg.content}`)
        if (!updated) {
          addBotMessage(`[错误] ${msg.content}`)
        }
      }
      break
  }
}

const disconnectWebSocket = () => {
  if (unsubscribe) {
    unsubscribe()
    unsubscribe = null
  }
  if (props.agentId !== 'chat') {
    chatWsService.disconnect(props.agentId)
  }
  isConnected.value = false
}

const validateFile = (file: File): string | null => {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  const isImage = ALLOWED_IMAGE_TYPES.includes(file.type) || ['.jpg', '.jpeg', '.png', '.gif', '.webp'].includes(ext)
  const isDocument = ALLOWED_DOCUMENT_TYPES.includes(file.type) || ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.md'].includes(ext)

  if (!isImage && !isDocument) {
    return `不支持的文件类型: ${ext}。支持的图片格式: jpg, png, gif, webp; 支持的文档格式: pdf, doc, docx, xls, xlsx, txt, md`
  }

  if (file.size > MAX_FILE_SIZE) {
    return `文件大小超过限制(10MB)`
  }

  return null
}

const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  uploadError.value = ''

  for (const file of Array.from(input.files)) {
    const error = validateFile(file)
    if (error) {
      uploadError.value = error
      continue
    }

    isUploading.value = true
    try {
      const response = await uploadApi.upload(file, file.name)
      pendingFiles.value.push({
        file_id: response.file_id,
        file_name: response.file_name,
        file_url: response.file_url,
        file_path: response.file_path,
        file_type: response.file_type,
        file_size: response.file_size
      })
    } catch (error) {
      uploadError.value = error instanceof Error ? error.message : '上传失败'
    } finally {
      isUploading.value = false
    }
  }

  input.value = ''
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const removePendingFile = (fileId: string) => {
  pendingFiles.value = pendingFiles.value.filter(f => f.file_id !== fileId)
}

const canSend = computed(() => {
  return message.value.trim() || pendingFiles.value.length > 0
})

const hasPendingMessage = computed(() => {
  const messages = props.tabState?.messages || localMessages.value
  return messages.some(m => m._pending)
})

const handleSend = () => {
  if (!canSend.value) return

  const userMessage = message.value.trim()

  if (mode.value === 'task') {
    taskMessages.value.push({ text: userMessage, files: [...pendingFiles.value] })
    message.value = ''
    pendingFiles.value = []
    return
  }

  emit('send', userMessage, props.agentId, pendingFiles.value, props.userName, props.userAvatar)
  message.value = ''
  pendingFiles.value = []
}

const handleStartTask = () => {
  if (taskMessages.value.length === 0 && !message.value.trim() && pendingFiles.value.length === 0) return

  if (pendingFiles.value.length > 0) {
    taskMessages.value.push({ text: message.value.trim(), files: [...pendingFiles.value] })
    pendingFiles.value = []
  }

  const combinedText = taskMessages.value.map(m => m.text).filter(t => t).join('\n')
  const allFiles = taskMessages.value.flatMap(m => m.files || [])

  emit('send', combinedText, props.agentId, allFiles, props.userName, props.userAvatar)
  taskMessages.value = []
  message.value = ''
}

const handleModeSwitch = (newMode: 'chat' | 'task') => {
  mode.value = newMode
}

const handleClearHistory = () => {
  if (props.tabState) {
    if (chatWsService.clearHistory(props.agentId)) {
      props.tabState.messages = []
    }
  }
}

const getAvatarGradient = (id: string) => {
  const gradients: Record<string, string> = {
    chat: 'linear-gradient(135deg, var(--accent-blue), #005a9e)',
    order: 'linear-gradient(135deg, #10b981, #059669)',
    report: 'linear-gradient(135deg, #f59e0b, #d97706)',
    approval: 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
  }
  return gradients[id] || gradients.chat
}

const getFileIcon = (fileType: string) => {
  if (fileType === 'image') {
    return 'M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z'
  }
  return 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z'
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const openPreview = (url: string) => {
  previewImage.value = url
  previewVisible.value = true
}

const closePreview = () => {
  previewVisible.value = false
  previewImage.value = ''
}

const downloadFile = (file: ChatFile) => {
  const link = document.createElement('a')
  link.href = file.file_url
  link.download = file.file_name
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const handleNextStepClick = (step: string, selectedData?: string) => {
  let fullMessage = ''
  if (selectedData) {
    fullMessage = `${selectedData}\n执行：${step}`
  } else {
    fullMessage = step
  }
  message.value = fullMessage
  setTimeout(() => {
    handleSend()
  }, 50)
}

const scrollToBottom = () => {
  const chatBody = document.querySelector('.chat-messages')
  if (chatBody) {
    setTimeout(() => {
      chatBody.scrollTop = chatBody.scrollHeight
    }, 50)
  }
}

watch(() => props.tabState, (newState) => {
  if (newState) {
    const wasConnected = isConnected.value
    isConnected.value = newState.connected
    if (newState.connected && !wasConnected) {
      isLoading.value = true
      if (unsubscribe) {
        unsubscribe()
      }
      unsubscribe = chatWsService.onMessage(props.agentId, handleMessage)
    } else if (!newState.connected && unsubscribe) {
      disconnectWebSocket()
    }
    if (props.agentId === 'chat' && !newState.connected) {
      isConnected.value = true
    }
  }
}, { immediate: true, deep: true })

watch(() => props.isActive, (active) => {
  if (active) {
    scrollToBottom()
  }
}, { immediate: true })

watch(() => props.tabState?.messages, () => {
  if (props.isActive) {
    scrollToBottom()
  }
}, { deep: true })

watch(() => props.tabState?._waitingForResponse, (waiting) => {
  isLoading.value = waiting || props.tabState?.connecting || false
})

onMounted(() => {
  if (props.isActive) {
    scrollToBottom()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<template>
  <div class="chat-card">
    <div class="card-header">
      <div class="header-left">
        <div class="bot-avatar" :style="{ background: getAvatarGradient(agentId) }">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
          </svg>
        </div>
        <div class="header-text">
          <h3 class="header-title">{{ agentName }}</h3>
          <div class="header-status">
            <span :class="['status-dot', { connected: isConnected }]"></span>
            <span class="status-text">{{ isConnected ? '在线' : '离线' }}</span>
          </div>
        </div>
      </div>
      <div class="header-badge">
        <button class="clear-btn" @click="handleClearHistory" title="清空对话">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
        </button>
        <div class="mode-toggle">
          <button
            :class="['mode-btn', { active: mode === 'chat' }]"
            @click="handleModeSwitch('chat')"
          >
            聊天
          </button>
          <button
            :class="['mode-btn', { active: mode === 'task' }]"
            @click="handleModeSwitch('task')"
          >
            任务
          </button>
        </div>
      </div>
    </div>

    <div class="chat-body">
      <div class="chat-messages">
        <div
          v-for="msg in (tabState?.messages || localMessages)"
          :key="msg.id"
          :class="['message', msg.type === 'user' ? 'user-message' : 'bot-message']"
        >
          <div v-if="msg.type === 'user'" class="user-message-header">
            <img v-if="msg.userAvatar" :src="msg.userAvatar" class="user-avatar" />
            <div v-else class="user-avatar-placeholder">{{ (msg.userName || '用户').charAt(0) }}</div>
            <span class="user-name">{{ msg.userName || '用户' }}</span>
          </div>
          <div v-if="msg.type !== 'user'" class="message-avatar" :style="{ background: getAvatarGradient(agentId) }">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
            </svg>
          </div>
          <div class="message-bubble">
            <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-calls-container">
              <div class="tool-calls-header">
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <path d="M22 9V7h-2V5c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-2h2v-2h-2v-2h2v-2h-2V9h2zm-4 10H4V5h14v14zM6 13h5v4H6zm6-6h4v3h-4zm0 4h4v6h-4zm6-4h5v2h-5zm0 4h5v2h-5z"/>
                </svg>
                <span>工具调用 ({{ msg.toolCalls.length }})</span>
              </div>
              <ToolCallItem
                v-for="(toolCall, index) in msg.toolCalls"
                :key="index"
                :tool-call="toolCall"
                :index="index"
              />
              <div v-if="msg._pending && !msg.content" class="tool-loading">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
              </div>
            </div>
            <div v-if="msg.content && !msg._pending">
              <template v-if="isAgentResponse(msg.content)">
                <div class="agent-response">
                  <div v-if="parseAgentResponse(msg.content)?.text" class="agent-text">
                    {{ parseAgentResponse(msg.content)?.text }}
                  </div>
                  <AgentDataDisplay
                    v-if="parseAgentResponse(msg.content)?.related_data || parseAgentResponse(msg.content)?.next_step?.length"
                    :response="parseAgentResponse(msg.content) as AgentResponse"
                    @action="handleNextStepClick"
                  />
                </div>
              </template>
              <template v-else>
                <div class="message-text">{{ msg.content }}</div>
              </template>
            </div>
            <div v-if="msg.files && msg.files.length > 0" class="message-files">
              <div v-for="file in msg.files" :key="file.file_id" class="message-file">
                <img v-if="file.file_type === 'image'" :src="file.file_url" :alt="file.file_name" class="file-image" @click="openPreview(file.file_url)" />
                <div v-else class="file-info" @click="downloadFile(file)">
                  <svg class="file-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path :d="getFileIcon(file.file_type)" />
                  </svg>
                  <span class="file-name">{{ file.file_name }}</span>
                  <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="isLoading && !hasPendingMessage" class="message bot-message">
          <div class="message-avatar" :style="{ background: getAvatarGradient(agentId) }">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
            </svg>
          </div>
          <div class="message-bubble loading">
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <div v-if="pendingFiles.length > 0" class="pending-files">
          <div v-for="file in pendingFiles" :key="file.file_id" class="pending-file">
            <img v-if="file.file_type === 'image'" :src="file.file_url" :alt="file.file_name" class="pending-file-image" />
            <div v-else class="pending-file-info">
              <svg class="file-icon" viewBox="0 0 24 24" fill="currentColor">
                <path :d="getFileIcon(file.file_type)" />
              </svg>
              <span class="file-name">{{ file.file_name }}</span>
            </div>
            <button class="remove-file-btn" @click="removePendingFile(file.file_id)">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>

        <div v-if="mode === 'task'" class="task-panel">
          <div class="task-header">
            <span class="task-hint">已收集 {{ taskMessages.length }} 条消息</span>
          </div>
          <div v-if="taskMessages.length > 0" class="task-messages">
            <div v-for="(msg, index) in taskMessages" :key="index" class="task-message-item">
              <span class="task-msg-index">{{ index + 1 }}.</span>
              <div class="task-msg-wrapper">
                <span v-if="msg.text" class="task-msg-content">{{ msg.text }}</span>
                <span v-if="msg.text && msg.files && msg.files.length > 0" class="task-msg-separator">+</span>
                <div v-if="msg.files && msg.files.length > 0" class="task-msg-files">
                  <div v-for="file in msg.files" :key="file.file_id" class="task-file-item">
                    <img v-if="file.file_type === 'image'" :src="file.file_url" :alt="file.file_name" class="task-file-thumb" />
                    <svg v-else class="task-file-icon" viewBox="0 0 24 24" fill="currentColor">
                      <path :d="getFileIcon(file.file_type)" />
                    </svg>
                    <span class="task-file-name">{{ file.file_name }}</span>
                  </div>
                </div>
                <span v-if="!msg.text && (!msg.files || msg.files.length === 0)" class="task-msg-empty">[空消息]</span>
              </div>
            </div>
          </div>
          <div class="task-actions">
            <button class="start-task-btn" @click="handleStartTask" :disabled="taskMessages.length === 0 && !message.trim() && pendingFiles.length === 0">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              开始任务
            </button>
          </div>
        </div>

        <div class="input-row">
          <button class="attach-btn" @click="triggerFileInput" :disabled="isUploading">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/>
            </svg>
          </button>
          <input
            ref="fileInputRef"
            type="file"
            class="hidden-file-input"
            accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.md"
            multiple
            @change="handleFileSelect"
          />
          <div class="input-wrapper">
            <input
              v-model="message"
              type="text"
              class="chat-input"
              :placeholder="placeholder"
              @keyup.enter="handleSend"
            />
          </div>
          <button class="send-btn" @click="handleSend" :disabled="!canSend || isUploading">
            <svg class="send-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
            <span>{{ mode === 'task' ? '添加' : '发送' }}</span>
          </button>
        </div>
      </div>

      <div v-if="previewVisible" class="preview-modal" @click="closePreview">
        <div class="preview-content" @click.stop>
          <img :src="previewImage" alt="预览" class="preview-image" />
          <button class="preview-close" @click="closePreview">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.bot-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  transition: background var(--transition-fast);
}

.bot-avatar svg {
  width: 100%;
  height: 100%;
  color: white;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted);
  transition: background-color var(--transition-fast);
}

.status-dot.connected {
  background-color: var(--accent-green);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.header-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: var(--accent-red);
}

.clear-btn:hover svg {
  color: var(--accent-red);
}

.clear-btn svg {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.mode-toggle {
  display: flex;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn:hover {
  color: var(--text-primary);
}

.mode-btn.active {
  background-color: var(--accent-blue);
  color: white;
}

.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  min-height: 0;
  scroll-behavior: smooth;
}

.message {
  display: flex;
  gap: 12px;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  flex-shrink: 0;
  transition: background var(--transition-fast);
}

.message-avatar svg {
  width: 100%;
  height: 100%;
  color: white;
}

.message-bubble {
  background-color: var(--bg-secondary);
  padding: 14px 18px;
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  max-width: 75%;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.tool-calls-container {
  margin-top: 12px;
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}

.tool-calls-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.tool-calls-header svg {
  color: var(--accent-blue);
}

.tool-loading {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  padding: 12px 0 4px;
}

.message-file {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.file-image:hover {
  opacity: 0.8;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.file-info:hover {
  background-color: var(--bg-card);
}

.file-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-blue);
}

.file-name {
  font-size: 13px;
  color: var(--text-primary);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: var(--text-muted);
}

.user-message {
  flex-direction: column;
  align-items: flex-end;
}

.user-message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  padding-right: 4px;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--accent-blue);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  font-size: 12px;
  color: var(--text-muted);
}

.user-message .message-bubble {
  background-color: var(--accent-blue);
  color: white;
  border-top-right-radius: 4px;
}

.bot-message .message-bubble {
  border-top-left-radius: 4px;
}

.message-bubble.loading {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 20px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
  flex-shrink: 0;
}

.pending-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pending-file {
  position: relative;
  display: flex;
  align-items: center;
}

.pending-file-image {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  border: 2px solid var(--accent-blue);
}

.pending-file-info {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.pending-file-info .file-icon {
  width: 16px;
  height: 16px;
}

.pending-file-info .file-name {
  font-size: 12px;
  max-width: 80px;
}

.remove-file-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: var(--accent-red, #ef4444);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.remove-file-btn svg {
  width: 12px;
  height: 12px;
  color: white;
}

.upload-error {
  font-size: 12px;
  color: var(--accent-red, #ef4444);
  padding: 6px 10px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.attach-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.attach-btn:hover:not(:disabled) {
  background-color: var(--bg-card);
  border-color: var(--accent-blue);
}

.attach-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attach-btn svg {
  width: 20px;
  height: 20px;
  color: var(--text-muted);
}

.hidden-file-input {
  display: none;
}

.input-wrapper {
  flex: 1;
}

.chat-input {
  width: 100%;
  padding: 14px 18px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color var(--transition-fast);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.chat-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.15);
  outline: none;
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background-color: var(--accent-blue);
  color: white;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.send-btn:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
  transform: translateY(-1px);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  width: 18px;
  height: 18px;
}

.task-panel {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.task-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.task-messages {
  max-height: 120px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.task-message-item {
  display: flex;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary);
  padding: 6px 8px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
}

.task-msg-index {
  color: var(--accent-blue);
  font-weight: 500;
  flex-shrink: 0;
}

.task-msg-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-msg-separator {
  color: var(--text-muted);
  font-size: 12px;
}

.task-msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.task-file-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.task-file-thumb {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  object-fit: cover;
}

.task-file-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-blue);
}

.task-file-name {
  font-size: 11px;
  color: var(--text-secondary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-msg-empty {
  color: var(--text-muted);
  font-style: italic;
}

.task-msg-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
}

.start-task-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: var(--accent-green);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.start-task-btn:hover:not(:disabled) {
  background-color: #0ea572;
  transform: translateY(-1px);
}

.start-task-btn:active:not(:disabled) {
  transform: translateY(0);
}

.start-task-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.start-task-btn svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 768px) {
  .chat-input-area {
    flex-direction: column;
  }

  .send-btn {
    justify-content: center;
  }

  .message-bubble {
    max-width: 85%;
  }

  .file-image {
    max-width: 150px;
    max-height: 100px;
  }
}

.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
}

.preview-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  cursor: default;
}

.preview-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--radius-md);
}

.preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--transition-fast);
}

.preview-close:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.preview-close svg {
  width: 20px;
  height: 20px;
  color: white;
}

.agent-response {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.agent-data {
  margin-top: 8px;
}

.data-table-container {
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
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  min-width: 100px;
  font-weight: 500;
  color: var(--text-muted);
}

.form-value {
  flex: 1;
  color: var(--text-primary);
}

.data-key-value {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.kv-item {
  display: flex;
  gap: 12px;
  padding: 6px 0;
}

.kv-label {
  min-width: 100px;
  font-weight: 500;
  color: var(--text-muted);
}

.kv-value {
  flex: 1;
  color: var(--text-primary);
  word-break: break-word;
}

.agent-next-step {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
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
</style>
