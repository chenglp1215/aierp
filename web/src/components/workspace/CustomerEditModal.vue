<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { customerApi, type InvoiceInfo, type ShippingAddress } from '../../services/api'
import ProvinceCitySelector from '../common/ProvinceCitySelector.vue'

const props = defineProps<{
  visible: boolean
  customerData: any | null
  mode: 'create' | 'edit'
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved', data?: any): void
}>()

const saving = ref(false)
const showAiPanel = ref(false)
const aiInputText = ref('')
const aiImageFiles = ref<File[]>([])
const aiImagePreviews = ref<string[]>([])
const aiParsing = ref(false)

const form = reactive({
  customer_name: '',
  customer_type: 'terminal' as 'terminal' | 'dealer',
  settlement_method: 1,
  contact_phone: '',
  contact_person: '',
  province: '',
  city: '',
  district: '',
  address: '',
  remark: ''
})

const researchGroup = reactive({
  research_group_name: '',
  research_leader: '',
  contact_phone: ''
})

const invoiceInfos = ref<InvoiceInfo[]>([])
const shippingAddresses = ref<ShippingAddress[]>([])

const showResearchGroup = computed(() => form.customer_type === 'terminal')
const isEditing = computed(() => props.mode === 'edit')

watch(() => props.visible, (val) => {
  if (val && props.mode === 'edit' && props.customerData) {
    Object.assign(form, {
      customer_name: props.customerData.customer_name || '',
      customer_type: props.customerData.customer_type || 'terminal',
      settlement_method: props.customerData.settlement_method ?? 1,
      contact_phone: props.customerData.contact_phone || '',
      contact_person: props.customerData.contact_person || '',
      province: props.customerData.province || '',
      city: props.customerData.city || '',
      district: props.customerData.district || '',
      address: props.customerData.address || '',
      remark: props.customerData.remark || ''
    })
    if (props.customerData.research_groups?.length > 0) {
      Object.assign(researchGroup, props.customerData.research_groups[0])
    }
    invoiceInfos.value = (props.customerData.invoice_infos || []).map((info: any) => ({
      ...info,
      address_phone: info.address_phone || null
    }))
    shippingAddresses.value = (props.customerData.shipping_addresses || []).map((addr: any) => ({
      ...addr,
      receiver: addr.receiver || addr.recipient_name || '',
      phone: addr.phone || addr.recipient_phone || ''
    }))
  } else if (val && props.mode === 'create') {
    Object.assign(form, {
      customer_name: '', customer_type: 'terminal',
      settlement_method: 1, contact_phone: '', contact_person: '',
      province: '', city: '', district: '', address: '', remark: ''
    })
    Object.assign(researchGroup, { research_group_name: '', research_leader: '', contact_phone: '' })
    invoiceInfos.value = []
    shippingAddresses.value = []
  }
})

const close = () => emit('update:visible', false)

const toggleAiPanel = () => {
  showAiPanel.value = !showAiPanel.value
  if (showAiPanel.value) {
    aiInputText.value = ''
    aiImageFiles.value = []
    aiImagePreviews.value = []
  }
}

// 处理多图选择
const handleAiImageSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files) return

  const newFiles = Array.from(input.files)
  // 最多 5 张
  if (aiImageFiles.value.length + newFiles.length > 5) {
    window.showToast('最多支持5张图片', 'warning')
    return
  }

  for (const file of newFiles) {
    // 单图 5MB 限制
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`图片 ${file.name} 超过5MB限制`, 'warning')
      continue
    }
    aiImageFiles.value.push(file)
    // 生成预览
    const reader = new FileReader()
    reader.onload = (e) => {
      aiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  // 重置 input 以支持重复选择同一文件
  input.value = ''
}

// 删除图片
const removeAiImage = (index: number) => {
  aiImageFiles.value.splice(index, 1)
  aiImagePreviews.value.splice(index, 1)
}

