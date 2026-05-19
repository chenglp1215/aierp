<script setup lang="ts">
defineOptions({ name: 'AgentSettings' })

import { ref, onMounted } from 'vue'
import { agentApi, skillApi, mcpApi, aiToolsApi } from '../../services/api'

interface Agent {
  id?: number
  name: string
  description?: string
  system_prompt: string
  skill_ids: number[]
  mcp_server_ids: number[]
  tools_range: string[]
  enabled: boolean
  sort_order: number
  created_at?: string
}

interface Skill {
  id: number
  name: string
  category: string
  enabled: boolean
}

interface McpServer {
  id: number
  name: string
  server_type: string
  status: string
}

interface Tool {
  name: string
  cn_name: string
  description: string
  permission_code: string
}

const agents = ref<Agent[]>([])
const skills = ref<Skill[]>([])
const mcpServers = ref<McpServer[]>([])
const availableTools = ref<Tool[]>([])
const loading = ref(false)
const saving = ref(false)

const showAgentModal = ref(false)
const showDeleteConfirm = ref(false)
const editingAgent = ref<Agent | null>(null)
const deleteTargetId = ref<number | null>(null)

const agentForm = ref<Partial<Agent>>({
  name: '',
  description: '',
  system_prompt: '',
  skill_ids: [],
  mcp_server_ids: [],
  tools_range: [],
  enabled: true,
  sort_order: 0
})

const agentColumns = [
  { key: 'name', label: 'Agent 名称' },
  { key: 'description', label: '描述' },
  { key: 'skills', label: '关联技能' },
  { key: 'tools', label: '关联工具' },
  { key: 'mcp', label: '关联MCP' },
  { key: 'enabled', label: '状态' }
]

