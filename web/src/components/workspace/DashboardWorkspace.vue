<script setup lang="ts">
defineOptions({ name: 'DashboardWorkspace' })

import StatCard from './StatCard.vue'
import DataTable from './DataTable.vue'

const stats = [
  { title: '本月订单', value: '1,284', subtitle: '较上月 +12.5%', trend: 'up' as const, icon: 'order', color: 'blue' as const },
  { title: '销售额', value: '¥2,456,780', subtitle: '较上月 +8.3%', trend: 'up' as const, icon: 'money', color: 'green' as const },
  { title: '库存商品', value: '5,672', subtitle: '较上月 -2.1%', trend: 'down' as const, icon: 'product', color: 'yellow' as const },
  { title: '客户总数', value: '3,458', subtitle: '较上月 +15', trend: 'up' as const, icon: 'user', color: 'blue' as const }
]

const recentOrdersColumns = [
  { key: 'orderNo', label: '订单编号', width: '120px' },
  { key: 'customer', label: '客户名称' },
  { key: 'amount', label: '订单金额', align: 'right' as const },
  { key: 'status', label: '状态' },
  { key: 'date', label: '下单时间' }
]

const recentOrders = [
  { orderNo: 'PO20260415001', customer: '深圳市腾达科技有限公司', amount: '¥128,500', status: '待发货', date: '2026-04-15 10:30' },
  { orderNo: 'PO20260415002', customer: '广州白云贸易有限公司', amount: '¥85,200', status: '已完成', date: '2026-04-15 09:15' },
  { orderNo: 'PO20260414003', customer: '北京华信数据系统公司', amount: '¥256,000', status: '处理中', date: '2026-04-14 16:45' },
  { orderNo: 'PO20260414004', customer: '上海鼎盛贸易集团', amount: '¥178,300', status: '已完成', date: '2026-04-14 14:20' },
  { orderNo: 'PO20260414005', customer: '杭州智联科技公司', amount: '¥92,800', status: '待发货', date: '2026-04-14 11:00' }
]

const lowStockColumns = [
  { key: 'productCode', label: '商品编码', width: '100px' },
  { key: 'productName', label: '商品名称' },
  { key: 'stock', label: '当前库存', align: 'right' as const },
  { key: 'minStock', label: '最低库存', align: 'right' as const }
]

const lowStockProducts = [
  { productCode: 'P001', productName: '联想ThinkPad X1 Carbon', stock: 5, minStock: 10 },
  { productCode: 'P002', productName: '戴尔显示器 27寸 4K', stock: 8, minStock: 15 },
  { productCode: 'P003', productName: '罗技MX Keys键盘', stock: 12, minStock: 20 },
  { productCode: 'P004', productName: '华为MateBook 14', stock: 3, minStock: 8 }
]

const handleOrderAction = (actionId: string, row: any) => {
  console.log('Order action:', actionId, row)
}

const handleRowClick = (row: any) => {
  console.log('Row clicked:', row)
}
</script>

<template>
  <div class="dashboard-workspace">
    <div class="stats-grid">
      <StatCard
        v-for="stat in stats"
        :key="stat.title"
        :title="stat.title"
        :value="stat.value"
        :subtitle="stat.subtitle"
        :trend="stat.trend"
        :icon="stat.icon"
        :color="stat.color"
      />
    </div>

    <div class="tables-grid">
      <div class="table-card">
        <div class="table-card-header">
          <h3 class="table-card-title">近期订单</h3>
          <button class="view-more-btn">查看更多</button>
        </div>
        <DataTable
          :columns="recentOrdersColumns"
          :data="recentOrders"
          :actions="[{ id: 'view', label: '查看', type: 'default' as const }]"
          @action="handleOrderAction"
          @row-click="handleRowClick"
        />
      </div>

      <div class="table-card">
        <div class="table-card-header">
          <h3 class="table-card-title">库存预警</h3>
          <button class="view-more-btn">查看更多</button>
        </div>
        <DataTable
          :columns="lowStockColumns"
          :data="lowStockProducts"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-workspace {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.tables-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.table-card {
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.table-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.view-more-btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-interactive);
  font-size: 12px;
  border: 1px solid var(--color-interactive);
  transition: all var(--transition-fast);
}

.view-more-btn:hover {
  background-color: var(--color-interactive);
  color: white;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .tables-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>