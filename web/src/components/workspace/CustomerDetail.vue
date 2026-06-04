<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { customerApi } from '../../services/api'

const props = defineProps<{
  visible: boolean
  customerId: number | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'edit', customer: any): void
  (e: 'claim', customer: any): void
}>()

const loading = ref(false)
const detail = ref<any>(null)

const settlementMethodMap: Record<number, string> = { 1: '月结', 2: '现结', 3: '预付' }
const settlementMethodText = computed(() => settlementMethodMap[detail.value?.settlement_method] || '-')
const fullAddress = computed(() => [detail.value?.province, detail.value?.city, detail.value?.district, detail.value?.address].filter(Boolean).join(''))
const formatAmount = (val: any) => val != null ? Number(val).toFixed(2) : '0.00'

const loadDetail = async () => {
  if (!props.customerId) return
  loading.value = true
  try {
    const res = await customerApi.getById(String(props.customerId))
    detail.value = res
  } catch (e) {
    console.error('加载客户详情失败', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.visible, (val) => {
  if (val) loadDetail()
})

const close = () => emit('update:visible', false)

const handleEdit = () => {
  emit('edit', detail.value)
  close()
}

const handleClaim = () => {
  emit('claim', detail.value)
  close()
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="close">
    <div class="modal detail-modal">
      <div class="modal-header">
        <h3>客户详情</h3>
        <button class="modal-close" @click="close">&times;</button>
      </div>
      <div v-if="loading" class="loading-text">加载中...</div>
      <div v-else-if="detail" class="modal-body">
        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="section-title">基本信息</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="label">客户编码</span><span class="value">{{ detail.customer_code }}</span></div>
            <div class="detail-item"><span class="label">客户名称</span><span class="value">{{ detail.customer_name }}</span></div>
            <div class="detail-item"><span class="label">客户类型</span><span class="value">{{ detail.customer_type === 'terminal' ? '终端' : '经销商' }}</span></div>
            <div class="detail-item"><span class="label">客户状态</span><span class="value"><span class="status-tag" :class="detail.customer_status === 1 ? 'normal' : 'pool'">{{ detail.customer_status === 1 ? '正常' : '公共池' }}</span></span></div>
            <div class="detail-item"><span class="label">业务员</span><span class="value">{{ detail.sales_user_name || '-' }}</span></div>
            <div class="detail-item"><span class="label">会员账号</span><span class="value">{{ detail.member_account || '-' }}</span></div>
            <div class="detail-item"><span class="label">结算方式</span><span class="value">{{ settlementMethodText }}</span></div>
          </div>
        </div>

        <!-- 联系方式 -->
        <div class="detail-section">
          <div class="section-title">联系方式</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="label">联系人</span><span class="value">{{ detail.contact_person || '-' }}</span></div>
            <div class="detail-item"><span class="label">联系电话</span><span class="value">{{ detail.contact_phone || '-' }}</span></div>
            <div class="detail-item"><span class="label">所属区域</span><span class="value">{{ fullAddress || '-' }}</span></div>
          </div>
        </div>

        <!-- 财务信息 -->
        <div class="detail-section">
          <div class="section-title">财务信息</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="label">账户余额</span><span class="value amount">{{ formatAmount(detail.account_balance) }}</span></div>
            <div class="detail-item"><span class="label">欠款总额</span><span class="value amount">{{ formatAmount(detail.debt_total) }}</span></div>
            <div class="detail-item"><span class="label">信用额度</span><span class="value amount">{{ formatAmount(detail.credit_limit) }}</span></div>
            <div class="detail-item"><span class="label">账期天数</span><span class="value">{{ detail.credit_days }}天</span></div>
            <div class="detail-item"><span class="label">是否超账期</span><span class="value" :class="{ 'text-danger': detail.is_overdue === 1 }">{{ detail.is_overdue === 1 ? '是' : '否' }}</span></div>
            <div class="detail-item"><span class="label">尾单时间</span><span class="value">{{ detail.last_order_time ? detail.last_order_time.substring(0, 10) : '-' }}</span></div>
            <div class="detail-item"><span class="label">成单金额</span><span class="value amount">{{ formatAmount(detail.total_order_amount) }}</span></div>
          </div>
        </div>

        <!-- 课题组信息 -->
        <div class="detail-section" v-if="detail.customer_type === 'terminal' && detail.research_groups?.length">
          <div class="section-title">课题组信息</div>
          <div v-for="rg in detail.research_groups" :key="rg.id" class="detail-grid">
            <div class="detail-item"><span class="label">课题组名称</span><span class="value">{{ rg.research_group_name }}</span></div>
            <div class="detail-item"><span class="label">负责人</span><span class="value">{{ rg.research_leader || '-' }}</span></div>
            <div class="detail-item"><span class="label">联系电话</span><span class="value">{{ rg.contact_phone || '-' }}</span></div>
          </div>
        </div>

        <!-- 开票信息 -->
        <div class="detail-section">
          <div class="section-title">开票信息</div>
          <div v-if="detail.invoice_infos?.length">
            <div v-for="inv in detail.invoice_infos" :key="inv.id" class="info-card">
              <span v-if="inv.is_default" class="default-badge">默认</span>
              <div class="detail-grid">
                <div class="detail-item"><span class="label">发票抬头</span><span class="value">{{ inv.invoice_title }}</span></div>
                <div class="detail-item"><span class="label">税号</span><span class="value">{{ inv.tax_number }}</span></div>
                <div class="detail-item"><span class="label">开户行</span><span class="value">{{ inv.bank_name }}</span></div>
                <div class="detail-item"><span class="label">银行账号</span><span class="value">{{ inv.bank_account }}</span></div>
                <div class="detail-item"><span class="label">地址电话</span><span class="value">{{ inv.address_phone || '-' }}</span></div>
              </div>
            </div>
          </div>
          <div v-else class="empty-text">暂无开票信息</div>
        </div>

        <!-- 收货地址 -->
        <div class="detail-section">
          <div class="section-title">收货地址</div>
          <div v-if="detail.shipping_addresses?.length">
            <div v-for="addr in detail.shipping_addresses" :key="addr.id" class="info-card">
              <span v-if="addr.is_default" class="default-badge">默认</span>
              <div class="detail-grid">
                <div class="detail-item"><span class="label">收货人</span><span class="value">{{ addr.receiver }}</span></div>
                <div class="detail-item"><span class="label">联系电话</span><span class="value">{{ addr.phone }}</span></div>
                <div class="detail-item"><span class="label">完整地址</span><span class="value">{{ [addr.province, addr.city, addr.district, addr.address].filter(Boolean).join('') }}</span></div>
              </div>
            </div>
          </div>
          <div v-else class="empty-text">暂无收货地址</div>
        </div>

        <!-- 订单汇总（预留） -->
        <div class="detail-section">
          <div class="section-title">订单汇总</div>
          <div class="empty-text">订单数据对接中，暂无可展示数据</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-footer">
        <template v-if="detail?.customer_status === 1">
          <button class="btn-primary" @click="handleEdit">编辑</button>
        </template>
        <template v-else-if="detail?.customer_status === 2">
          <button class="btn-primary" @click="handleClaim">认领</button>
        </template>
        <button class="btn-secondary" @click="close">关闭</button>
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
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.detail-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  background-color: var(--color-canvas);
  z-index: 1;
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
  gap: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-hairline);
  position: sticky;
  bottom: 0;
  background-color: var(--color-canvas);
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-hairline);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item .label {
  font-size: 12px;
  color: var(--color-muted);
}

.detail-item .value {
  font-size: 13px;
  color: var(--color-ink);
}

.detail-item .value.amount {
  font-weight: 600;
}

.text-danger {
  color: var(--color-danger);
  font-weight: 600;
}

.status-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: var(--radius-xs);
  font-size: 12px;
}

.status-tag.normal {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-tag.pool {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.info-card {
  background-color: var(--color-neutral-bg);
  border-radius: var(--radius-xs);
  padding: 12px;
  margin-bottom: 8px;
  position: relative;
}

.default-badge {
  position: absolute;
  top: 4px;
  right: 8px;
  background-color: var(--color-info-bg);
  color: var(--color-interactive);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-weight: 500;
}

.empty-text {
  color: var(--color-muted);
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.loading-text {
  text-align: center;
  padding: 40px;
  color: var(--color-muted);
}

.btn-secondary {
  padding: 10px 20px;
  border-radius: var(--radius-xs);
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
  border-radius: var(--radius-xs);
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
</style>