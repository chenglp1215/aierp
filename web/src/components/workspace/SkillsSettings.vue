<script setup lang="ts">
defineOptions({ name: 'SkillsSettings' })

import { ref, onMounted } from 'vue'
import { skillApi, uploadApi } from '../../services/api'

interface Skill {
  id?: string
  name: string
  description?: string
  category: string
  enabled: boolean
  priority: number
  permission_code?: string
  parameters?: any
  content?: string
  markdown?: string
  config?: any
  created_at?: string
}

const skills = ref<Skill[]>([])
const loading = ref(false)
const saving = ref(false)
const togglingId = ref<string | null>(null)

const showSkillModal = ref(false)
const showDeleteConfirm = ref(false)
const editingSkill = ref<Skill | null>(null)
const deleteTargetId = ref<string | null>(null)

const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

const skillForm = ref<Partial<Skill>>({
  name: '',
  description: '',
  category: 'conversation',
  enabled: true,
  priority: 5,
  permission_code: '',
  content: ''
})

const skillCategories = [
  { value: 'conversation', label: '对话' },
  { value: 'tool', label: '工具' },
  { value: 'workflow', label: '工作流' },
  { value: 'analysis', label: '分析' }
]

const skillColumns = [
  { key: 'name', label: '技能名称' },
  { key: 'description', label: '描述' },
  { key: 'category', label: '分类' },
  { key: 'enabled', label: '状态' },
  { key: 'priority', label: '优先级' },
  { key: 'created_at', label: '创建时间' }
]

const loadSkills = async () => {
  loading.value = true
  try {
    const res = await skillApi.list()
    skills.value = res.items || []
  } catch (error) {
    console.error('加载技能列表失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleSkill = async (skill: Skill) => {
  togglingId.value = skill.id!
  try {
    if (skill.enabled) {
      await skillApi.disable(skill.id!)
    } else {
      await skillApi.enable(skill.id!)
    }
    const index = skills.value.findIndex(s => s.id === skill.id)
    if (index !== -1) {
      skills.value[index] = { ...skills.value[index], enabled: !skill.enabled }
    }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    togglingId.value = null
  }
}

const parseFrontMatter = (content: string): Record<string, any> => {
  const result: Record<string, any> = {}
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/)
  if (match) {
    const frontMatter = match[1]
    result.content = match[2] || ''
    result.markdown = content
    frontMatter.split('\n').forEach(line => {
      const colonIndex = line.indexOf(':')
      if (colonIndex > 0) {
        const key = line.substring(0, colonIndex).trim()
        let value = line.substring(colonIndex + 1).trim()
        if (value === 'true') value = true
        else if (value === 'false') value = false
        else if (!isNaN(Number(value))) value = Number(value)
        result[key] = value
      }
    })
  } else {
    result.content = content
    result.markdown = content
  }
  return result
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    const file = input.files[0]
    if (!file.name.endsWith('.md')) {
      window.showToast('请选择 Markdown 文件 (.md)', 'warning')
      return
    }
    selectedFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      const parsed = parseFrontMatter(content)
      skillForm.value.name = parsed.name || file.name.replace('.md', '')
      skillForm.value.description = parsed.description || ''
      skillForm.value.priority = parsed.priority || 5
      skillForm.value.enabled = parsed.enabled !== false
      skillForm.value.content = parsed.content || content
      skillForm.value.markdown = parsed.markdown || content
    }
    reader.readAsText(file)
  }
}

const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

const resetSkillForm = () => {
  skillForm.value = {
    name: '',
    description: '',
    category: 'conversation',
    enabled: true,
    priority: 5,
    permission_code: '',
    content: ''
  }
  selectedFile.value = null
  editingSkill.value = null
}

const openCreateSkill = () => {
  resetSkillForm()
  showSkillModal.value = true
}

