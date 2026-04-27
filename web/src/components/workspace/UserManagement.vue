<script setup lang="ts">
defineOptions({ name: 'UserManagement' })

import { ref, onMounted } from 'vue'
import { authApi, roleApi } from '../../services/api'
import { usePermission, BUTTON_PERMISSION_MAP } from '../../hooks'

interface User {
  id: string
  username: string
  email: string
  phone?: string
  full_name?: string
  role_ids?: string[]
  role_names?: string[]
  status: string
  created_at?: string
}

const { hasPermission } = usePermission()

interface Role {
  id: string
  name: string
  code: string
}

const loading = ref(false)
const users = ref<User[]>([])
const roles = ref<Role[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const showModal = ref(false)
const showDeleteConfirm = ref(false)
const showResetPwdModal = ref(false)
const editingUser = ref<User | null>(null)
const deleteTargetId = ref<string | null>(null)
const resetPwdTarget = ref<{ id: string; username: string } | null>(null)
const newPassword = ref('')
const formLoading = ref(false)
const deleteLoading = ref(false)
const resetPwdLoading = ref(false)

const userForm = ref({
  username: '',
  email: '',
  phone: '',
  full_name: '',
  password: '',
  role_ids: [] as string[]
})

const columns = [
  { key: 'username', label: '用户名' },
  { key: 'email', label: '邮箱' },
  { key: 'phone', label: '手机' },
  { key: 'role_names', label: '角色' },
  { key: 'created_at', label: '创建时间' }
]

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await authApi.listUsers({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined
    })
    users.value = (res.items || []).map((user: any) => ({
      ...user,
      role_ids: (user.roles || []).map((r: any) => r.id || r),
      role_names: (user.roles || []).map((r: any) => r.name || r.code || r)
    }))
    total.value = res.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const res = await roleApi.list({ page_size: 100 })
    roles.value = res.items || []
  } catch (error) {
    console.error('加载角色列表失败:', error)
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadUsers()
}

const handleSearch = () => {
  page.value = 1
  loadUsers()
}

const clearKeyword = () => {
  keyword.value = ''
  handleSearch()
}

const resetForm = () => {
  userForm.value = {
    username: '',
    email: '',
    phone: '',
    full_name: '',
    password: '',
    role_ids: []
  }
  editingUser.value = null
}

