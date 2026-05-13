# 用户设置弹窗与角色初始化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 恢复数据库初始化脚本中的 4 个固定角色，并实现用户设置弹窗功能

**Architecture:** 修改后端初始化脚本添加角色初始化函数；创建独立的前端用户设置弹窗组件，集成到 DashboardHeader

**Tech Stack:** Python, pymysql, bcrypt（后端）；Vue 3, TypeScript, Composition API（前端）

---

## 文件结构

| 文件 | 操作 | 负责内容 |
|------|------|----------|
| `backend/scripts/init_db_sync.py` | 修改 | 添加三个角色初始化函数 |
| `web/src/components/UserSettingsDialog.vue` | 创建 | 用户设置弹窗组件 |
| `web/src/components/DashboardHeader.vue` | 修改 | 集成用户设置弹窗 |

---

### Task 1: 添加仓库管理员角色初始化函数

**Files:**
- Modify: `backend/scripts/init_db_sync.py`

- [ ] **Step 1: 添加 init_warehouse_admin_role 函数**

在 `init_super_admin_role` 函数后添加以下代码：

```python
def init_warehouse_admin_role(conn):
    """初始化仓库管理员角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'warehouse_admin'")
    result = cursor.fetchone()

    if result:
        logger.info("仓库管理员角色已存在，跳过初始化")
        return

    # 获取仓库和库存相关权限
    warehouse_perm_codes = [
        "warehouse.view", "warehouse.create", "warehouse.edit", "warehouse.delete",
        "inventory.stock.view", "inventory.stock.edit",
        "inventory.check.view", "inventory.check.edit",
    ]
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(warehouse_perm_codes)), warehouse_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('warehouse_admin', '仓库管理员', '仓库管理员，负责仓库日常管理', 1, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建仓库管理员角色成功，关联 {len(perm_ids)} 条权限")
```

- [ ] **Step 2: 验证语法正确**

Run: `cd backend && python -c "import scripts.init_db_sync" 2>&1 | head -5`
Expected: 无语法错误输出

---

### Task 2: 添加采购组角色初始化函数

**Files:**
- Modify: `backend/scripts/init_db_sync.py`

- [ ] **Step 1: 添加 init_purchaser_group_role 函数**

在 `init_warehouse_admin_role` 函数后添加以下代码：

```python
def init_purchaser_group_role(conn):
    """初始化采购组角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'purchaser_group'")
    result = cursor.fetchone()

    if result:
        logger.info("采购组角色已存在，跳过初始化")
        return

    # 获取采购和订单查看相关权限
    purchaser_perm_codes = [
        "procurement.view", "procurement.create", "procurement.edit",
        "order.view",
    ]
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(purchaser_perm_codes)), purchaser_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('purchaser_group', '采购组', '采购组成员，负责品牌商品采购', 1, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建采购组角色成功，关联 {len(perm_ids)} 条权限")
```

- [ ] **Step 2: 验证语法正确**

Run: `cd backend && python -c "import scripts.init_db_sync" 2>&1 | head -5`
Expected: 无语法错误输出

---

### Task 3: 添加普通用户角色初始化函数

**Files:**
- Modify: `backend/scripts/init_db_sync.py`

- [ ] **Step 1: 添加 init_default_user_role 函数**

在 `init_purchaser_group_role` 函数后添加以下代码：

```python
def init_default_user_role(conn):
    """初始化普通用户角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'user'")
    result = cursor.fetchone()

    if result:
        logger.info("普通用户角色已存在，跳过初始化")
        return

    # 获取基础权限
    basic_perm_codes = [
        "dashboard.view", "chat.view",
        "customer.view", "customer.create", "customer.edit",
        "product.view", "product.create", "product.edit",
        "order.view", "order.create", "order.edit", "order.confirm",
        "procurement.view", "procurement.create", "procurement.edit",
        "receivable.view", "receivable.create", "receivable.edit", "receivable.record",
        "warehouse.view", "warehouse.create", "warehouse.edit",
        "inventory.stock.view", "inventory.stock.edit",
        "finance.invoice.view", "finance.payment.view",
        "intelligent.settings.view"
    ]
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(basic_perm_codes)), basic_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('user', '普通用户', '普通用户角色，拥有基础权限', 0, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建普通用户角色成功，关联 {len(perm_ids)} 条权限")
```

- [ ] **Step 2: 验证语法正确**

Run: `cd backend && python -c "import scripts.init_db_sync" 2>&1 | head -5`
Expected: 无语法错误输出

---

### Task 4: 更新 main 函数调用新角色初始化

**Files:**
- Modify: `backend/scripts/init_db_sync.py`

- [ ] **Step 1: 修改 main 函数**

将 `main` 函数修改为：

```python
def main():
    logger.info("开始初始化 MySQL 数据库数据...")

    try:
        conn = get_connection()

        init_default_permissions(conn)
        init_super_admin_role(conn)
        init_warehouse_admin_role(conn)
        init_purchaser_group_role(conn)
        init_default_user_role(conn)
        init_admin_user(conn)

        conn.close()
        logger.info("MySQL 数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
```

- [ ] **Step 2: 运行初始化脚本验证**

Run: `cd backend && python scripts/init_db_sync.py`
Expected: 输出包含 "创建仓库管理员角色成功"、"创建采购组角色成功"、"创建普通用户角色成功"

- [ ] **Step 3: 验证数据库中的角色**

Run: `cd backend && python -c "
import pymysql
from config import settings
conn = pymysql.connect(host=settings.MYSQL_HOST, port=settings.MYSQL_PORT, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD, database=settings.MYSQL_DATABASE)
cursor = conn.cursor()
cursor.execute('SELECT code, name FROM roles')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')
conn.close()
"`
Expected: 显示 4 个角色（super_admin, warehouse_admin, purchaser_group, user）

