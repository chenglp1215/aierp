<script setup lang="ts">
defineOptions({ name: 'KnowledgeBaseSettings' })

import { ref, onMounted } from 'vue'
import { knowledgeBaseApi } from '../../services/api'

interface KnowledgeBase {
  id?: string
  name: string
  description?: string
  kb_type: string
  document_count?: number
  status: string
  created_at?: string
  vector_dimension?: number
  embedding_model?: string
  similarity_threshold?: number
}

interface Document {
  id?: string
  name: string
  file_size?: number
  status: string
  created_at?: string
}

const collections = ref<KnowledgeBase[]>([])
const documents = ref<Document[]>([])
const loading = ref(false)
const saving = ref(false)
const selectedCollection = ref<KnowledgeBase | null>(null)

const showCollectionModal = ref(false)
const showDocumentModal = ref(false)
const showDeleteConfirm = ref(false)
const editingCollection = ref<KnowledgeBase | null>(null)
const deleteTargetId = ref<string | null>(null)
const deleteType = ref<'collection' | 'document'>('collection')

const collectionForm = ref<Partial<KnowledgeBase>>({
  name: '',
  description: '',
  kb_type: 'vector',
  status: 'active'
})

const documentForm = ref<Partial<Document>>({
  name: ''
})

const kbTypes = [
  { value: 'vector', label: '向量数据库' },
  { value: 'db', label: '关系数据库' },
  { value: 'text', label: '文本库' }
]

const embeddingModels = [
  { value: 'text-embedding-ada-002', label: 'Ada' },
  { value: 'text-embedding-3-small', label: 'Embedding 3 Small' },
  { value: 'text-embedding-3-large', label: 'Embedding 3 Large' }
]

const vectorDimensions = [100, 384, 512, 768, 1024, 1536]

const collectionColumns = [
  { key: 'name', label: '名称' },
  { key: 'kb_type', label: '类型' },
  { key: 'document_count', label: '文档数' },
  { key: 'status', label: '状态' },
  { key: 'created_at', label: '创建时间' }
]

const documentColumns = [
  { key: 'name', label: '文档名称' },
  { key: 'file_size', label: '文件大小' },
  { key: 'status', label: '状态' },
  { key: 'created_at', label: '上传时间' }
]

