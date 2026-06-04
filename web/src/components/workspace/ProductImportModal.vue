<script setup lang="ts">
import { ref, onUnmounted, computed, onMounted } from 'vue'
import { importTaskApi } from '../../services/api'

const emit = defineEmits<{
  close: []
  success: []
}>()

// Tab 切换
const activeTab = ref<'upload' | 'history'>('upload')

// 文件上传相关
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 任务列表相关
const tasks = ref<any[]>([])
const loadingTasks = ref(false)
const pollingTimer = ref<number | null>(null)

const statusTextMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const statusClassMap: Record<string, string> = {
  pending: 'status-pending',
  processing: 'status-processing',
  completed: 'status-completed',
  failed: 'status-failed',
  cancelled: 'status-cancelled',
}

// 加载任务列表
const loadTasks = async () => {
  loadingTasks.value = true
  try {
    const result = await importTaskApi.list({ page: 1, page_size: 10 })
    tasks.value = result.items || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  } finally {
    loadingTasks.value = false
  }
}

// 开始轮询（有处理中的任务时）
const startPolling = () => {
  stopPolling()
  pollingTimer.value = window.setInterval(() => {
    loadTasks()
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

// 检查是否有进行中的任务
const hasProcessingTasks = computed(() => {
  return tasks.value.some(t => t.status === 'pending' || t.status === 'processing')
})

// 文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    if (!file.name.endsWith('.xlsx')) {
      window.showToast('仅支持 .xlsx 格式文件', 'error')
      return
    }
    selectedFile.value = file
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const file = event.dataTransfer?.files[0]
  if (file) {
    if (!file.name.endsWith('.xlsx')) {
      window.showToast('仅支持 .xlsx 格式文件', 'error')
      return
    }
    selectedFile.value = file
  }
}

// 上传文件
const handleUpload = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  try {
    await importTaskApi.create(selectedFile.value)
    window.showToast('导入任务已创建', 'success')
    selectedFile.value = null

    // 切换到历史记录 tab
    activeTab.value = 'history'

    // 刷新任务列表
    await loadTasks()

    // 开始轮询
    startPolling()

    emit('success')
  } catch (error: any) {
    window.showToast(error.message || '上传失败', 'error')
  } finally {
    uploading.value = false
  }
}

// 下载错误文件
const downloadErrors = async (taskId: number) => {
  try {
    await importTaskApi.downloadError(taskId)
  } catch (error: any) {
    window.showToast(error.message || '下载失败', 'error')
  }
}

// 下载模板
const downloadTemplate = () => {
  const templateData = [
    ['产品编号', '产品名称', '品牌名称', '分类名称', '规格编号', '包装', '销售规格', '价格', 'CAS号', '是否有效'],
    ['PROD001', '示例产品', '示例品牌', '试剂', 'SPEC001', '100g/罐', '100g*24罐/箱', '99.00', '1234-56-7', '是'],
  ]
  const csvContent = templateData.map(row => row.join(',')).join('\n')
  const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '产品导入模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const openFileSelect = () => {
  fileInput.value?.click()
}

