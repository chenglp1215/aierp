<script setup lang="ts">
defineOptions({ name: 'McpSettings' })

import { ref, onMounted } from 'vue'
import { mcpApi } from '../../services/api'

interface McpServer {
  id?: string
  name: string
  description?: string
  server_type: string
  url?: string
  status: string
  tool_count?: number
  created_at?: string
  timeout?: number
}

interface EnvVar {
  key: string
  value: string
}

interface Tool {
  name: string
  description?: string
  input_schema?: any
}

const servers = ref<McpServer[]>([])
const serverTools = ref<Record<string, Tool[]>>({})
const expandedServer = ref<string | null>(null)
const loading = ref(false)
const formLoading = ref(false)
const deleteLoading = ref(false)
const testingServerId = ref<string | null>(null)

const showServerModal = ref(false)
const showDeleteConfirm = ref(false)
const editingServer = ref<McpServer | null>(null)
const deleteTargetId = ref<string | null>(null)

const serverForm = ref<Partial<McpServer>>({
  name: '',
  description: '',
  server_type: 'stdio',
  url: '',
  status: 'active'
})

const envVars = ref<EnvVar[]>([{ key: '', value: '' }])

const serverTypes = [
  { value: 'stdio', label: 'STDIO' },
  { value: 'http', label: 'HTTP' },
  { value: 'sse', label: 'SSE' }
]

const serverColumns = [
  { key: 'name', label: '服务器名称' },
  { key: 'server_type', label: '类型' },
  { key: 'url', label: 'URL' },
  { key: 'status', label: '状态' },
  { key: 'tool_count', label: '工具数量' }
]