const openEdit = (user: User) => {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    email: user.email,
    phone: user.phone || '',
    full_name: (user as any).full_name || '',
    password: '',
    role_ids: user.role_ids || []
  }
  showModal.value = true
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleSave = async () => {
  if (!userForm.value.username?.trim()) {
    alert('请输入用户名')
    return
  }
  if (userForm.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userForm.value.email)) {
    alert('请输入有效的邮箱地址')
    return
  }
  if (!editingUser.value && !userForm.value.password?.trim()) {
    alert('请输入密码')
    return
  }
  if (userForm.value.password && userForm.value.password.length < 6) {
    alert('密码长度不能少于6位')
    return
  }

  formLoading.value = true
  try {
    if (editingUser.value) {
      const data: any = {
        email: userForm.value.email || undefined,
        phone: userForm.value.phone || undefined,
        full_name: userForm.value.full_name || undefined,
        role_ids: userForm.value.role_ids.length > 0 ? userForm.value.role_ids : undefined
      }
      if (userForm.value.password) {
        data.new_password = userForm.value.password
      }
      await authApi.updateUser(editingUser.value.id, data)
      alert('用户更新成功')
    } else {
      const data: any = {
        username: userForm.value.username,
        password: userForm.value.password,
        email: userForm.value.email || undefined,
        phone: userForm.value.phone || undefined,
        full_name: userForm.value.full_name || undefined,
        role_ids: userForm.value.role_ids.length > 0 ? userForm.value.role_ids : undefined
      }
      await authApi.createUser(data)
      alert('用户创建成功')
    }
    showModal.value = false
    loadUsers()
  } catch (error: any) {
    alert(error.message || '操作失败')
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return

  deleteLoading.value = true
  try {
    await authApi.deleteUser(deleteTargetId.value)
    alert('用户删除成功')
    showDeleteConfirm.value = false
    deleteTargetId.value = null
    loadUsers()
  } catch (error: any) {
    alert(error.message || '删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const openResetPwd = (user: User) => {
  resetPwdTarget.value = { id: user.id, username: user.username }
  newPassword.value = ''
  showResetPwdModal.value = true
}

const handleResetPwd = async () => {
  if (!resetPwdTarget.value || !newPassword.value.trim()) {
    alert('请输入新密码')
    return
  }
  if (newPassword.value.length < 6) {
    alert('密码长度不能少于6位')
    return
  }

  resetPwdLoading.value = true
  try {
    await authApi.resetPassword(resetPwdTarget.value.id, newPassword.value)
    alert('密码重置成功')
    showResetPwdModal.value = false
    resetPwdTarget.value = null
    newPassword.value = ''
  } catch (error: any) {
    alert(error.message || '密码重置失败')
  } finally {
    resetPwdLoading.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<template>
  <div class="user-management">
    <div class="workspace-header">
      <h2 class="workspace-title">用户管理</h2>
      <button class="primary-btn" @click="resetForm(); showModal = true">新建用户</button>
    </div>

    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item search-filter">
          <input
            type="text"
            class="filter-input"
            placeholder="搜索用户名、邮箱..."
            v-model="keyword"
            autocomplete="off"
            @keyup.enter="handleSearch"
          />
        </div>
        <button class="filter-btn" @click="handleSearch">搜索</button>
        <button class="filter-btn reset-btn" @click="clearKeyword" v-if="keyword">重置</button>
      </div>
    </div>

    <div class="table-section">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key">{{ col.label }}</th>
            <th style="width: 180px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td :colspan="columns.length + 1" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.phone || '-' }}</td>
            <td>{{ user.role_names?.join(', ') || '-' }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button v-permission="'user.edit'" class="btn-link" @click="openEdit(user)">编辑</button>
                <button v-permission="'user.reset-password'" class="btn-link" @click="openResetPwd(user)">重置密码</button>
                <button v-permission="'user.delete'" class="btn-link danger" @click="confirmDelete(user.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="total > 0">
      <span class="pagination-info">共 {{ total }} 条</span>
      <button class="pagination-btn" :disabled="page === 1" @click="handlePageChange(page - 1)">上一页</button>
      <span class="pagination-current">第 {{ page }} 页</span>
      <button class="pagination-btn" :disabled="users.length < pageSize" @click="handlePageChange(page + 1)">下一页</button>
    </div>

    <div class="modal-overlay" v-if="showModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingUser ? '编辑用户' : '新建用户' }}</h3>
          <button class="modal-close" @click="showModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>用户名 *</label>
              <input type="text" v-model="userForm.username" placeholder="请输入用户名" autocomplete="off" />
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="email" v-model="userForm.email" placeholder="请输入邮箱（选填）" autocomplete="off" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>手机</label>
              <input type="text" v-model="userForm.phone" placeholder="请输入手机号" autocomplete="off" />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input type="text" v-model="userForm.full_name" placeholder="请输入姓名" autocomplete="off" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>角色</label>
              <select v-model="userForm.role_ids" multiple autocomplete="off">
                <option value="">请选择角色</option>
                <option v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ editingUser ? '新密码' : '密码 *' }}</label>
              <input type="password" v-model="userForm.password" :placeholder="editingUser ? '留空则不修改' : '请输入密码'" autocomplete="new-password" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showModal = false">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="formLoading">
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
          <p>确定要删除该用户吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="handleDelete" :disabled="deleteLoading">
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showResetPwdModal" @click.self="showResetPwdModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>重置密码 - {{ resetPwdTarget?.username }}</h3>
          <button class="modal-close" @click="showResetPwdModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>新密码 *</label>
            <input
              type="password"
              v-model="newPassword"
              placeholder="请输入新密码（至少6位）"
              autocomplete="new-password"
              @keyup.enter="handleResetPwd"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showResetPwdModal = false">取消</button>
          <button class="btn-primary" @click="handleResetPwd" :disabled="resetPwdLoading">
            {{ resetPwdLoading ? '重置中...' : '确认重置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workspace-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
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

.filter-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
}

.filter-item.search-filter {
  flex: 1;
  min-width: 200px;
}

.filter-input {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
}

.filter-input::placeholder {
  color: var(--text-muted);
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.filter-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background-color: var(--accent-blue-hover);
}

.filter-btn.reset-btn {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.filter-btn.reset-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.table-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.pagination-info {
  font-size: 13px;
  color: var(--text-muted);
}

.pagination-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.pagination-btn:hover:not(:disabled) {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-current {
  font-size: 13px;
  color: var(--text-secondary);
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

.form-group input,
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

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
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
