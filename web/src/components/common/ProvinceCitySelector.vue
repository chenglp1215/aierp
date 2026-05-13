<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useProvinceCity } from '../../hooks/useProvinceCity'

interface ProvinceOption {
  code: string
  name: string
}

interface CityOption {
  code: string
  name: string
}

interface Props {
  province?: string
  provinceCode?: string
  city?: string
  cityCode?: string
  placeholder?: {
    province?: string
    city?: string
  }
}

const props = withDefaults(defineProps<Props>(), {
  province: '',
  provinceCode: '',
  city: '',
  cityCode: '',
  placeholder: () => ({
    province: '请选择省份',
    city: '请选择城市'
  })
})

const emit = defineEmits<{
  (e: 'update:province', value: string): void
  (e: 'update:provinceCode', value: string): void
  (e: 'update:city', value: string): void
  (e: 'update:cityCode', value: string): void
}>()

const { loadProvinceCityData, getProvinces, getCities } = useProvinceCity()

const provinces = ref<ProvinceOption[]>([])
const cities = ref<CityOption[]>([])
const isDataReady = ref(false)

const selectedProvinceCode = ref(props.provinceCode || '')
const selectedCityCode = ref(props.cityCode || '')

const initData = async () => {
  const data = await loadProvinceCityData()
  if (data) {
    provinces.value = getProvinces()
    isDataReady.value = true
  }
}

const handleProvinceChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  selectedProvinceCode.value = target.value
  selectedCityCode.value = ''
  cities.value = []

  const province = provinces.value.find(p => p.code === target.value)
  const provinceName = province?.name || ''
  emit('update:province', provinceName)
  emit('update:provinceCode', target.value)
  emit('update:city', '')
  emit('update:cityCode', '')

  if (target.value) {
    cities.value = getCities(provinceName)
  }
}

const handleCityChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  selectedCityCode.value = target.value

  const city = cities.value.find(c => c.code === target.value)
  const provinceName = provinces.value.find(p => p.code === selectedProvinceCode.value)?.name || ''
  emit('update:province', provinceName)
  emit('update:provinceCode', selectedProvinceCode.value)
  emit('update:city', city?.name || '')
  emit('update:cityCode', target.value)
}

watch(() => props.provinceCode, async (newProvinceCode) => {
  if (newProvinceCode && newProvinceCode !== selectedProvinceCode.value) {
    selectedProvinceCode.value = newProvinceCode
    const provinceName = provinces.value.find(p => p.code === newProvinceCode)?.name || ''
    cities.value = provinceName ? getCities(provinceName) : []
    if (props.cityCode) {
      selectedCityCode.value = props.cityCode
    }
  }
})

onMounted(async () => {
  await initData()
  if (selectedProvinceCode.value && provinces.value.length > 0) {
    const provinceName = provinces.value.find(p => p.code === selectedProvinceCode.value)?.name || ''
    cities.value = provinceName ? getCities(provinceName) : []
  }
})

defineExpose({
  reset: () => {
    selectedProvinceCode.value = ''
    selectedCityCode.value = ''
    cities.value = []
    emit('update:province', '')
    emit('update:provinceCode', '')
    emit('update:city', '')
    emit('update:cityCode', '')
  }
})
</script>

<template>
  <div class="province-city-selector">
    <select
      class="province-select"
      :value="selectedProvinceCode"
      @change="handleProvinceChange"
    >
      <option value="">{{ placeholder.province }}</option>
      <option v-for="province in provinces" :key="province.code" :value="province.code">
        {{ province.name }}
      </option>
    </select>

    <select
      class="city-select"
      :value="selectedCityCode"
      @change="handleCityChange"
      :disabled="!selectedProvinceCode || !isDataReady"
    >
      <option value="">{{ placeholder.city }}</option>
      <option v-for="city in cities" :key="city.code" :value="city.code">
        {{ city.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.province-city-selector {
  display: flex;
  gap: 8px;
}

.province-select,
.city-select {
  flex: 1;
  padding: 10px 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  min-width: 0;
}

.province-select:focus,
.city-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.province-select:disabled,
.city-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.city-select:disabled {
  background-color: var(--bg-secondary);
}
</style>