const loadServers = async () => {
  loading.value = true
  try {
    const res = await mcpApi.list()
    servers.value = res.items || []
  } catch (error) {
    console.error('加载MCP服务器列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadServerTools = async (serverId: string) => {
  if (serverTools.value[serverId]) return
  try {
    const res = await mcpApi.getTools(serverId)
    serverTools.value[serverId] = res.items || res || []
  } catch (error) {
    console.error('加载工具列表失败:', error)
    serverTools.value[serverId] = []
  }
}

const toggleServerTools = async (server: McpServer) => {
  if (expandedServer.value === server.id) {
    expandedServer.value = null
  } else {
    expandedServer.value = server.id || null
    if (server.id) {
      loadServerTools(server.id)
    }
  }
}

const testConnection = async (serverId: string) => {
  testingServerId.value = serverId
  try {
    await mcpApi.testConnection(serverId)
    window.showToast('连接测试成功', 'success')
  } catch (error: any) {
    window.showToast(error.message || '连接测试失败', 'error')
  } finally {
    testingServerId.value = null
  }
}

const resetServerForm = () => {
  serverForm.value = {
    name: '',
    description: '',
    server_type: 'stdio',
    url: '',
    status: 'active'
  }
  envVars.value = [{ key: '', value: '' }]
  editingServer.value = null
}

const openCreateServer = () => {
  resetServerForm()
  showServerModal.value = true
}

const openEditServer = (server: McpServer) => {
  editingServer.value = server
  serverForm.value = { ...server }
  envVars.value = [{ key: '', value: '' }]
  showServerModal.value = true
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const addEnvVar = () => {
  envVars.value.push({ key: '', value: '' })
}

const removeEnvVar = (index: number) => {
  envVars.value.splice(index, 1)
}

const getEnvVarsObject = () => {
  const obj: Record<string, string> = {}
  envVars.value.forEach(({ key, value }) => {
    if (key.trim()) {
      obj[key.trim()] = value
    }
  })
  return obj
}

const handleSaveServer = async () => {
  if (!serverForm.value.name?.trim()) {
    window.showToast('请输入服务器名称', 'warning')
    return
  }
  formLoading.value = true
  try {
    const data = {
      ...serverForm.value,
      env_vars: getEnvVarsObject()
    }
    if (editingServer.value?.id) {
      await mcpApi.update(editingServer.value.id, data)
      window.showToast('服务器更新成功', 'success')
      const index = servers.value.findIndex(s => s.id === editingServer.value!.id)
      if (index !== -1) {
        servers.value[index] = {
          ...servers.value[index],
          ...data
        }
      }
    } else {
      await mcpApi.create(data)
      window.showToast('服务器创建成功', 'success')
      loadServers()
    }
    showServerModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  deleteLoading.value = true
  try {
    await mcpApi.delete(deleteTargetId.value)
    window.showToast('服务器删除成功', 'success')
    servers.value = servers.value.filter(s => s.id !== deleteTargetId.value)
    if (expandedServer.value === deleteTargetId.value) {
      expandedServer.value = null
    }
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    deleteLoading.value = false
  }
}

const formatServerType = (type: string) => {
  const found = serverTypes.find(t => t.value === type)
  return found ? found.label : type
}

const formatStatus = (status: string) => {
  return status === 'active' ? '启用' : '禁用'
}

onMounted(() => {
  loadServers()
})
</script>

<template>
  <div class="mcp-settings">
    <section class="settings-section">
      <div class="section-header">
        <h3 class="section-title">MCP 服务器</h3>
        <button class="primary-btn" @click="openCreateServer">添加服务器</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in serverColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 320px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td :colspan="serverColumns.length + 1" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="servers.length === 0">
              <td :colspan="serverColumns.length + 1" class="empty-cell">暂无服务器</td>
            </tr>
            <template v-else v-for="server in servers" :key="server.id">
              <tr>
                <td>{{ server.name }}</td>
                <td>{{ formatServerType(server.server_type) }}</td>
                <td class="url-cell" :title="server.url">{{ server.url || '-' }}</td>
                <td>
                  <span class="status-tag" :class="server.status">
                    {{ formatStatus(server.status) }}
                  </span>
                </td>
                <td>{{ server.tool_count || 0 }}</td>
                <td>
                  <div class="action-buttons">
                    <button class="btn-link" @click="toggleServerTools(server)">
                      {{ expandedServer === server.id ? '隐藏工具' : '查看工具' }}
                    </button>
                    <button class="btn-link" @click="testConnection(server.id!)" :disabled="testingServerId === server.id">
                      {{ testingServerId === server.id ? '测试中...' : '测试' }}
                    </button>
                    <button class="btn-link" @click="openEditServer(server)">编辑</button>
                    <button class="btn-link danger" @click="confirmDelete(server.id!)">删除</button>
                  </div>
                </td>
              </tr>
              <tr v-if="expandedServer === server.id" class="tools-row">
                <td :colspan="serverColumns.length + 1">
                  <div class="tools-panel">
                    <h4>提供的工具 ({{ serverTools[server.id!]?.length || 0 }})</h4>
                    <div class="tools-list" v-if="serverTools[server.id!]?.length">
                      <div class="tool-item" v-for="tool in serverTools[server.id!]" :key="tool.name">
                        <span class="tool-name">{{ tool.name }}</span>
                        <span class="tool-desc">{{ tool.description || '无描述' }}</span>
                      </div>
                    </div>
                    <div class="empty-tools" v-else>暂无可用工具</div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <div class="modal-overlay" v-if="showServerModal" @click.self="showServerModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingServer ? '编辑服务器' : '添加服务器' }}</h3>
          <button class="modal-close" @click="showServerModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>服务器名称 *</label>
            <input type="text" v-model="serverForm.name" placeholder="请输入服务器名称" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="serverForm.description" placeholder="请输入描述" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>服务器类型</label>
              <select v-model="serverForm.server_type">
                <option v-for="t in serverTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>连接超时 (秒)</label>
              <input type="number" v-model.number="serverForm.timeout" min="5" max="300" />
            </div>
          </div>
          <div class="form-group">
            <label>服务器 URL 或命令</label>
            <input type="text" v-model="serverForm.url" placeholder="http://localhost:3000 或 npx ..." />
          </div>
          <div class="form-group">
            <label>环境变量</label>
            <div class="env-vars">
              <div class="env-var-row" v-for="(env, index) in envVars" :key="index">
                <input type="text" v-model="env.key" placeholder="Key" />
                <input type="text" v-model="env.value" placeholder="Value" />
                <button class="remove-env-btn" @click="removeEnvVar(index)" v-if="envVars.length > 1">×</button>
              </div>
              <button class="add-env-btn" @click="addEnvVar">+ 添加环境变量</button>
            </div>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="serverForm.status">
              <option value="active">启用</option>
              <option value="inactive">禁用</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showServerModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveServer" :disabled="formLoading">
            {{ formLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除该服务器吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mcp-settings {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.table-section {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.data-table th {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.data-table td {
  font-size: 13px;
  color: var(--text-primary);
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.url-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.status-tag.inactive {
  background-color: rgba(128, 128, 128, 0.1);
  color: var(--text-muted);
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.btn-link:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.btn-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tools-row td {
  padding: 0;
  background-color: var(--bg-secondary);
}

.tools-panel {
  padding: 16px 20px;
}

.tools-panel h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
}

.tool-name {
  font-weight: 500;
  color: var(--accent-blue);
  font-size: 13px;
}

.tool-desc {
  color: var(--text-muted);
  font-size: 12px;
}

.empty-tools {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group textarea {
  resize: vertical;
}

.env-vars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.env-var-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
  align-items: center;
}

.remove-env-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
  border: none;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-env-btn:hover {
  background-color: var(--accent-red);
  color: white;
}

.add-env-btn {
  padding: 8px 12px;
  background-color: transparent;
  color: var(--accent-blue);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-env-btn:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-red);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-modal {
  max-width: 400px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}
</style>
