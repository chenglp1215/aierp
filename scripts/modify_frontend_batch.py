#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端批次管理功能修改脚本 - 一次性修改所有 Vue 文件"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, 'web', 'src')

def modify_inventory_workspace():
    """修改 InventoryWorkspace.vue - F2/F3/F4"""
    filepath = os.path.join(WEB_DIR, 'components', 'workspace', 'InventoryWorkspace.vue')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # F2: 修改 import，添加 warehouseLocationApi
    content = content.replace(
        "import { stockApi, warehouseApi, productApi, inboundBatchApi, outboundBatchApi } from '../../services/api'",
        "import { stockApi, warehouseApi, productApi, inboundBatchApi, outboundBatchApi, warehouseLocationApi } from '../../services/api'"
    )

    # F3: Stock 接口添加 locked_quantity 和 available_quantity
    content = content.replace(
        "  quantity: number\n  min_stock: number",
        "  quantity: number\n  locked_quantity?: number\n  available_quantity?: number\n  min_stock: number"
    )

    # F2: InboundBatch 接口添加新字段
    content = content.replace(
        "interface InboundBatch {\n  id: string\n  inventory_id: string\n  batch_code: string\n  quantity: number\n  user_id?: string\n  user_name?: string\n  remarks?: string\n  created_at: string\n}",
        "interface InboundBatch {\n  id: string\n  inventory_id: string\n  batch_code: string\n  quantity: number\n  location_id?: number | null\n  location_code?: string | null\n  expiry_date?: string | null\n  current_quantity?: number\n  user_id?: string\n  user_name?: string\n  remarks?: string\n  created_at: string\n}"
    )

    # F2: inboundForm 添加新字段
    content = content.replace(
        "const inboundForm = ref({\n  warehouse_id: '',\n  product_id: '',\n  product_code: '',\n  product_name: '',\n  spec_id: '',\n  spec_code: '',\n  quantity: 0,\n  remarks: ''\n})",
        "const inboundForm = ref({\n  warehouse_id: '',\n  product_id: '',\n  product_code: '',\n  product_name: '',\n  spec_id: '',\n  spec_code: '',\n  quantity: 0,\n  location_id: null as number | null,\n  location_code: '',\n  expiry_date: '',\n  remarks: ''\n})"
    )

    # F2: 添加库位相关变量和方法（在 formLoading 后面）
    location_code = """// 库位相关
interface WarehouseLocation {
  id: string
  warehouse_id: number
  location_code: string
  location_name?: string
  status: string
  description?: string
}
const locationList = ref<WarehouseLocation[]>([])
const locationLoading = ref(false)

const loadLocationsByWarehouse = async (warehouseId: string | number) => {
  if (!warehouseId) {
    locationList.value = []
    return
  }
  locationLoading.value = true
  try {
    const res = await warehouseLocationApi.list({ warehouse_id: warehouseId, page_size: 200 })
    locationList.value = res?.items || []
  } catch (e) {
    console.error('加载库位列表失败:', e)
    locationList.value = []
  } finally {
    locationLoading.value = false
  }
}

const handleLocationSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selectedId = target.value
  inboundForm.value.location_id = selectedId ? Number(selectedId) : null
  const selected = locationList.value.find(l => l.id === selectedId)
  inboundForm.value.location_code = selected ? selected.location_code : ''
}

const handleWarehouseChangeForInbound = () => {
  loadLocationsByWarehouse(inboundForm.value.warehouse_id)
  inboundForm.value.location_id = null
  inboundForm.value.location_code = ''
}
"""
    content = content.replace(
        "const formLoading = ref(false)\n\nconst filterKeyword",
        "const formLoading = ref(false)\n\n" + location_code + "\nconst filterKeyword"
    )

    # F2: openCreateInbound 添加新字段初始化和库位加载
    content = content.replace(
        """const openCreateInbound = () => {
  inboundTargetStock.value = null
  inboundForm.value = {
    warehouse_id: filterWarehouse.value || '',
    product_id: '',
    product_code: '',
    product_name: '',
    spec_id: '',
    spec_code: '',
    quantity: 0,
    remarks: ''
  }
  selectedSpec.value = null
  specKeyword.value = ''
  specSearchResults.value = []
  showInboundModal.value = true
}""",
        """const openCreateInbound = () => {
  inboundTargetStock.value = null
  inboundForm.value = {
    warehouse_id: filterWarehouse.value || '',
    product_id: '',
    product_code: '',
    product_name: '',
    spec_id: '',
    spec_code: '',
    quantity: 0,
    location_id: null,
    location_code: '',
    expiry_date: '',
    remarks: ''
  }
  selectedSpec.value = null
  specKeyword.value = ''
  specSearchResults.value = []
  locationList.value = []
  if (filterWarehouse.value) {
    loadLocationsByWarehouse(filterWarehouse.value)
  }
  showInboundModal.value = true
}"""
    )

    # F2: openInboundModal 添加新字段初始化和库位加载
    content = content.replace(
        """const openInboundModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  inboundTargetStock.value = stock
  inboundForm.value = {
    warehouse_id: stock.warehouse_id,
    product_id: stock.product_id,
    product_code: stock.product_code || stock.product_info?.product_code || '',
    product_name: stock.product_name || stock.product_info?.name || '',
    spec_id: stock.spec_id,
    spec_code: stock.spec_code || stock.spec_info?.spec_code || '',
    quantity: 0,
    remarks: ''
  }
  showInboundModal.value = true
}""",
        """const openInboundModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  inboundTargetStock.value = stock
  inboundForm.value = {
    warehouse_id: stock.warehouse_id,
    product_id: stock.product_id,
    product_code: stock.product_code || stock.product_info?.product_code || '',
    product_name: stock.product_name || stock.product_info?.name || '',
    spec_id: stock.spec_id,
    spec_code: stock.spec_code || stock.spec_info?.spec_code || '',
    quantity: 0,
    location_id: null,
    location_code: '',
    expiry_date: '',
    remarks: ''
  }
  loadLocationsByWarehouse(stock.warehouse_id)
  showInboundModal.value = true
}"""
    )

    # F2: handleInbound 添加新字段传递
    content = content.replace(
        """    await inboundBatchApi.create({
      warehouse_id: inboundForm.value.warehouse_id,
      product_id: inboundForm.value.product_id,
      product_code: inboundForm.value.product_code,
      product_name: inboundForm.value.product_name,
      spec_id: inboundForm.value.spec_id,
      spec_code: inboundForm.value.spec_code,
      stock_id: inboundTargetStock.value?.id || '',
      quantity: inboundForm.value.quantity,
      user_id: user.id,
      user_name: user.name || user.username || '未知用户'
    })""",
        """    await inboundBatchApi.create({
      warehouse_id: inboundForm.value.warehouse_id,
      product_id: inboundForm.value.product_id,
      product_code: inboundForm.value.product_code,
      product_name: inboundForm.value.product_name,
      spec_id: inboundForm.value.spec_id,
      spec_code: inboundForm.value.spec_code,
      stock_id: inboundTargetStock.value?.id || '',
      quantity: inboundForm.value.quantity,
      location_id: inboundForm.value.location_id || null,
      location_code: inboundForm.value.location_code || null,
      expiry_date: inboundForm.value.expiry_date || null,
      user_id: user.id,
      user_name: user.name || user.username || '未知用户'
    })"""
    )

    # F3: buildVerticalTableData 添加 locked_quantity 和 available_quantity
    content = content.replace(
        "        quantity: stock.quantity,\n        min_stock: stock.min_stock,",
        "        quantity: stock.quantity,\n        locked_quantity: stock.locked_quantity ?? 0,\n        available_quantity: stock.available_quantity ?? stock.quantity,\n        min_stock: stock.min_stock,"
    )

    # F2: 入库弹窗模板 - 仓库选择添加 change 事件
    content = content.replace(
        '<select v-model="inboundForm.warehouse_id">',
        '<select v-model="inboundForm.warehouse_id" @change="handleWarehouseChangeForInbound">'
    )

    # F2: 入库弹窗模板 - 在入库数量和备注之间添加库位和有效期
    content = content.replace(
        """          <div class="form-group">
            <label>入库数量 *</label>
            <input type="number" v-model="inboundForm.quantity" min="1" placeholder="请输入入库数量" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="inboundForm.remarks" placeholder="可选填写备注信息" />
          </div>""",
        """          <div class="form-group">
            <label>入库数量 *</label>
            <input type="number" v-model="inboundForm.quantity" min="1" placeholder="请输入入库数量" />
          </div>
          <div class="form-group">
            <label>库位</label>
            <select :value="inboundForm.location_id || ''" @change="handleLocationSelect" :disabled="locationLoading">
              <option value="">请选择库位</option>
              <option v-for="loc in locationList" :key="loc.id" :value="loc.id">{{ loc.location_code }}{{ loc.location_name ? ' (' + loc.location_name + ')' : '' }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>有效截止时间</label>
            <input type="date" v-model="inboundForm.expiry_date" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input type="text" v-model="inboundForm.remarks" placeholder="可选填写备注信息" />
          </div>"""
    )

    # F3: 库存表格添加锁定数量和可用数量列
    content = content.replace(
        """        <vxe-column field="quantity" title="当前库存" min-width="70" class-name="col--center">
          <template #default="{ row }">
            <span class="number-cell">{{ row.quantity }}</span>
          </template>
        </vxe-column>
        <vxe-column field="min_stock" title="最低库存" min-width="60" class-name="col--center" />""",
        """        <vxe-column field="quantity" title="当前库存" min-width="70" class-name="col--center">
          <template #default="{ row }">
            <span class="number-cell">{{ row.quantity }}</span>
          </template>
        </vxe-column>
        <vxe-column field="locked_quantity" title="锁定数量" min-width="70" class-name="col--center">
          <template #default="{ row }">
            <span class="number-cell">{{ row.locked_quantity }}</span>
          </template>
        </vxe-column>
        <vxe-column field="available_quantity" title="可用数量" min-width="70" class-name="col--center">
          <template #default="{ row }">
            <span class="number-cell">{{ row.available_quantity }}</span>
          </template>
        </vxe-column>
        <vxe-column field="min_stock" title="最低库存" min-width="60" class-name="col--center" />"""
    )

    # F4: 库存详情弹窗 - 入库记录 tab 改为批次详情展示
    content = content.replace(
        """            <div v-show="detailActiveTab === 'inbound'" class="batch-scroll-list">
              <div class="batch-scroll-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
                <span class="batch-user">{{ batch.user_name || '-' }}</span>
                <span class="batch-qty success">+{{ batch.quantity }}</span>
                <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
              </div>
              <div v-if="!stockDetail.inbound_batches?.length" class="batches-empty">暂无入库记录</div>
            </div>""",
        """            <div v-show="detailActiveTab === 'inbound'" class="batch-scroll-list">
              <div class="batch-detail-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
                <div class="batch-detail-row">
                  <span class="batch-detail-label">库位:</span>
                  <span class="batch-detail-value">{{ batch.location_code || '-' }}</span>
                  <span class="batch-detail-label" style="margin-left:12px">有效期:</span>
                  <span class="batch-detail-value" :class="{
                    'text-expired': batch.expiry_date && new Date(batch.expiry_date) < new Date(),
                    'text-expiring': batch.expiry_date && new Date(batch.expiry_date) >= new Date() && new Date(batch.expiry_date) < new Date(Date.now() + 30 * 24 * 3600 * 1000)
                  }">{{ batch.expiry_date ? batch.expiry_date.substring(0, 10) : '-' }}</span>
                </div>
                <div class="batch-detail-row">
                  <span class="batch-detail-label">入库数量:</span>
                  <span class="batch-detail-value success">+{{ batch.quantity }}</span>
                  <span class="batch-detail-label" style="margin-left:12px">当前剩余:</span>
                  <span class="batch-detail-value">{{ batch.current_quantity ?? batch.quantity }}</span>
                  <span class="batch-detail-label" style="margin-left:12px">操作人:</span>
                  <span class="batch-detail-value">{{ batch.user_name || '-' }}</span>
                </div>
              </div>
              <div v-if="!stockDetail.inbound_batches?.length" class="batches-empty">暂无入库记录</div>
            </div>"""
    )

    # F4: 添加批次详情样式
    content = content.replace(
        """.batch-scroll-item.check-record {
  grid-template-columns: 1fr 80px 140px;
}""",
        """.batch-scroll-item.check-record {
  grid-template-columns: 1fr 80px 140px;
}

.batch-detail-item {
  padding: 10px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.batch-detail-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.batch-detail-label {
  color: var(--text-muted);
  min-width: 50px;
}

.batch-detail-value {
  color: var(--text-primary);
  font-weight: 500;
}

.batch-detail-value.success {
  color: var(--accent-green);
}

.text-expired {
  color: var(--accent-red) !important;
  font-weight: 600;
}

.text-expiring {
  color: var(--accent-yellow) !important;
  font-weight: 600;
}"""
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'InventoryWorkspace.vue 修改完成')