const openEditSkill = (skill: Skill) => {
  editingSkill.value = skill
  skillForm.value = {
    ...skill
  }
  showSkillModal.value = true
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSaveSkill = async () => {
  if (!skillForm.value.name?.trim()) {
    window.showToast('请输入技能名称或上传 Markdown 文件', 'warning')
    return
  }
  saving.value = true
  try {
    const data = { ...skillForm.value }
    if (editingSkill.value?.id) {
      await skillApi.update(editingSkill.value.id, data)
      window.showToast('技能更新成功', 'success')
      const index = skills.value.findIndex(s => s.id === editingSkill.value!.id)
      if (index !== -1) {
        skills.value[index] = { ...skills.value[index], ...data }
      }
    } else {
      await skillApi.create(data)
      window.showToast('技能创建成功', 'success')
      loadSkills()
    }
    showSkillModal.value = false
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
    await skillApi.delete(deleteTargetId.value)
    window.showToast('技能删除成功', 'success')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadSkills()
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    saving.value = false
  }
}

const formatCategory = (category: string) => {
  const found = skillCategories.find(c => c.value === category)
  return found ? found.label : category
}

const formatEnabled = (enabled: boolean) => {
  return enabled ? '启用' : '禁用'
}

onMounted(() => {
  loadSkills()
})
</script>

<template>
  <div class="skills-settings">
    <section class="settings-section">
      <div class="section-header">
        <h3 class="section-title">Skills 列表</h3>
        <button class="primary-btn" @click="openCreateSkill">添加技能</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in skillColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 240px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td :colspan="skillColumns.length + 1" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="skills.length === 0">
              <td :colspan="skillColumns.length + 1" class="empty-cell">暂无技能</td>
            </tr>
            <tr v-else v-for="skill in skills" :key="skill.id">
              <td>{{ skill.name }}</td>
              <td class="desc-cell" :title="skill.description">{{ skill.description || '-' }}</td>
              <td>{{ formatCategory(skill.category) }}</td>
              <td>
                <span class="status-tag" :class="{ active: skill.enabled }">
                  {{ formatEnabled(skill.enabled) }}
                </span>
              </td>
              <td>{{ skill.priority }}</td>
              <td>{{ skill.created_at || '-' }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link" @click="toggleSkill(skill)" :disabled="togglingId === skill.id">
                    {{ togglingId === skill.id ? '切换中...' : (skill.enabled ? '禁用' : '启用') }}
                  </button>
                  <button class="btn-link" @click="openEditSkill(skill)">编辑</button>
                  <button class="btn-link danger" @click="confirmDelete(skill.id!)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="modal-overlay" v-if="showSkillModal" @click.self="showSkillModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingSkill ? '编辑技能' : '添加技能' }}</h3>
          <button class="modal-close" @click="showSkillModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>上传 Markdown 文件</label>
            <div class="file-upload-area">
              <input
                type="file"
                ref="fileInputRef"
                accept=".md"
                @change="handleFileSelect"
                style="display: none"
              />
              <button class="upload-btn" @click="triggerFileSelect">
                {{ selectedFile ? selectedFile.name : '选择文件' }}
              </button>
              <span class="file-hint">支持 .md 格式，文件内的 name/description/priority 会被自动解析</span>
            </div>
          </div>
          <div class="form-divider">
            <span>或手动填写</span>
          </div>
          <div class="form-group">
            <label>技能名称 *</label>
            <input type="text" v-model="skillForm.name" placeholder="请输入技能名称" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="skillForm.description" placeholder="请输入描述" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>分类</label>
              <select v-model="skillForm.category">
                <option v-for="c in skillCategories" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级 (1-10)</label>
              <input type="number" v-model.number="skillForm.priority" min="1" max="10" />
            </div>
          </div>
          <div class="form-group">
            <label>技能内容</label>
            <textarea v-model="skillForm.content" placeholder="技能的具体内容（当Agent调用此技能时返回的响应）" rows="6"></textarea>
          </div>
          <div class="form-group">
            <label>权限码</label>
            <input type="text" v-model="skillForm.permission_code" placeholder="留空则所有用户可用" />
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="skillForm.enabled" />
              <span>启用技能</span>
            </label>
          </div>
          <div class="form-group">
            <label>技能配置 (JSON)</label>
            <textarea v-model="skillForm.config" placeholder='{"key": "value"}' rows="4"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showSkillModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveSkill" :disabled="saving">
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
          <p>确定要删除该技能吗？此操作不可恢复。</p>
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
.skills-settings {
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

.file-upload-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-btn {
  padding: 10px 16px;
  background-color: var(--bg-secondary);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  text-align: center;
  transition: all var(--transition-fast);
}

.upload-btn:hover {
  border-color: var(--accent-blue);
  background-color: rgba(0, 120, 212, 0.05);
}

.file-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.form-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--text-muted);
  font-size: 12px;
}

.form-divider::before,
.form-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background-color: var(--border-color);
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