- [ ] **Step 4: 提交后端修改**

```bash
git add backend/scripts/init_db_sync.py
git commit -m "feat: 恢复数据库初始化脚本中的4个固定角色

- 添加仓库管理员角色初始化
- 添加采购组角色初始化
- 添加普通用户角色初始化

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: 创建用户设置弹窗组件

**Files:**
- Create: `web/src/components/UserSettingsDialog.vue`

- [ ] **Step 1: 创建组件文件**

创建 `web/src/components/UserSettingsDialog.vue` 文件：

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { authApi } from '../../services/api'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

interface UserData {
  id: number
  username: string
  email: string
  phone?: string
  full_name?: string
  roles?: Array<{ id: number; name: string; code: string }>
}

const loading = ref(false)
const saving = ref(false)
const userData = ref<UserData | null>(null)
const email = ref('')
const newPassword = ref('')

const loadUserData = async () => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return

  try {
    const user = JSON.parse(userStr)
    loading.value = true
    const res = await authApi.getUser(String(user.id))
    userData.value = res
    email.value = res.email || ''
    newPassword.value = ''
  } catch (error) {
    console.error('加载用户信息失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!userData.value) return

  if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    window.showToast('请输入有效的邮箱地址', 'warning')
    return
  }

  if (newPassword.value && newPassword.value.length < 6) {
    window.showToast('密码长度不能少于6位', 'warning')
    return
  }

  saving.value = true
  try {
    const data: any = {
      email: email.value || undefined
    }
    if (newPassword.value) {
      data.new_password = newPassword.value
    }
    await authApi.updateUser(String(userData.value.id), data)
    window.showToast('保存成功', 'success')
    emit('saved')
    emit('close')
  } catch (error: any) {
    window.showToast(error.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  emit('close')
}

watch(() => props.visible, (val) => {
  if (val) {
    loadUserData()
  }
})
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="handleClose">
    <div class="modal">
      <div class="modal-header">
        <h3>用户设置</h3>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body">
        <div v-if="loading" class="loading-cell">加载中...</div>
        <template v-else-if="userData">
          <div class="form-row">
            <div class="form-group">
              <label>用户名</label>
              <input type="text" :value="userData.username" disabled />
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="email" v-model="email" placeholder="请输入邮箱" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>手机</label>
              <input type="text" :value="userData.phone || '-'" disabled />
            </div>
            <div class="form-group">
              <label>姓名</label>
              <input type="text" :value="userData.full_name || '-'" disabled />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>角色</label>
              <input type="text" :value="userData.roles?.map(r => r.name).join(', ') || '-'" disabled />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input type="password" v-model="newPassword" placeholder="留空则不修改" autocomplete="new-password" />
            </div>
          </div>
        </template>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="handleClose">取消</button>
        <button class="btn-primary" @click="handleSave" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

.form-group input {
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-group input:focus {
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

.loading-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 2: 验证组件语法**

Run: `cd web && npm run build 2>&1 | head -20`
Expected: 无编译错误

---

### Task 6: 集成用户设置弹窗到 DashboardHeader

**Files:**
- Modify: `web/src/components/DashboardHeader.vue`

- [ ] **Step 1: 导入组件并添加状态**

在 `<script setup>` 部分添加：

```typescript
import UserSettingsDialog from './UserSettingsDialog.vue'

const showSettingsDialog = ref(false)
```

- [ ] **Step 2: 修改 handleSettings 函数**

将 `handleSettings` 函数修改为：

```typescript
const handleSettings = () => {
  showUserMenu.value = false
  showSettingsDialog.value = true
}
```

- [ ] **Step 3: 添加弹窗关闭和保存回调**

添加以下函数：

```typescript
const handleSettingsClose = () => {
  showSettingsDialog.value = false
}

const handleSettingsSaved = () => {
  // 可以在这里刷新用户信息
  window.dispatchEvent(new CustomEvent('user-updated'))
}
```

- [ ] **Step 4: 在模板中添加弹窗组件**

在 `<template>` 的最后 `</header>` 前添加：

```vue
    <UserSettingsDialog
      :visible="showSettingsDialog"
      @close="handleSettingsClose"
      @saved="handleSettingsSaved"
    />
```

- [ ] **Step 5: 验证前端编译**

Run: `cd web && npm run build 2>&1 | head -20`
Expected: 无编译错误

- [ ] **Step 6: 提交前端修改**

```bash
git add web/src/components/UserSettingsDialog.vue web/src/components/DashboardHeader.vue
git commit -m "feat: 实现用户设置弹窗功能

- 创建 UserSettingsDialog 组件
- 集成到 DashboardHeader 设置按钮
- 支持编辑邮箱和密码

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: 验证完整功能

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && python main.py &`
Expected: 服务启动成功

- [ ] **Step 2: 启动前端服务**

Run: `cd web && npm run dev`
Expected: 前端服务启动成功

- [ ] **Step 3: 手动验证**

1. 登录系统
2. 点击右上角用户头像
3. 点击"设置"按钮
4. 验证弹窗显示用户信息
5. 修改邮箱，点击保存
6. 验证保存成功提示

---

## 自检清单

**1. Spec 覆盖率:**
- [x] 用户设置弹窗展示 → Task 5, 6
- [x] 字段只读状态 → Task 5 (disabled 属性)
- [x] 邮箱验证 → Task 5 (正则验证)
- [x] 密码验证 → Task 5 (长度验证)
- [x] 保存功能 → Task 5 (authApi.updateUser)
- [x] 数据库角色初始化 → Task 1-4

**2. 占位符扫描:** 无 TBD、TODO、"implement later" 等占位符

**3. 类型一致性:** 组件使用 TypeScript 接口定义，API 调用与现有代码一致