const loadCollections = async () => {
  loading.value = true
  try {
    const res = await knowledgeBaseApi.list()
    collections.value = res.items || []
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadDocuments = async (collectionId: string) => {
  try {
    const res = await knowledgeBaseApi.getDocuments(collectionId)
    documents.value = res.items || []
  } catch (error) {
    console.error('加载文档列表失败:', error)
  }
}

const selectCollection = (collection: KnowledgeBase) => {
  selectedCollection.value = collection
  loadDocuments(collection.id!)
}

const deselectCollection = () => {
  selectedCollection.value = null
  documents.value = []
}

const resetCollectionForm = () => {
  collectionForm.value = {
    name: '',
    description: '',
    kb_type: 'vector',
    status: 'active'
  }
  editingCollection.value = null
}

const resetDocumentForm = () => {
  documentForm.value = { name: '' }
}

const openCreateCollection = () => {
  resetCollectionForm()
  showCollectionModal.value = true
}

const openEditCollection = (collection: KnowledgeBase) => {
  editingCollection.value = collection
  collectionForm.value = { ...collection }
  showCollectionModal.value = true
}

const confirmDelete = (type: 'collection' | 'document', id: string) => {
  deleteType.value = type
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSaveCollection = async () => {
  if (!collectionForm.value.name?.trim()) {
    window.showToast('请输入知识库名称', 'warning')
    return
  }
  saving.value = true
  try {
    if (editingCollection.value?.id) {
      await knowledgeBaseApi.update(editingCollection.value.id, collectionForm.value)
      window.showToast('知识库更新成功', 'success')
      // 直接更新列表中对应项
      const index = collections.value.findIndex(c => c.id === editingCollection.value!.id)
      if (index !== -1) {
        collections.value[index] = {
          ...collections.value[index],
          ...collectionForm.value
        }
        // 如果正在查看该知识库，同步更新 selectedCollection
        if (selectedCollection.value?.id === editingCollection.value.id) {
          selectedCollection.value = { ...collections.value[index] }
        }
      }
    } else {
      await knowledgeBaseApi.create(collectionForm.value)
      window.showToast('知识库创建成功', 'success')
      loadCollections()
    }
    showCollectionModal.value = false
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    saving.value = false
  }
}

const handleSaveDocument = async () => {
  if (!documentForm.value.name?.trim()) {
    window.showToast('请输入文档名称', 'warning')
    return
  }
  if (!selectedCollection.value?.id) return
  saving.value = true
  try {
    await knowledgeBaseApi.addDocument(selectedCollection.value.id, documentForm.value)
    window.showToast('文档添加成功', 'success')
    // 直接在文档列表中添加新文档
    const newDoc: Document = {
      id: Date.now().toString(), // 临时ID，实际以服务器返回为准
      name: documentForm.value.name,
      status: 'active'
    }
    documents.value = [newDoc, ...documents.value]
    // 更新知识库的文档计数
    const collIndex = collections.value.findIndex(c => c.id === selectedCollection.value!.id)
    if (collIndex !== -1) {
      collections.value[collIndex] = {
        ...collections.value[collIndex],
        document_count: (collections.value[collIndex].document_count || 0) + 1
      }
    }
    showDocumentModal.value = false
    resetDocumentForm()
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
    if (deleteType.value === 'collection') {
      await knowledgeBaseApi.delete(deleteTargetId.value)
      window.showToast('知识库删除成功', 'success')
      // 直接从列表中 filter 移除该知识库
      collections.value = collections.value.filter(c => c.id !== deleteTargetId.value)
      // 如果正在查看该知识库，清空选中状态
      if (selectedCollection.value?.id === deleteTargetId.value) {
        deselectCollection()
      }
    } else if (selectedCollection.value?.id) {
      await knowledgeBaseApi.deleteDocument(selectedCollection.value.id, deleteTargetId.value)
      window.showToast('文档删除成功', 'success')
      // 直接从文档列表中 filter 移除该文档
      documents.value = documents.value.filter(d => d.id !== deleteTargetId.value)
      // 更新知识库的文档计数
      const collIndex = collections.value.findIndex(c => c.id === selectedCollection.value!.id)
      if (collIndex !== -1) {
        collections.value[collIndex] = {
          ...collections.value[collIndex],
          document_count: Math.max(0, (collections.value[collIndex].document_count || 1) - 1)
        }
      }
    }
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  } finally {
    saving.value = false
  }
}

const rebuildIndex = async (collectionId: string) => {
  try {
    await knowledgeBaseApi.rebuildIndex(collectionId)
    window.showToast('索引重建任务已启动', 'success')
  } catch (error: any) {
    window.showToast(error.message || '重建失败', 'error')
  }
}

const formatKbType = (type: string) => {
  const found = kbTypes.find(t => t.value === type)
  return found ? found.label : type
}

const formatStatus = (status: string) => {
  return status === 'active' ? '启用' : '禁用'
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => {
  loadCollections()
})
</script>

<template>
  <div class="kb-settings">
    <section class="settings-section">
      <div class="section-header">
        <h3 class="section-title">知识库集合</h3>
        <button class="primary-btn" @click="openCreateCollection">新建知识库</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in collectionColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 280px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td :colspan="collectionColumns.length + 1" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="collections.length === 0">
              <td :colspan="collectionColumns.length + 1" class="empty-cell">暂无知识库</td>
            </tr>
            <tr v-else v-for="kb in collections" :key="kb.id">
              <td>{{ kb.name }}</td>
              <td>{{ formatKbType(kb.kb_type) }}</td>
              <td>{{ kb.document_count || 0 }}</td>
              <td>
                <span class="status-tag" :class="kb.status">
                  {{ formatStatus(kb.status) }}
                </span>
              </td>
              <td>{{ kb.created_at || '-' }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link" @click="selectCollection(kb)">文档</button>
                  <button class="btn-link" @click="openEditCollection(kb)">编辑</button>
                  <button class="btn-link" @click="rebuildIndex(kb.id!)">重建索引</button>
                  <button class="btn-link danger" @click="confirmDelete('collection', kb.id!)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="settings-section" v-if="selectedCollection">
      <div class="section-header">
        <div class="collection-title">
          <button class="back-btn" @click="deselectCollection">&larr;</button>
          <h3 class="section-title">{{ selectedCollection.name }} - 文档管理</h3>
        </div>
        <button class="primary-btn" @click="showDocumentModal = true">添加文档</button>
      </div>
      <div class="table-section">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in documentColumns" :key="col.key">{{ col.label }}</th>
              <th style="width: 120px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="documents.length === 0">
              <td :colspan="documentColumns.length + 1" class="empty-cell">暂无文档</td>
            </tr>
            <tr v-else v-for="doc in documents" :key="doc.id">
              <td>{{ doc.name }}</td>
              <td>{{ formatFileSize(doc.file_size) }}</td>
              <td>
                <span class="status-tag" :class="doc.status">
                  {{ formatStatus(doc.status) }}
                </span>
              </td>
              <td>{{ doc.created_at || '-' }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-link danger" @click="confirmDelete('document', doc.id!)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="modal-overlay" v-if="showCollectionModal" @click.self="showCollectionModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingCollection ? '编辑知识库' : '新建知识库' }}</h3>
          <button class="modal-close" @click="showCollectionModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称 *</label>
            <input type="text" v-model="collectionForm.name" placeholder="请输入知识库名称" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="collectionForm.description" placeholder="请输入描述" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>知识库类型</label>
              <select v-model="collectionForm.kb_type">
                <option v-for="t in kbTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>向量维度</label>
              <select v-model="collectionForm.vector_dimension">
                <option v-for="d in vectorDimensions" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Embedding 模型</label>
              <select v-model="collectionForm.embedding_model">
                <option v-for="m in embeddingModels" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="collectionForm.status">
                <option value="active">启用</option>
                <option value="inactive">禁用</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>相似度阈值: {{ collectionForm.similarity_threshold || 0.7 }}</label>
            <input type="range" v-model.number="collectionForm.similarity_threshold" min="0" max="1" step="0.05" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCollectionModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveCollection" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showDocumentModal" @click.self="showDocumentModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加文档</h3>
          <button class="modal-close" @click="showDocumentModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>文档名称 *</label>
            <input type="text" v-model="documentForm.name" placeholder="请输入文档名称" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDocumentModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveDocument" :disabled="saving">
            {{ saving ? '添加中...' : '添加' }}
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
          <p>确定要删除{{ deleteType === 'collection' ? '该知识库' : '该文档' }}吗？此操作不可恢复。</p>
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
.kb-settings {
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

.collection-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.back-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
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

.form-group input[type="range"] {
  width: 100%;
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