def modify_pending_outbound_workspace():
    """修改 PendingOutboundWorkspace.vue - F5"""
    filepath = os.path.join(WEB_DIR, 'components', 'workspace', 'PendingOutboundWorkspace.vue')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # F5: 添加批次选择相关变量和方法
    batch_code = """
// 批次选择相关
interface AvailableBatch {
  id: number
  inbound_batch_id: number
  location_code: string | null
  expiry_date: string | null
  current_quantity: number
  out_quantity: number
}
const availableBatches = ref<AvailableBatch[]>([])
const batchLoading = ref(false)

const loadAvailableBatches = async (pendingId: number) => {
  batchLoading.value = true
  try {
    const res = await pendingOutboundApi.getAvailableBatches(pendingId)
    const batches = res?.items || res || []
    availableBatches.value = batches.map((b: any) => ({
      ...b,
      out_quantity: 0
    }))
    // 先进先出自动填充
    autoFillBatches()
  } catch (e) {
    console.error('加载可出库批次失败:', e)
    availableBatches.value = []
  } finally {
    batchLoading.value = false
  }
}

const autoFillBatches = () => {
  let remaining = outboundQty.value
  for (const batch of availableBatches.value) {
    if (remaining <= 0) {
      batch.out_quantity = 0
      continue
    }
    const take = Math.min(remaining, batch.current_quantity)
    batch.out_quantity = take
    remaining -= take
  }
}

const totalBatchQuantity = computed(() => {
  return availableBatches.value.reduce((sum, b) => sum + b.out_quantity, 0)
})

const batchQuantityValid = computed(() => {
  return Math.abs(totalBatchQuantity.value - outboundQty.value) < 0.001
})

const isBatchExpired = (batch: AvailableBatch) => {
  if (!batch.expiry_date) return false
  return new Date(batch.expiry_date) < new Date()
}

const isBatchExpiring = (batch: AvailableBatch) => {
  if (!batch.expiry_date) return false
  const d = new Date(batch.expiry_date)
  return d >= new Date() && d < new Date(Date.now() + 30 * 24 * 3600 * 1000)
}
"""
    content = content.replace(
        "const outboundLoading = ref(false)",
        "const outboundLoading = ref(false)\n" + batch_code
    )

    # F5: 修改 openOutboundModal 加载批次
    content = content.replace(
        """const openOutboundModal = (item: PendingOutbound) => {
  selectedPending.value = item
  outboundQty.value = item.locked_qty - item.out_qty
  showOutboundModal.value = true
}""",
        """const openOutboundModal = (item: PendingOutbound) => {
  selectedPending.value = item
  outboundQty.value = item.locked_qty - item.out_qty
  availableBatches.value = []
  loadAvailableBatches(item.id)
  showOutboundModal.value = true
}"""
    )

    # F5: 修改 handleOutbound 传递 batch_items
    content = content.replace(
        """    await pendingOutboundApi.execute(selectedPending.value.id, outboundQty.value)
    window.showToast('出库成功', 'success')""",
        """    const batchItems = availableBatches.value
      .filter(b => b.out_quantity > 0)
      .map(b => ({ inbound_batch_id: b.inbound_batch_id, quantity: b.out_quantity }))
    await pendingOutboundApi.execute(selectedPending.value.id, outboundQty.value, batchItems.length > 0 ? batchItems : undefined)
    window.showToast('出库成功', 'success')"""
    )

    # F5: 出库弹窗模板添加批次选择区域
    content = content.replace(
        """          <div class="form-section">
            <div class="form-row">
              <div class="form-group full-width">
                <label>出库数量</label>
                <input
                  type="number"
                  v-model.number="outboundQty"
                  class="form-control"
                  :max="selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0"
                  min="1"
                />
              </div>
            </div>
          </div>""",
        """          <div class="form-section">
            <div class="form-row">
              <div class="form-group full-width">
                <label>出库数量</label>
                <input
                  type="number"
                  v-model.number="outboundQty"
                  class="form-control"
                  :max="selectedPending ? selectedPending.locked_qty - selectedPending.out_qty : 0"
                  min="1"
                  @input="autoFillBatches"
                />
              </div>
            </div>
          </div>
          <div class="batch-select-section" v-if="availableBatches.length > 0">
            <h4>批次选择（先进先出）</h4>
            <div class="batch-loading" v-if="batchLoading">加载批次中...</div>
            <table class="batch-table" v-else>
              <thead>
                <tr>
                  <th>库位</th>
                  <th>有效期</th>
                  <th>剩余数量</th>
                  <th>出库数量</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="batch in availableBatches" :key="batch.inbound_batch_id" :class="{ 'batch-expired': isBatchExpired(batch), 'batch-expiring': isBatchExpiring(batch) }">
                  <td>{{ batch.location_code || '-' }}</td>
                  <td>{{ batch.expiry_date ? batch.expiry_date.substring(0, 10) : '-' }}</td>
                  <td>{{ batch.current_quantity }}</td>
                  <td>
                    <input
                      type="number"
                      v-model.number="batch.out_quantity"
                      class="batch-qty-input"
                      :max="batch.current_quantity"
                      min="0"
                      :disabled="isBatchExpired(batch)"
                    />
                  </td>
                  <td>
                    <span v-if="isBatchExpired(batch)" class="batch-status expired">已过期</span>
                    <span v-else-if="isBatchExpiring(batch)" class="batch-status expiring">即将过期</span>
                    <span v-else class="batch-status normal">正常</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="batch-summary" v-if="availableBatches.length > 0">
              <span>批次出库合计: {{ totalBatchQuantity }}</span>
              <span v-if="!batchQuantityValid" class="batch-error">（与总出库数量不一致）</span>
            </div>
          </div>"""
    )

    # F5: 确认按钮添加 batchQuantityValid 校验
    content = content.replace(
        ':disabled="outboundLoading || outboundQty <= 0"',
        ':disabled="outboundLoading || outboundQty <= 0 || (availableBatches.length > 0 && !batchQuantityValid)"'
    )

    # F5: 添加批次选择样式
    content = content.replace(
        """@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .filter-input,
  .filter-select {
    width: 100%;
  }
}""",
        """@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .filter-input,
  .filter-select {
    width: 100%;
  }
}

.batch-select-section {
  margin-top: 16px;
}

.batch-select-section h4 {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.batch-loading {
  color: var(--text-muted);
  font-size: 13px;
  padding: 8px 0;
}

.batch-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.batch-table th {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-weight: 500;
}

.batch-table td {
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.batch-table tr.batch-expired {
  opacity: 0.5;
}

.batch-table tr.batch-expiring td {
  color: var(--accent-yellow);
}

.batch-qty-input {
  width: 80px;
  padding: 4px 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 13px;
  text-align: right;
}

.batch-qty-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.batch-status {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.batch-status.normal {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}

.batch-status.expired {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.batch-status.expiring {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--accent-yellow);
}

.batch-summary {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.batch-error {
  color: var(--accent-red);
  margin-left: 8px;
}"""
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'PendingOutboundWorkspace.vue 修改完成')


