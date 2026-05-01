<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { provinceApi, type ProvinceInfo, type CityInfo } from '../../services/api'

interface Props {
  modelValue?: {
    province?: string
    provinceCode?: string
    city?: string
    cityCode?: string
  }
  placeholder?: {
    province?: string
    city?: string
  }
}

interface Emits {
  (e: 'update:modelValue', value: { province?: string; provinceCode?: string; city?: string; cityCode?: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  placeholder: () => ({
    province: '请选择省份',
    city: '请选择城市'
  })
})

const emit = defineEmits<Emits>()

const provinces = ref<ProvinceInfo[]>([])
const cities = ref<CityInfo[]>([])
const loadingProvinces = ref(false)
const loadingCities = ref(false)

const selectedProvinceCode = ref(props.modelValue?.provinceCode || '')
const selectedCityCode = ref(props.modelValue?.cityCode || '')

const selectedProvinceName = computed(() => {
  const province = provinces.value.find(p => p.code === selectedProvinceCode.value)
  return province?.name || ''
})

const loadProvinces = async () => {
  loadingProvinces.value = true
  try {
    const res = await provinceApi.getProvinces()
    provinces.value = res.result || []
  } catch (error) {
    console.error('加载省份失败:', error)
    provinces.value = []
  } finally {
    loadingProvinces.value = false
  }
}

const loadCities = async (provinceCode: string) => {
  if (!provinceCode) {
    cities.value = []
    return
  }

  loadingCities.value = true
  try {
    const provinceName = provinces.value.find(p => p.code === provinceCode)?.name || provinceCode
    const res = await provinceApi.getCities(provinceName)
    cities.value = res.result || []
  } catch (error) {
    console.error('加载城市失败:', error)
    cities.value = []
  } finally {
    loadingCities.value = false
  }
}

const handleProvinceChange = async (event: Event) => {
  const target = event.target as HTMLSelectElement
  selectedProvinceCode.value = target.value
  selectedCityCode.value = ''
  cities.value = []

  const province = provinces.value.find(p => p.code === target.value)
  emit('update:modelValue', {
    province: province?.name || '',
    provinceCode: target.value,
    city: '',
    cityCode: ''
  })

  if (target.value) {
    await loadCities(target.value)
  }
}

const handleCityChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  selectedCityCode.value = target.value

  const city = cities.value.find(c => c.code === target.value)
  emit('update:modelValue', {
    province: selectedProvinceName.value,
    provinceCode: selectedProvinceCode.value,
    city: city?.name || '',
    cityCode: target.value
  })
}

// Watch for external province changes to reload cities
watch(() => props.modelValue?.provinceCode, async (newProvinceCode) => {
  if (newProvinceCode && newProvinceCode !== selectedProvinceCode.value) {
    selectedProvinceCode.value = newProvinceCode
    await loadCities(newProvinceCode)
    if (props.modelValue?.cityCode) {
      selectedCityCode.value = props.modelValue.cityCode
    }
  }
})

onMounted(async () => {
  await loadProvinces()
  if (selectedProvinceCode.value) {
    await loadCities(selectedProvinceCode.value)
  }
})

// Expose methods for external control
defineExpose({
  reset: () => {
    selectedProvinceCode.value = ''
    selectedCityCode.value = ''
    cities.value = []
    emit('update:modelValue', {
      province: '',
      provinceCode: '',
      city: '',
      cityCode: ''
    })
  },
  setValues: (province: string, provinceCode: string, city: string, cityCode: string) => {
    selectedProvinceCode.value = provinceCode
    selectedCityCode.value = cityCode
    emit('update:modelValue', { province, provinceCode, city, cityCode })
  }
})
</script>

<template>
  <div class="province-city-selector">
    <select
      class="province-select"
      :value="selectedProvinceCode"
      @change="handleProvinceChange"
      :disabled="loadingProvinces"
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
      :disabled="!selectedProvinceCode || loadingCities"
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