const handleClose = () => {
  stopPolling()
  emit('close')
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTasks()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="modal-overlay" @click.self="handleClose">
    <div class="modal import-modal">
      <div class="modal-header">
        <h3>批量导入产品</h3>
        <button class="modal-close" @click="handleClose">×</button>
      </div>

      <!-- Tab 切换 -->
      <div class="tab-header">
        <button
          :class="['tab-btn', { active: activeTab === 'upload' }]"
          @click="activeTab = 'upload'"
        >
          上传文件
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'history' }]"
          @click="activeTab = 'history'; loadTasks()"
        >
          导入记录
          <span v-if="hasProcessingTasks" class="processing-dot"></span>
        </button>
      </div>

      <div class="modal-body">
        <!-- 上传文件 Tab -->
        <div v-if="activeTab === 'upload'" class="upload-section">
          <div
            class="upload-area"
            @drop="handleDrop"
            @dragover.prevent
            @dragenter.prevent
          >
            <input
              type="file"
              accept=".xlsx"
              @change="handleFileSelect"
              hidden
              ref="fileInput"
            />
            <div v-if="!selectedFile" class="upload-placeholder" @click="openFileSelect">
              <div class="upload-icon">📄</div>
              <div class="upload-text">点击或拖拽上传 Excel 文件</div>
              <div class="upload-hint">仅支持 .xlsx 格式</div>
            </div>
            <div v-else class="file-selected" @click="openFileSelect">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</div>
            </div>
          </div>

          <div class="template-link">
            <button class="btn-link" @click="downloadTemplate">下载导入模板</button>
          </div>

          <button
            class="btn-primary btn-full"
            @click="handleUpload"
            :disabled="!selectedFile || uploading"
          >
            {{ uploading ? '上传中...' : '开始导入' }}
          </button>
        </div>

        <!-- 导入记录 Tab -->
        <div v-else class="history-section">
          <div v-if="loadingTasks && tasks.length === 0" class="empty-state">
            加载中...
          </div>

          <div v-else-if="tasks.length === 0" class="empty-state">
            暂无导入记录
          </div>

          <div v-else class="task-list">
            <div v-for="task in tasks" :key="task.id" class="task-item">
              <div class="task-header">
                <span class="task-id">#{{ task.id }}</span>
                <span :class="['status-tag', statusClassMap[task.status]]">
                  {{ statusTextMap[task.status] || task.status }}
                </span>
              </div>

              <div class="task-progress">
                <div class="progress-bar-container">
                  <div class="progress-bar" :style="{ width: task.progress_percent + '%' }"></div>
                </div>
                <span class="progress-text">{{ task.progress_percent }}%</span>
              </div>

              <div class="task-stats">
                <span>总数: {{ task.total_rows }}</span>
                <span class="success">新建: {{ task.success_count }}</span>
                <span class="update">更新: {{ task.update_count }}</span>
                <span v-if="task.error_count > 0" class="error">错误: {{ task.error_count }}</span>
              </div>

              <div class="task-footer">
                <span class="task-time">{{ formatDate(task.created_at) }}</span>
                <button
                  v-if="task.status === 'completed' && task.error_count > 0"
                  class="btn-link"
                  @click="downloadErrors(task.id)"
                >
                  下载错误
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="handleClose">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-modal {
  max-width: 560px;
}

.tab-header {
  display: flex;
  border-bottom: 1px solid var(--color-hairline);
  padding: 0 20px;
}

.tab-btn {
  padding: 12px 20px;
  background: none;
  border: none;
  font-size: 14px;
  color: var(--color-muted);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-ink);
}

.tab-btn.active {
  color: var(--color-interactive);
  font-weight: 500;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--color-interactive);
}

.processing-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-interactive);
  margin-left: 6px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-area {
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-area:hover {
  border-color: var(--color-interactive);
  background-color: rgba(0, 120, 212, 0.02);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 48px;
}

.upload-text {
  font-size: 14px;
  color: var(--color-ink);
}

.upload-hint {
  font-size: 12px;
  color: var(--color-muted);
}

.file-selected {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  color: var(--color-ink);
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: var(--color-muted);
}

.template-link {
  text-align: center;
}

.history-section {
  min-height: 200px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-muted);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  padding: 12px;
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-sm);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-id {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-ink);
}

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-pending {
  background-color: var(--color-neutral-bg);
  color: var(--color-muted);
}

.status-processing {
  background-color: var(--color-info-bg);
  color: var(--color-interactive);
}

.status-completed {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-failed {
  background-color: var(--color-danger-bg);
  color: var(--color-danger);
}

.status-cancelled {
  background-color: var(--color-neutral-bg);
  color: var(--color-muted);
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.progress-bar-container {
  flex: 1;
  height: 6px;
  background-color: var(--color-canvas);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: var(--color-interactive);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--color-muted);
  min-width: 40px;
  text-align: right;
}

.task-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--color-muted);
}

.task-stats .success {
  color: var(--color-success);
}

.task-stats .update {
  color: var(--color-interactive);
}

.task-stats .error {
  color: var(--color-danger);
  font-weight: 500;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-hairline);
}

.task-time {
  font-size: 11px;
  color: var(--color-muted);
}

.btn-full {
  width: 100%;
}

/* 全局样式 */
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
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-hover);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--color-hairline);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  color: var(--color-muted);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background-color: rgba(0, 0, 0, 0.06);
  color: var(--color-ink);
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
  border-top: 1px solid var(--color-hairline);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 14px;
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}

.btn-primary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-interactive-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.btn-link:hover {
  background-color: var(--color-info-bg);
}
</style>