def modify_warehouse_workspace():
    """修改 WarehouseWorkspace.vue - F6"""
    filepath = os.path.join(WEB_DIR, 'components', 'workspace', 'WarehouseWorkspace.vue')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # F6: 添加 warehouseLocationApi 导入
    content = content.replace(
        "import { warehouseApi } from '../../services/api'",
        "import { warehouseApi, warehouseLocationApi } from '../../services/api'"
    )

    # F6: 添加库位管理相关变量
    location_vars = """
// 库位管理相关
const showLocationModal = ref(false)
const editingLocation = ref<any | null>(null)
const locationList = ref<any[]>([])
const locationLoading = ref(false)
const locationFormLoading = ref(false)
const selectedWarehouseForLocation = ref<Warehouse | null>(null)

const locationForm = ref({
  location_code: '',
  location_name: '',
  status: 'active',
  description: ''
})

const loadLocations = async (warehouseId: string | number) => {
  locationLoading.value = true
  try {
    const res = await warehouseLocationApi.list({ warehouse_id: warehouseId, page_size: 200 })
    locationList.value = res?.items || []
  } catch (e) {
    console.error('加载库位列表失败:', e)
    locationList.value = []
  } finally {
    locationLoading.value = false
  }
}

const openLocationModal = (row: any) => {
  const warehouse = warehouses.value.find(w => w.id === row._id)
  if (!warehouse) return
  selectedWarehouseForLocation.value = warehouse
  editingLocation.value = null
  locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
  loadLocations(warehouse.id)
  showLocationModal.value = true
}

const openEditLocation = (loc: any) => {
  editingLocation.value = loc
  locationForm.value = {
    location_code: loc.location_code || '',
    location_name: loc.location_name || '',
    status: loc.status || 'active',
    description: loc.description || ''
  }
}

const handleSaveLocation = async () => {
  if (!locationForm.value.location_code.trim()) {
    window.showToast('请输入库位编码', 'warning')
    return
  }
  if (!selectedWarehouseForLocation.value) return

  locationFormLoading.value = true
  try {
    if (editingLocation.value) {
      await warehouseLocationApi.update(editingLocation.value.id, locationForm.value)
      window.showToast('库位更新成功', 'success')
    } else {
      await warehouseLocationApi.create({
        warehouse_id: selectedWarehouseForLocation.value.id,
        ...locationForm.value
      })
      window.showToast('库位创建成功', 'success')
    }
    await loadLocations(selectedWarehouseForLocation.value.id)
    editingLocation.value = null
    locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    locationFormLoading.value = false
  }
}

const handleDeleteLocation = async (loc: any) => {
  if (!confirm('确定删除该库位吗？')) return
  try {
    await warehouseLocationApi.delete(loc.id)
    window.showToast('库位删除成功', 'success')
    if (selectedWarehouseForLocation.value) {
      await loadLocations(selectedWarehouseForLocation.value.id)
    }
  } catch (error: any) {
    window.showToast(error.message || '删除失败', 'error')
  }
}

const cancelLocationEdit = () => {
  editingLocation.value = null
  locationForm.value = { location_code: '', location_name: '', status: 'active', description: '' }
}
"""
    content = content.replace(
        "onMounted(() => {",
        location_vars + "\nonMounted(() => {"
    )

    # F6: 操作列添加"库位管理"按钮
    content = content.replace(
        """            <span class="action-btns">
              <button class="btn-link" @click="viewInventory(row)">查看库存</button>
              <button class="btn-link" @click="openEditWarehouse(row)">编辑</button>
            </span>""",
        """            <span class="action-btns">
              <button class="btn-link" @click="viewInventory(row)">查看库存</button>
              <button class="btn-link" @click="openLocationModal(row)">库位管理</button>
              <button class="btn-link" @click="openEditWarehouse(row)">编辑</button>
            </span>"""
    )

    # F6: 添加库位管理弹窗
    location_modal = """
    <!-- 库位管理弹窗 -->
    <div class="modal-overlay" v-if="showLocationModal">
      <div class="modal" style="max-width: 700px;">
        <div class="modal-header">
          <h3>{{ selectedWarehouseForLocation?.name }} - 库位管理</h3>
          <button class="modal-close" @click="showLocationModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="location-form" v-if="!editingLocation">
            <div class="form-row">
              <div class="form-group">
                <label>库位编码 *</label>
                <input type="text" v-model="locationForm.location_code" placeholder="如 A-01" />
              </div>
              <div class="form-group">
                <label>库位名称</label>
                <input type="text" v-model="locationForm.location_name" placeholder="可选" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>状态</label>
                <select v-model="locationForm.status">
                  <option value="active">启用</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
              <div class="form-group">
                <label>描述</label>
                <input type="text" v-model="locationForm.description" placeholder="可选" />
              </div>
            </div>
            <button class="btn-primary" @click="handleSaveLocation" :disabled="locationFormLoading" style="align-self: flex-end;">
              {{ locationFormLoading ? '保存中...' : '添加库位' }}
            </button>
          </div>
          <div class="location-form" v-else>
            <div class="form-row">
              <div class="form-group">
                <label>库位编码 *</label>
                <input type="text" v-model="locationForm.location_code" />
              </div>
              <div class="form-group">
                <label>库位名称</label>
                <input type="text" v-model="locationForm.location_name" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>状态</label>
                <select v-model="locationForm.status">
                  <option value="active">启用</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
              <div class="form-group">
                <label>描述</label>
                <input type="text" v-model="locationForm.description" />
              </div>
            </div>
            <div style="display: flex; gap: 8px; align-self: flex-end;">
              <button class="btn-secondary" @click="cancelLocationEdit">取消</button>
              <button class="btn-primary" @click="handleSaveLocation" :disabled="locationFormLoading">
                {{ locationFormLoading ? '保存中...' : '保存' }}
              </button>
            </div>
          </div>
          <div class="location-list">
            <div v-if="locationLoading" style="text-align: center; padding: 20px; color: var(--text-muted);">加载中...</div>
            <table v-else class="location-table">
              <thead>
                <tr>
                  <th>库位编码</th>
                  <th>名称</th>
                  <th>状态</th>
                  <th>描述</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="loc in locationList" :key="loc.id">
                  <td>{{ loc.location_code }}</td>
                  <td>{{ loc.location_name || '-' }}</td>
                  <td>
                    <span class="status-tag" :class="loc.status">{{ loc.status === 'active' ? '启用' : '停用' }}</span>
                  </td>
                  <td>{{ loc.description || '-' }}</td>
                  <td>
                    <span class="action-btns">
                      <button class="btn-link" @click="openEditLocation(loc)">编辑</button>
                      <button class="btn-link danger" @click="handleDeleteLocation(loc)">删除</button>
                    </span>
                  </td>
                </tr>
                <tr v-if="locationList.length === 0">
                  <td colspan="5" style="text-align: center; color: var(--text-muted);">暂无库位</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showLocationModal = false">关闭</button>
        </div>
      </div>
    </div>
"""
    content = content.replace(
        "  </div>\n</template>",
        location_modal + "  </div>\n</template>"
    )

    # F6: 添加库位管理样式
    content = content.replace(
        """@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}""",
        """@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}

.location-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.location-list {
  max-height: 300px;
  overflow-y: auto;
}

.location-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.location-table th {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-weight: 500;
}

.location-table td {
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}"""
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'WarehouseWorkspace.vue 修改完成')


if __name__ == '__main__':
    modify_inventory_workspace()
    modify_pending_outbound_workspace()
    modify_warehouse_workspace()
    print('所有前端修改完成!')