const loadAgents = async () => {
  loading.value = true
  try {
    const res = await agentApi.list()
    agents.value = res.items || []
  } catch (error) {
    console.error('加载Agent列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadSkills = async () => {
  try {
    const res = await skillApi.list({ page_size: 100 })
    skills.value = (res.items || []).filter((s: Skill) => s.enabled)
  } catch (error) {
    console.error('加载技能列表失败:', error)
  }
}

const loadMcpServers = async () => {
  try {
    const res = await mcpApi.list({ page_size: 100 })
    mcpServers.value = (res.items || []).filter((s: McpServer) => s.status === 'active')
  } catch (error) {
    console.error('加载MCP服务器列表失败:', error)
  }
}

const loadAvailableTools = async () => {
  try {
    const res = await aiToolsApi.listTools()
    availableTools.value = res.items || []
  } catch (error) {
    console.error('加载可用工具列表失败:', error)
  }
}

const resetAgentForm = () => {
  agentForm.value = {
    name: '',
    description: '',
    system_prompt: '',
    skill_ids: [],
    mcp_server_ids: [],
    tools_range: [],
    enabled: true,
    sort_order: 0
  }
  editingAgent.value = null
}

const openCreateAgent = () => {
  resetAgentForm()
  showAgentModal.value = true
}

const openEditAgent = (agent: Agent) => {
  editingAgent.value = agent
  agentForm.value = {
    name: agent.name,
    description: agent.description || '',
    system_prompt: agent.system_prompt || '',
    skill_ids: [...(agent.skill_ids || [])],
    mcp_server_ids: [...(agent.mcp_server_ids || [])],
    tools_range: [...(agent.tools_range || [])],
    enabled: agent.enabled,
    sort_order: agent.sort_order || 0
  }
  showAgentModal.value = true
}

const confirmDelete = (id: number) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSaveAgent = async () => {
  if (!agentForm.value.name?.trim()) {
    window.showToast('请输入Agent名称', 'warning')
    return
  }
  saving.value = true
  try {
    if (editingAgent.value?.id) {
      await agentApi.update(editingAgent.value.id, agentForm.value)
      window.showToast('Agent更新成功', 'success')
      const index = agents.value.findIndex(a => a.id === editingAgent.value!.id)
      if (index !== -1) {
        agents.value[index] = {
          ...agents.value[index],
          ...agentForm.value
        }
      }
    } else {
      await agentApi.create(agentForm.value)
      window.showToast('Agent创建成功', 'success')
      loadAgents()
    }
    showAgentModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  saving.value = true
  try {
    await agentApi.delete(deleteTargetId.value)
    window.showToast('Agent删除成功', 'success')
    agents.value = agents.value.filter(a => a.id !== deleteTargetId.value)
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    saving.value = false
  }
}

const getSkillNames = (agent: Agent) => {
  if (!agent.skill_ids?.length) return '-'
  return agent.skill_ids
    .map(id => skills.value.find(s => s.id === id)?.name || id)
    .join(', ')
}
const getMcpNames = (agent: Agent) => {
  if (!agent.mcp_server_ids?.length) return '-'
  return agent.mcp_server_ids
    .map(id => mcpServers.value.find(m => m.id === id)?.name || id)
    .join(', ')
}

const formatEnabled = (enabled: boolean) => enabled ? '启用' : '禁用'

const isMultiSelected = (arr: string[], id: string) => arr.includes(id)

const toggleSelection = (arr: string[], id: string) => {
  const index = arr.indexOf(id)
  if (index === -1) {
    arr.push(id)
  } else {
    arr.splice(index, 1)
  }
}

onMounted(() => {
  loadAgents()
  loadSkills()
  loadMcpServers()
  loadAvailableTools()
})
</script>

<template>
  <div class="agent-settings">
    <section class="settings-section">
      <div class="section-header">
        <h3 class="section-title">Agent 列表</h3>
        <button class="primary-btn" @click="openCreateAgent">添加 Agent</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in agentColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 200px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td :colspan="agentColumns.length + 1" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="agents.length === 0">
              <td :colspan="agentColumns.length + 1" class="empty-cell">暂无 Agent</td>
            </tr>
            <tr v-else v-for="agent in agents" :key="agent.id">
              <td>{{ agent.name }}</td>
              <td class="desc-cell" :title="agent.description">{{ agent.description || '-' }}</td>
              <td>{{ getSkillNames(agent) }}</td>
              <td class="tools-cell">
                <span v-if="!agent.tools_range?.length">-</span>
                <span v-else v-for="name in agent.tools_range" :key="name" class="tool-tag">
                  {{ availableTools.find(t => t.name === name)?.cn_name || name }}
                </span>
              </td>
              <td>{{ getMcpNames(agent) }}</td>
              <td>
                <span class="status-tag" :class="{ active: agent.enabled }">
                  {{ formatEnabled(agent.enabled) }}
                </span>
              </td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link" @click="openEditAgent(agent)">编辑</button>
                  <button class="btn-link danger" @click="confirmDelete(agent.id!)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="modal-overlay" v-if="showAgentModal">
      <div class="modal agent-modal">
        <div class="modal-header">
          <h3>{{ editingAgent ? '编辑 Agent' : '添加 Agent' }}</h3>
          <button class="modal-close" @click="showAgentModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Agent 名称 *</label>
            <input type="text" v-model="agentForm.name" placeholder="请输入 Agent 名称" autocomplete="off" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input type="text" v-model="agentForm.description" placeholder="请输入描述" />
          </div>
          <div class="form-group">
            <label>系统提示词</label>
            <textarea v-model="agentForm.system_prompt" placeholder="请输入系统提示词，用于定义 Agent 的行为和能力" rows="6"></textarea>
          </div>
          <div class="form-group">
            <label>关联 Skills</label>
            <div class="checkbox-grid" v-if="skills.length > 0">
              <label
                v-for="skill in skills"
                :key="skill.id"
                class="checkbox-item"
                :class="{ selected: isMultiSelected(agentForm.skill_ids || [], skill.id) }"
              >
                <input
                  type="checkbox"
                  :checked="isMultiSelected(agentForm.skill_ids || [], skill.id)"
                  @change="toggleSelection(agentForm.skill_ids || [], skill.id)"
                />
                <span>{{ skill.name }}</span>
              </label>
            </div>
            <div v-else class="empty-hint">暂无可用的 Skills</div>
          </div>
          <div class="form-group">
            <label>关联 MCP 服务器</label>
            <div class="checkbox-grid" v-if="mcpServers.length > 0">
              <label
                v-for="mcp in mcpServers"
                :key="mcp.id"
                class="checkbox-item"
                :class="{ selected: isMultiSelected(agentForm.mcp_server_ids || [], mcp.id) }"
              >
                <input
                  type="checkbox"
                  :checked="isMultiSelected(agentForm.mcp_server_ids || [], mcp.id)"
                  @change="toggleSelection(agentForm.mcp_server_ids || [], mcp.id)"
                />
                <span>{{ mcp.name }}</span>
              </label>
            </div>
            <div v-else class="empty-hint">暂无可用的 MCP 服务器</div>
          </div>
          <div class="form-group">
            <label>工具范围</label>
            <div class="checkbox-grid" v-if="availableTools.length > 0">
              <label
                v-for="tool in availableTools"
                :key="tool.name"
                class="checkbox-item"
                :class="{ selected: isMultiSelected(agentForm.tools_range || [], tool.name) }"
                :title="tool.description"
              >
                <input
                  type="checkbox"
                  :checked="isMultiSelected(agentForm.tools_range || [], tool.name)"
                  @change="toggleSelection(agentForm.tools_range || [], tool.name)"
                />
                <span>{{ tool.cn_name || tool.name }}</span>
              </label>
            </div>
            <div v-else class="empty-hint">暂无可用的工具</div>
            <div class="field-hint">留空表示不使用任何工具</div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>排序权重</label>
              <input type="number" v-model.number="agentForm.sort_order" min="0" placeholder="数字越小越靠前" />
            </div>
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="agentForm.enabled" />
                <span>启用 Agent</span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAgentModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveAgent" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
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
          <p>确定要删除该 Agent 吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="saving">
            {{ saving ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-settings {
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

.desc-cell {
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

.status-tag:not(.active) {
  background-color: rgba(128, 128, 128, 0.1);
  color: var(--text-muted);
}

.tools-cell {
  max-width: 200px;
}

.tool-tag {
  display: inline-block;
  padding: 2px 8px;
  margin: 2px;
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--accent-blue);
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
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
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group input[type="number"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group input[type="number"]::-webkit-inner-spin-button,
.form-group input[type="number"]::-webkit-outer-spin-button {
  opacity: 1;
  height: 28px;
}

.form-group textarea {
  resize: vertical;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  max-height: 150px;
  overflow-y: auto;
  padding: 8px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 13px;
  color: var(--text-primary);
  border: 1px solid transparent;
}

.checkbox-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.checkbox-item.selected {
  background-color: rgba(0, 120, 212, 0.1);
  border-color: var(--accent-blue);
}

.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent-blue);
}

.empty-hint {
  padding: 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.field-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
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
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.agent-modal {
  max-width: 700px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  background-color: var(--bg-card);
  z-index: 1;
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
