<script setup lang="ts">
import DataTable from './DataTable.vue'

const columns = [
  { key: 'orderNo', label: '采购单号', width: '130px' },
  { key: 'supplier', label: '供应商' },
  { key: 'product', label: '采购商品' },
  { key: 'quantity', label: '数量', align: 'right' as const },
  { key: 'amount', label: '采购金额', align: 'right' as const },
  { key: 'status', label: '状态' },
  { key: 'date', label: '采购日期' }
]

const data = [
  { orderNo: 'PR20260415001', supplier: '深圳华强电子有限公司', product: 'Intel i7-12700K 处理器', quantity: 50, amount: '¥224,500', status: '待入库', date: '2026-04-15' },
  { orderNo: 'PR20260414002', supplier: '广州天河数码科技', product: '三星980 PRO 1TB SSD', quantity: 100, amount: '¥89,000', status: '已完成', date: '2026-04-14' },
  { orderNo: 'PR20260414003', supplier: '北京中关物资公司', product: 'NVIDIA RTX 4080 显卡', quantity: 30, amount: '¥450,000', status: '运输中', date: '2026-04-14' },
  { orderNo: 'PR20260413004', supplier: '上海浦东电子集团', product: '镁光DDR5 32GB内存条', quantity: 80, amount: '¥192,000', status: '已完成', date: '2026-04-13' },
  { orderNo: 'PR20260413005', supplier: '杭州阿里巴巴供应商', product: '西部数据 4TB 机械硬盘', quantity: 60, amount: '¥126,000', status: '待审批', date: '2026-04-13' }
]

const supplierColumns = [
  { key: 'code', label: '供应商编码', width: '100px' },
  { key: 'name', label: '供应商名称' },
  { key: 'contact', label: '联系人' },
  { key: 'phone', label: '联系电话' },
  { key: 'category', label: '供应类别' },
  { key: 'status', label: '状态' }
]

const suppliers = [
  { code: 'S001', name: '深圳华强电子有限公司', contact: '张经理', phone: '0755-12345678', category: '电子元器件', status: '合作中' },
  { code: 'S002', name: '广州天河数码科技', contact: '李总监', phone: '020-87654321', category: '存储设备', status: '合作中' },
  { code: 'S003', name: '北京中关物资公司', contact: '王经理', phone: '010-65432109', category: '显示设备', status: '合作中' },
  { code: 'S004', name: '上海浦东电子集团', contact: '陈总', phone: '021-98765432', category: '存储设备', status: '审核中' },
  { code: 'S005', name: '杭州阿里巴巴供应商', contact: '刘经理', phone: '0571-56789012', category: '办公设备', status: '合作中' }
]

const handleAction = (actionId: string, row: any) => {
  console.log('Action:', actionId, row)
}
</script>

<template>
  <div class="procurement-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">采购管理</h2>
      <button class="primary-btn">新建采购单</button>
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">采购订单列表</h3>
        <div class="section-actions">
          <button class="action-btn">筛选</button>
          <button class="action-btn">导出</button>
        </div>
      </div>
      <DataTable
        :columns="columns"
        :data="data"
        :actions="[{ id: 'detail', label: '详情', type: 'default' as const }, { id: 'approve', label: '审批', type: 'primary' as const }]"
        @action="handleAction"
      />
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">供应商管理</h3>
        <div class="section-actions">
          <button class="action-btn">添加供应商</button>
        </div>
      </div>
      <DataTable
        :columns="supplierColumns"
        :data="suppliers"
        :actions="[{ id: 'edit', label: '编辑', type: 'default' as const }, { id: 'view', label: '查看', type: 'default' as const }]"
        @action="handleAction"
      />
    </div>
  </div>
</template>

<style scoped>
.procurement-workspace {
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