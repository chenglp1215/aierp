<script setup lang="ts">
defineOptions({ name: 'InventoryWorkspace' })

import DataTable from './DataTable.vue'
import { ref } from 'vue'

const stockColumns = [
  { key: 'productCode', label: '商品编码', width: '100px' },
  { key: 'productName', label: '商品名称' },
  { key: 'category', label: '商品类别' },
  { key: 'stock', label: '当前库存', align: 'right' as const },
  { key: 'minStock', label: '最低库存', align: 'right' as const },
  { key: 'unit', label: '单位' },
  { key: 'location', label: '存放位置' }
]

const stockData = [
  { productCode: 'P001', productName: '联想ThinkPad X1 Carbon', category: '笔记本电脑', stock: 15, minStock: 10, unit: '台', location: 'A区-01-01' },
  { productCode: 'P002', productName: '戴尔显示器 27寸 4K', category: '显示器', stock: 28, minStock: 15, unit: '台', location: 'A区-01-02' },
  { productCode: 'P003', productName: '罗技MX Keys键盘', category: '外设', stock: 45, minStock: 20, unit: '个', location: 'B区-02-01' },
  { productCode: 'P004', productName: '华为MateBook 14', category: '笔记本电脑', stock: 8, minStock: 8, unit: '台', location: 'A区-01-03' },
  { productCode: 'P005', productName: 'Intel i7-12700K', category: 'CPU', stock: 120, minStock: 50, unit: '个', location: 'C区-01-01' }
]

const handleAction = (actionId: string, row: any) => {
  console.log('Action:', actionId, row)
}
</script>

<template>
  <div class="inventory-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">库存管理</h2>
      <div class="header-actions">
        <button class="action-btn">库存盘点</button>
        <button class="primary-btn">新增入库</button>
      </div>
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">库存列表</h3>
        <div class="section-actions">
          <button class="action-btn">筛选</button>
          <button class="action-btn">导出</button>
        </div>
      </div>
      <DataTable
        :columns="stockColumns"
        :data="stockData"
        :actions="[{ id: 'detail', label: '详情', type: 'default' as const }, { id: 'adjust', label: '调整', type: 'default' as const }]"
        @action="handleAction"
      />
    </div>
  </div>
</template>

<style scoped>
.inventory-workspace {
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
}

.header-actions {
  display: flex;
  gap: 8px;
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--accent-blue);
  color: white;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--accent-blue-hover);
}

.table-section {
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
}

.section-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}
</style>