// 处理粘贴图片
const handleAiPaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  const imageFiles: File[] = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) imageFiles.push(file)
    }
  }

  if (imageFiles.length === 0) return

  // 有图片时阻止默认粘贴行为（避免图片文件名混入文本）
  event.preventDefault()

  if (aiImageFiles.value.length + imageFiles.length > 5) {
    window.showToast('最多支持5张图片', 'warning')
    return
  }

  for (const file of imageFiles) {
    if (file.size > 5 * 1024 * 1024) {
      window.showToast(`粘贴的图片超过5MB限制`, 'warning')
      continue
    }
    aiImageFiles.value.push(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      aiImagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  window.showToast(`已粘贴${imageFiles.length}张图片`, 'success')
}

// 将图片文件转为 base64（不含 data:image/...;base64, 前缀）
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      // 去除 data:image/xxx;base64, 前缀
      const base64 = dataUrl.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// 安全取字符串，排除 null/undefined/"null"
const safeStr = (v: any): string => {
  if (v === null || v === undefined) return ''
  const s = String(v).trim()
  return s === 'null' ? '' : s
}

// customer_type 兜底：中文→英文，非法值→terminal
const safeCustomerType = (v: any): 'terminal' | 'dealer' => {
  if (v === 'terminal' || v === 'dealer') return v
  const map: Record<string, 'terminal' | 'dealer'> = { '终端': 'terminal', '经销商': 'dealer' }
  return map[String(v)] || 'terminal'
}

// settlement_method 兜底：文字→数字，非法值→1
const safeSettlementMethod = (v: any): number => {
  if (typeof v === 'number' && [1, 2, 3].includes(v)) return v
  const map: Record<string, number> = { '月结': 1, '现结': 2, '预付': 3 }
  const n = Number(v)
  if (!isNaN(n) && [1, 2, 3].includes(n)) return n
  return map[String(v)] || 1
}

// AI 解析结果填充到表单
const fillFormWithAiResult = (result: any) => {
  if (!result) return

  const { customer, research_groups, invoice_info, shipping_address } = result

  // 填充基本信息
  if (customer) {
    if (customer.customer_name) form.customer_name = safeStr(customer.customer_name)
    if (customer.customer_type) form.customer_type = safeCustomerType(customer.customer_type)
    if (customer.contact_person) form.contact_person = safeStr(customer.contact_person)
    if (customer.contact_phone) form.contact_phone = safeStr(customer.contact_phone)
    if (customer.province) form.province = safeStr(customer.province)
    if (customer.city) form.city = safeStr(customer.city)
    if (customer.district) form.district = safeStr(customer.district)
    if (customer.address) form.address = safeStr(customer.address)
    if (customer.settlement_method) form.settlement_method = safeSettlementMethod(customer.settlement_method)
    if (customer.remark) form.remark = safeStr(customer.remark)
  }

  // 填充课题组（取第一个，仅终端客户）
  if (research_groups && research_groups.length > 0 && form.customer_type === 'terminal') {
    const group = research_groups[0]
    if (group.group_name) researchGroup.research_group_name = safeStr(group.group_name)
    if (group.contact_person) researchGroup.research_leader = safeStr(group.contact_person)
    if (group.contact_phone) researchGroup.contact_phone = safeStr(group.contact_phone)
  }

  // 填充开票信息
  if (invoice_info) {
    const invoice: InvoiceInfo = {
      invoice_title: safeStr(invoice_info.invoice_title),
      tax_number: safeStr(invoice_info.tax_number),
      bank_name: safeStr(invoice_info.bank_name),
      bank_account: safeStr(invoice_info.bank_account),
      address_phone: safeStr(invoice_info.address_phone) || null,
      is_default: true
    }
    if (invoiceInfos.value.length > 0) {
      invoiceInfos.value[0] = { ...invoiceInfos.value[0], ...invoice }
    } else {
      invoiceInfos.value = [invoice]
    }
  }

  // 填充收货地址
  if (shipping_address) {
    const addr: ShippingAddress = {
      receiver: safeStr(shipping_address.receiver),
      phone: safeStr(shipping_address.phone),
      province: safeStr(shipping_address.province),
      city: safeStr(shipping_address.city),
      district: safeStr(shipping_address.district),
      address: safeStr(shipping_address.address),
      is_default: true
    }
    if (shippingAddresses.value.length > 0) {
      shippingAddresses.value[0] = { ...shippingAddresses.value[0], ...addr }
    } else {
      shippingAddresses.value = [addr]
    }
  }
}

const handleAiSubmit = async () => {
  const hasText = aiInputText.value && aiInputText.value.trim()
  const hasImages = aiImageFiles.value.length > 0

  if (!hasText && !hasImages) {
    window.showToast('请输入文本描述或上传图片', 'warning')
    return
  }

  aiParsing.value = true
  try {
    // 将图片转为 base64
    const images: string[] = []
    for (const file of aiImageFiles.value) {
      const base64 = await fileToBase64(file)
      images.push(base64)
    }

    // 调用 AI 解析接口
    const result = await customerApi.parseByAi({
      text: hasText ? aiInputText.value.trim() : undefined,
      images: images.length > 0 ? images : undefined,
    })

    // 填充表单
    fillFormWithAiResult(result)
    showAiPanel.value = false
    window.showToast('AI解析完成，请核对并补充信息', 'success')
  } catch (error: any) {
    const msg = error?.message || 'AI解析失败，请重试或手动填写'
    window.showToast(msg, 'error')
  } finally {
    aiParsing.value = false
  }
}

const addInvoiceInfo = () => {
  invoiceInfos.value.push({
    invoice_title: '',
    tax_number: '',
    bank_name: '',
    bank_account: '',
    address_phone: null,
    is_default: invoiceInfos.value.length === 0
  })
}

const removeInvoiceInfo = (index: number) => {
  const wasDefault = invoiceInfos.value[index].is_default
  invoiceInfos.value.splice(index, 1)
  if (invoiceInfos.value.length > 0 && (wasDefault || !invoiceInfos.value.some(i => i.is_default))) {
    invoiceInfos.value[0].is_default = true
  }
}

const setDefaultInvoice = (index: number) => {
  invoiceInfos.value.forEach((info, i) => {
    info.is_default = i === index
  })
}

const addShippingAddress = () => {
  shippingAddresses.value.push({
    receiver: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    address: '',
    is_default: shippingAddresses.value.length === 0
  })
}

const removeShippingAddress = (index: number) => {
  const wasDefault = shippingAddresses.value[index].is_default
  shippingAddresses.value.splice(index, 1)
  if (shippingAddresses.value.length > 0 && (wasDefault || !shippingAddresses.value.some(a => a.is_default))) {
    shippingAddresses.value[0].is_default = true
  }
}

const setDefaultAddress = (index: number) => {
  shippingAddresses.value.forEach((addr, i) => {
    addr.is_default = i === index
  })
}

const validateForm = (): boolean => {
  if (!form.customer_name.trim()) {
    window.showToast('请输入客户名称', 'warning')
    return false
  }
  if (!form.customer_type) {
    window.showToast('请选择客户类型', 'warning')
    return false
  }
  if (showResearchGroup.value) {
    if (!researchGroup.research_group_name.trim()) {
      window.showToast('请输入课题组名称', 'warning')
      return false
    }
    if (!researchGroup.research_leader.trim()) {
      window.showToast('请输入课题组负责人', 'warning')
      return false
    }
    if (!researchGroup.contact_phone.trim()) {
      window.showToast('请输入负责人电话', 'warning')
      return false
    }
  }
  return true
}

const handleSave = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    const customerData: any = {
      customer_name: form.customer_name.trim(),
      customer_type: form.customer_type,
      settlement_method: form.settlement_method,
      contact_person: form.contact_person?.trim() || undefined,
      contact_phone: form.contact_phone?.trim() || undefined,
      province: form.province || undefined,
      city: form.city || undefined,
      district: form.district || undefined,
      address: form.address || undefined,
      remark: form.remark || undefined,
      invoice_infos: invoiceInfos.value.map((info) => ({
        id: info.id || undefined,
        invoice_title: info.invoice_title,
        tax_number: info.tax_number,
        bank_name: info.bank_name,
        bank_account: info.bank_account,
        address_phone: info.address_phone || undefined,
        is_default: info.is_default === true
      })),
      shipping_addresses: shippingAddresses.value.map((addr) => ({
        id: addr.id || undefined,
        receiver: addr.receiver,
        phone: addr.phone,
        province: addr.province || '',
        city: addr.city || '',
        district: addr.district || '',
        address: addr.address || '',
        is_default: addr.is_default === true
      }))
    }

    if (form.customer_type === 'terminal') {
      customerData.research_groups = [{ ...researchGroup }]
    }

    if (isEditing.value && props.customerData) {
      await customerApi.update(String(props.customerData.id), customerData)
      window.showToast('客户更新成功', 'success')
      emit('saved', { ...customerData, id: props.customerData.id })
    } else {
      await customerApi.create(customerData)
      window.showToast('客户创建成功', 'success')
      emit('saved')
    }
    close()
  } catch (error: any) {
    window.showToast(error.message || '操作失败', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" v-if="visible" @click.self="close">
    <div class="modal customer-modal">
      <div class="modal-header">
        <div class="modal-header-left">
          <h3>{{ isEditing ? '编辑客户' : '新建客户' }}</h3>
          <button v-if="!isEditing" class="ai-btn" @click="toggleAiPanel" :class="{ active: showAiPanel }">
            AI
          </button>
        </div>
        <button class="modal-close" @click="close">&times;</button>
      </div>

      <!-- AI 智能解析面板 -->
      <div class="ai-panel" v-if="showAiPanel && !isEditing">
        <div class="ai-panel-header">
          <span class="ai-panel-title">AI 智能解析</span>
          <button class="btn-link" @click="showAiPanel = false" :disabled="aiParsing">收起</button>
        </div>

        <!-- 解析中状态 -->
        <div class="ai-thinking" v-if="aiParsing">
          <div class="ai-thinking-animation">
            <div class="ai-thinking-dot"></div>
            <div class="ai-thinking-dot"></div>
            <div class="ai-thinking-dot"></div>
          </div>
          <div class="ai-thinking-text">
            <span class="ai-thinking-label">Thinking</span>
            <span class="ai-thinking-ellipsis">
              <span class="ai-ellipsis-dot">.</span>
              <span class="ai-ellipsis-dot">.</span>
              <span class="ai-ellipsis-dot">.</span>
            </span>
          </div>
          <p class="ai-thinking-hint">AI 正在解析客户信息，请稍候</p>
        </div>

        <!-- 正常输入状态 -->
        <div class="ai-panel-body" v-else>
          <!-- 文本输入 -->
          <div class="ai-section">
            <label class="ai-label">文本描述</label>
            <textarea
              v-model="aiInputText"
              class="ai-textarea"
              placeholder="粘贴客户信息，或直接 Ctrl+V 粘贴图片..."
              rows="4"
              @paste="handleAiPaste"
            ></textarea>
          </div>
          <!-- 图片上传 -->
          <div class="ai-section">
            <label class="ai-label">图片（最多5张）</label>
            <div class="ai-image-upload-area">
              <div class="ai-image-list">
                <div
                  v-for="(preview, index) in aiImagePreviews"
                  :key="index"
                  class="ai-image-item"
                >
                  <img :src="preview" alt="预览" class="ai-image-preview" />
                  <button class="ai-image-remove" @click="removeAiImage(index)" title="删除">&times;</button>
                </div>
                <!-- 添加按钮（未满5张时显示） -->
                <label v-if="aiImageFiles.length < 5" class="ai-image-add">
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    class="ai-file-input"
                    @change="handleAiImageSelect"
                  />
                  <span class="ai-image-add-icon">+</span>
                  <span class="ai-image-add-text">上传图片</span>
                </label>
              </div>
              <p class="ai-image-hint">支持名片、营业执照等，最多5张，单张不超过5MB</p>
            </div>
          </div>
          <!-- 提交按钮 -->
          <div class="ai-actions">
            <button class="btn-primary" @click="handleAiSubmit" :disabled="!aiInputText?.trim() && aiImageFiles.length === 0">
              AI 解析
            </button>
            <button class="btn-secondary" @click="toggleAiPanel">取消</button>
          </div>
        </div>
      </div>

      <div class="modal-body" v-else>
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="section-title">基本信息</div>
          <div class="form-row">
            <div class="form-group">
              <label>客户名称 <span class="required">*</span></label>
              <input type="text" v-model="form.customer_name" placeholder="请输入客户名称" />
            </div>
            <div class="form-group">
              <label>客户类型 <span class="required">*</span></label>
              <select v-model="form.customer_type">
                <option value="terminal">终端</option>
                <option value="dealer">经销商</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>结算方式</label>
              <select v-model="form.settlement_method">
                <option :value="1">月结</option>
                <option :value="2">现结</option>
                <option :value="3">预付</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 联系方式 -->
        <div class="form-section">
          <div class="section-title">联系方式</div>
          <div class="form-row">
            <div class="form-group">
              <label>联系电话</label>
              <input type="text" v-model="form.contact_phone" placeholder="请输入联系电话" />
            </div>
            <div class="form-group">
              <label>联系人</label>
              <input type="text" v-model="form.contact_person" placeholder="请输入联系人" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>省</label>
              <input type="text" v-model="form.province" placeholder="省" />
            </div>
            <div class="form-group">
              <label>市</label>
              <input type="text" v-model="form.city" placeholder="市" />
            </div>
            <div class="form-group">
              <label>区</label>
              <input type="text" v-model="form.district" placeholder="区" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>详细地址</label>
              <input type="text" v-model="form.address" placeholder="请输入详细地址" />
            </div>
          </div>
        </div>

        <!-- 课题组信息（终端客户时显示） -->
        <div class="form-section" v-if="showResearchGroup">
          <div class="section-title">课题组信息</div>
          <div class="form-row">
            <div class="form-group">
          <label>课题组名称 <span class="required">*</span></label>
              <input type="text" v-model="researchGroup.research_group_name" placeholder="请输入课题组名称" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>负责人 <span class="required">*</span></label>
              <input type="text" v-model="researchGroup.research_leader" placeholder="请输入负责人" />
            </div>
            <div class="form-group">
              <label>联系电话 <span class="required">*</span></label>
              <input type="text" v-model="researchGroup.contact_phone" placeholder="请输入联系电话" />
            </div>
          </div>
        </div>

        <!-- 开票信息 -->
        <div class="form-section">
          <div class="section-title">
            <span>开票信息</span>
            <button class="btn-link add-btn" @click="addInvoiceInfo">+ 添加</button>
          </div>
          <div class="info-table" v-if="invoiceInfos.length > 0">
            <div class="info-table-header">
              <div class="info-th" style="flex: 2;">开票抬头</div>
              <div class="info-th" style="flex: 1.5;">税务编码</div>
              <div class="info-th" style="flex: 1.5;">开户银行</div>
              <div class="info-th" style="flex: 1.5;">银行账号</div>
              <div class="info-th" style="flex: 1.5;">地址电话</div>
              <div class="info-th" style="width: 120px;">操作</div>
            </div>
            <div class="info-table-body">
              <div
                class="info-tr"
                :class="{ 'is-default': info.is_default }"
                v-for="(info, idx) in invoiceInfos"
                :key="idx"
              >
                <div class="info-td" style="flex: 2;">
                  <input type="text" v-model="info.invoice_title" placeholder="开票抬头" />
                </div>
                <div class="info-td" style="flex: 1.5;">
                  <input type="text" v-model="info.tax_number" placeholder="税务编码" />
                </div>
                <div class="info-td" style="flex: 1.5;">
                  <input type="text" v-model="info.bank_name" placeholder="开户银行" />
                </div>
                <div class="info-td" style="flex: 1.5;">
                  <input type="text" v-model="info.bank_account" placeholder="银行账号" />
                </div>
                <div class="info-td" style="flex: 1.5;">
                  <input type="text" v-model="info.address_phone" placeholder="地址、电话" />
                </div>
                <div class="info-td" style="width: 120px; display: flex; gap: 4px;">
                  <button class="btn-link" @click="setDefaultInvoice(idx)" v-if="!info.is_default">设默认</button>
                  <button class="btn-link danger" @click="removeInvoiceInfo(idx)" v-if="invoiceInfos.length > 1">删除</button>
                </div>
              </div>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无开票信息</div>
        </div>

        <!-- 收货地址 -->
        <div class="form-section">
          <div class="section-title">
            <span>收货地址</span>
            <button class="btn-link add-btn" @click="addShippingAddress">+ 添加</button>
          </div>
          <div class="info-table" v-if="shippingAddresses.length > 0">
            <div class="info-table-header">
              <div class="info-th" style="flex: 1;">收货人</div>
              <div class="info-th" style="flex: 1.2;">联系电话</div>
              <div class="info-th" style="flex: 1;">省份</div>
              <div class="info-th" style="flex: 1;">城市</div>
              <div class="info-th" style="flex: 2;">详细地址</div>
              <div class="info-th" style="width: 120px;">操作</div>
            </div>
            <div class="info-table-body">
              <div
                class="info-tr"
                :class="{ 'is-default': addr.is_default }"
                v-for="(addr, idx) in shippingAddresses"
                :key="idx"
              >
                <div class="info-td" style="flex: 1;">
                  <input type="text" v-model="addr.receiver" placeholder="收货人" />
                </div>
                <div class="info-td" style="flex: 1.2;">
                  <input type="text" v-model="addr.phone" placeholder="联系电话" />
                </div>
                <div class="info-td" style="flex: 1;">
                  <ProvinceCitySelector
                    v-model:province="addr.province"
                    v-model:city="addr.city"
                  />
                </div>
                <div class="info-td" style="flex: 2;">
                  <input type="text" v-model="addr.address" placeholder="详细地址" />
                </div>
                <div class="info-td" style="width: 120px; display: flex; gap: 4px;">
                  <button class="btn-link" @click="setDefaultAddress(idx)" v-if="!addr.is_default">设默认</button>
                  <button class="btn-link danger" @click="removeShippingAddress(idx)" v-if="shippingAddresses.length > 1">删除</button>
                </div>
              </div>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无收货地址</div>
        </div>

        <!-- 备注 -->
        <div class="form-section">
          <div class="section-title">备注</div>
          <textarea v-model="form.remark" rows="3" placeholder="请输入备注"></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
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
  background-color: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.customer-modal {
  max-width: 900px;
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

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.ai-btn {
  padding: 6px 12px;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-xs);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ai-btn:hover {
  opacity: 0.9;
}

.ai-btn.active {
  box-shadow: 0 0 0 2px var(--color-accent-soft);
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

.ai-panel {
  padding: 20px;
  background-color: var(--color-neutral-bg);
  border-bottom: 1px solid var(--color-hairline);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.ai-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ai-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.ai-panel-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ai-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
}

.ai-textarea {
  width: 100%;
  padding: 12px;
  background-color: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.ai-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.ai-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-image-upload-area {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-image-item {
  position: relative;
  width: 80px;
  height: 80px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.ai-image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-image-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  min-width: 20px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  color: #fff;
  border: none;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.ai-image-remove:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

.ai-image-remove:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-image-add {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-xs);
  cursor: pointer;
  color: var(--color-muted);
  transition: all var(--transition-fast);
}

.ai-image-add:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.ai-file-input {
  display: none;
}

.ai-image-add-icon {
  font-size: 24px;
  line-height: 1;
}

.ai-image-add-text {
  font-size: 11px;
  margin-top: 2px;
}

.ai-image-hint {
  font-size: 12px;
  color: var(--color-muted);
  margin: 0;
}

.ai-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
}

/* AI Thinking 动画 */
.ai-thinking {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 16px;
}

.ai-thinking-animation {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ai-thinking-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--color-accent);
  animation: aiDotPulse 1.4s ease-in-out infinite;
}

.ai-thinking-dot:nth-child(1) {
  animation-delay: 0s;
}

.ai-thinking-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.ai-thinking-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes aiDotPulse {
  0%, 80%, 100% {
    transform: scale(0.4);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.ai-thinking-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.ai-thinking-label {
  color: var(--color-accent);
}

.ai-thinking-ellipsis {
  display: inline-flex;
  overflow: hidden;
}

.ai-ellipsis-dot {
  animation: aiEllipsis 1.4s infinite;
  opacity: 0;
}

.ai-ellipsis-dot:nth-child(1) {
  animation-delay: 0s;
}

.ai-ellipsis-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.ai-ellipsis-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes aiEllipsis {
  0% { opacity: 0; }
  40% { opacity: 1; }
  80%, 100% { opacity: 0; }
}

.ai-thinking-hint {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
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

.form-section {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-row:has(> .form-group:nth-child(3)) {
  grid-template-columns: repeat(3, 1fr);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-muted);
}

.form-group .required {
  color: var(--color-danger);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--color-muted);
}

.info-table {
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.info-table-header {
  display: flex;
  background-color: var(--color-neutral-bg);
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-hairline);
}

.info-th {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  padding: 0 8px;
}

.info-table-body {
  max-height: 200px;
  overflow-y: auto;
}

.info-tr {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-hairline);
}

.info-tr:last-child {
  border-bottom: none;
}

.info-tr:hover {
  background-color: var(--color-info-bg);
}

.info-tr.is-default {
  background-color: var(--color-info-bg);
  border-left: 3px solid var(--color-interactive);
}

.info-tr.is-default:hover {
  background-color: var(--color-info-bg);
}

.info-td {
  padding: 0 8px;
}

.info-td input,
.info-td select {
  width: 100%;
  padding: 6px 8px;
  background-color: var(--color-neutral-bg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  color: var(--color-ink);
  font-size: 13px;
}

.info-td input:focus,
.info-td select:focus {
  outline: none;
  border-color: var(--color-interactive);
}

.info-td input::placeholder {
  color: var(--color-muted);
  font-size: 12px;
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: var(--color-muted);
  font-size: 13px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-interactive);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-xs);
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-link:hover {
  background-color: var(--color-info-bg);
}

.btn-link.danger {
  color: var(--color-danger);
}

.btn-link.danger:hover {
  background-color: var(--color-danger-bg);
}

.btn-link.add-btn {
  font-size: 12px;
  padding: 2px 8px;
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal {
    width: 95%;
    margin: 16px;
  }
}
</style>