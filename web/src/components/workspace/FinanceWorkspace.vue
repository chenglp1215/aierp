<script setup lang="ts">
defineOptions({ name: 'FinanceWorkspace' })

import DataTable from './DataTable.vue'

const invoiceColumns = [
  { key: 'invoiceNo', label: '发票号', width: '120px' },
  { key: 'customer', label: '客户名称' },
  { key: 'orderNo', label: '订单号', width: '130px' },
  { key: 'amount', label: '发票金额', align: 'right' as const },
  { key: 'tax', label: '税额', align: 'right' as const },
  { key: 'status', label: '状态' },
  { key: 'date', label: '开票日期' }
]

const invoices = [
  { invoiceNo: 'INV20260415001', customer: '深圳市腾达科技有限公司', orderNo: 'SO20260415001', amount: '¥256,000', tax: '¥33,280', status: '已开具', date: '2026-04-15' },
  { invoiceNo: 'INV20260415002', customer: '广州白云贸易有限公司', orderNo: 'SO20260415002', amount: '¥187,500', tax: '¥24,375', status: '已开具', date: '2026-04-15' },
  { invoiceNo: 'INV20260414003', customer: '北京华信数据系统公司', orderNo: 'SO20260414003', amount: '¥420,000', tax: '¥54,600', status: '已认证', date: '2026-04-14' },
  { invoiceNo: 'INV20260414004', customer: '上海鼎盛贸易集团', orderNo: 'SO20260414004', amount: '¥45,000', tax: '¥5,850', status: '待开具', date: '2026-04-14' }
]

const paymentColumns = [
  { key: 'paymentNo', label: '付款单号', width: '120px' },
  { key: 'supplier', label: '供应商' },
  { key: 'orderNo', label: '采购单号', width: '130px' },
  { key: 'amount', label: '付款金额', align: 'right' as const },
  { key: 'method', label: '付款方式' },
  { key: 'status', label: '状态' },
  { key: 'date', label: '付款日期' }
]

const payments = [
  { paymentNo: 'PAY20260415001', supplier: '深圳华强电子有限公司', orderNo: 'PR20260415001', amount: '¥224,500', method: '银行转账', status: '已付款', date: '2026-04-15' },
  { paymentNo: 'PAY20260414002', supplier: '广州天河数码科技', orderNo: 'PR20260414002', amount: '¥89,000', method: '银行转账', status: '已付款', date: '2026-04-14' },
  { paymentNo: 'PAY20260414003', supplier: '北京中关物资公司', orderNo: 'PR20260414003', amount: '¥450,000', method: '承兑汇票', status: '处理中', date: '2026-04-14' }
]

const stats = [
  { title: '本月应收', value: '¥1,234,500', subtitle: '已收 ¥908,500', trend: 'up' as const, icon: 'money' as const, color: 'green' as const },
  { title: '本月应付', value: '¥856,200', subtitle: '已付 ¥623,000', trend: 'neutral' as const, icon: 'money' as const, color: 'blue' as const },
  { title: '本月支出', value: '¥423,800', subtitle: '较上月 -5.2%', trend: 'down' as const, icon: 'money' as const, color: 'red' as const }
]

const handleAction = (actionId: string, row: any) => {
  console.log('Action:', actionId, row)
}
</script>

<template>
  <div class="finance-workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">财务管理</h2>
      <div class="header-actions">
        <button class="action-btn">财务报表</button>
        <button class="primary-btn">新建付款</button>
      </div>
    </div>

    <div class="stats-row">
      <div v-for="stat in stats" :key="stat.title" class="stat-box">
        <span class="stat-label">{{ stat.title }}</span>
        <span class="stat-value">{{ stat.value }}</span>
        <span class="stat-sub">{{ stat.subtitle }}</span>
      </div>
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">发票管理</h3>
        <div class="section-actions">
          <button class="action-btn">开票</button>
          <button class="action-btn">导出</button>
        </div>
      </div>
      <DataTable
        :columns="invoiceColumns"
        :data="invoices"
        :actions="[{ id: 'view', label: '查看', type: 'default' as const }, { id: 'download', label: '下载', type: 'default' as const }]"
        @action="handleAction"
      />
    </div>

    <div class="table-section">
      <div class="section-header">
        <h3 class="section-title">付款管理</h3>
        <div class="section-actions">
          <button class="action-btn">导出</button>
        </div>
      </div>
      <DataTable
        :columns="paymentColumns"
        :data="payments"
        :actions="[{ id: 'detail', label: '详情', type: 'default' as const }, { id: 'approve', label: '审批', type: 'primary' as const }]"
        @action="handleAction"
      />
    </div>
  </div>
</template>

<style scoped>
.finance-workspace {
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
  color: var(--color-ink);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.primary-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  background-color: var(--color-interactive);
  color: white;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  background-color: var(--color-interactive-hover);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-box {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: var(--shadow-card);
}

.stat-label {
  font-size: 13px;
  color: var(--color-muted);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
}

.stat-sub {
  font-size: 12px;
  color: var(--color-muted);
}

.table-section {
  background-color: var(--color-canvas);
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
  color: var(--color-ink);
}

.section-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-muted);
  font-size: 13px;
  border: 1px solid var(--color-hairline);
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--color-ink);
}
</style>