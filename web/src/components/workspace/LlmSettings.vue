<script setup lang="ts">
defineOptions({ name: 'LlmSettings' })

import { ref, onMounted } from 'vue'
import { llmApi } from '../../services/api'

interface LlmModel {
  id?: string
  name: string
  model_type: string
  status: string
}

interface LlmConfig {
  default_model: string
  api_base_url: string
  api_key: string
  streaming: boolean
  timeout: number
  retry_count: number
}

const models = ref<LlmModel[]>([])
const loading = ref(false)
const saving = ref(false)
const testingModelId = ref<string | null>(null)

const config = ref<LlmConfig>({
  default_model: '',
  api_base_url: '',
  api_key: '',
  streaming: true,
  timeout: 60,
  retry_count: 3
})

const showModelModal = ref(false)
const showDeleteConfirm = ref(false)
const editingModel = ref<LlmModel | null>(null)
const deleteTargetId = ref<string | null>(null)

const modelForm = ref<Partial<LlmModel>>({
  name: '',
  model_type: 'openai',
  status: 'active'
})

const modelTypes = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'custom', label: '自定义' }
]

const modelColumns = [
  { key: 'name', label: '模型名称' },
  { key: 'model_type', label: '模型类型' },
  { key: 'status', label: '状态' }
]

const loadModels = async () => {
  loading.value = true
  try {
    const res = await llmApi.list()
    models.value = res.items || []
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadConfig = async () => {
  try {
    const res = await llmApi.getConfig()
    if (res) {
      config.value = { ...config.value, ...res }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await llmApi.updateConfig(config.value)
    alert('配置保存成功')
  } catch (error: any) {
    alert(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const testConnection = async (modelId: string) => {
  testingModelId.value = modelId
  try {
    await llmApi.testConnection(modelId)
    alert('连接测试成功')
  } catch (error: any) {
    alert(error.message || '连接测试失败')
  } finally {
    testingModelId.value = null
  }
}

const resetModelForm = () => {
  modelForm.value = {
    name: '',
    model_type: 'openai',
    status: 'active'
  }
  editingModel.value = null
}

const openCreateModel = () => {
  resetModelForm()
  showModelModal.value = true
}

const openEditModel = (model: LlmModel) => {
  editingModel.value = model
  modelForm.value = { ...model }
  showModelModal.value = true
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSaveModel = async () => {
  if (!modelForm.value.name?.trim()) {
    alert('请输入模型名称')
    return
  }
  saving.value = true
  try {
    if (editingModel.value?.id) {
      await llmApi.update(editingModel.value.id, modelForm.value)
      alert('模型更新成功')
    } else {
      await llmApi.create(modelForm.value)
      alert('模型创建成功')
    }
    showModelModal.value = false
    loadModels()
  } catch (error: any) {
    alert(error.message || '操作失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  saving.value = true
  try {
    await llmApi.delete(deleteTargetId.value)
    alert('模型删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadModels()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    saving.value = false
  }
}

const formatModelType = (type: string) => {
  const found = modelTypes.find(m => m.value === type)
  return found ? found.label : type
}

const formatStatus = (status: string) => {
  return status === 'active' ? '启用' : '禁用'
}

onMounted(() => {
  loadModels()
  loadConfig()
})
</script>

<template>
  <div class="llm-settings">
    <section class="settings-section">
      <h3 class="section-title">LLM 默认配置</h3>
      <div class="config-form">
        <div class="form-row">
          <div class="form-group">
            <label>默认模型</label>
            <input type="text" v-model="config.default_model" placeholder="请输入模型名称，如 gpt-4" autocomplete="off" />
          </div>
          <div class="form-group">
            <label>API Base URL</label>
            <div style="display: none"><input type="text" name="username" tabindex="-1" autocomplete="off" /></div>
            <input type="text" v-model="config.api_base_url" placeholder="https://api.openai.com/v1" autocomplete="off" />
          </div>
        </div>
        <div class="form-group">
          <label>API Key</label>
          <div style="display: none"><input type="password" name="password" tabindex="-1" autocomplete="off" /></div>
          <input type="password" v-model="config.api_key" placeholder="sk-..." autocomplete="new-password" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Timeout (秒)</label>
            <input type="number" v-model.number="config.timeout" min="10" max="300" />
          </div>
          <div class="form-group">
            <label>Retry Count</label>
            <input type="number" v-model.number="config.retry_count" min="1" max="10" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-primary" @click="saveConfig" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </section>

    <section class="settings-section">
      <div class="section-header">
        <h3 class="section-title">模型列表</h3>
        <button class="primary-btn" @click="openCreateModel">添加模型</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in modelColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 200px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td :colspan="modelColumns.length + 1" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="models.length === 0">
              <td :colspan="modelColumns.length + 1" class="empty-cell">暂无模型</td>
            </tr>
            <tr v-else v-for="model in models" :key="model.id">
              <td>{{ model.name }}</td>
              <td>{{ formatModelType(model.model_type) }}</td>
              <td>
                <span class="status-tag" :class="model.status">
                  {{ formatStatus(model.status) }}
                </span>
              </td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link" @click="openEditModel(model)">编辑</button>
                  <button class="btn-link" @click="testConnection(model.id!)" :disabled="testingModelId === model.id">
                    {{ testingModelId === model.id ? '测试中...' : '测试' }}
                  </button>
                  <button class="btn-link danger" @click="confirmDelete(model.id!)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="modal-overlay" v-if="showModelModal" @click.self="showModelModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingModel ? '编辑模型' : '添加模型' }}</h3>
          <button class="modal-close" @click="showModelModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模型名称 *</label>
            <input type="text" v-model="modelForm.name" placeholder="请输入模型名称" autocomplete="off" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>模型类型</label>
              <select v-model="modelForm.model_type">
                <option v-for="t in modelTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="modelForm.status">
                <option value="active">启用</option>
                <option value="inactive">禁用</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showModelModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveModel" :disabled="saving">
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
          <p>确定要删除该模型吗？此操作不可恢复。</p>
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
.llm-settings {
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
  margin: 0 0 16px 0;
}

.section-header .section-title {
  margin: 0;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
.form-group input[type="password"],
.form-group input[type="number"],
.form-group select {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-group input[type="range"] {
  width: 100%;
  cursor: pointer;
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

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
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
  max-width: 500px;
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

.confirm-modal {
  max-width: 400px;
}

.confirm-modal .modal-body p {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}
</style>
