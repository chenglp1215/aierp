import { ref, computed } from 'vue'
import { provinceApi, type ProvinceCityData } from '../services/api'

const provinceCityCache = ref<ProvinceCityData | null>(null)
const isDataLoaded = ref(false)
const isLoading = ref(false)

export function useProvinceCity() {
  const loadProvinceCityData = async (): Promise<ProvinceCityData | null> => {
    if (isDataLoaded.value && provinceCityCache.value) {
      return provinceCityCache.value
    }

    if (isLoading.value) {
      return null
    }

    isLoading.value = true
    try {
      const res = await provinceApi.getAll()
      provinceCityCache.value = res
      isDataLoaded.value = true
      return provinceCityCache.value
    } catch (error) {
      console.error('加载省市数据失败:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  const getProvinces = (): { code: string; name: string }[] => {
    if (!provinceCityCache.value) return []
    return Object.entries(provinceCityCache.value).map(([name, data]) => ({
      name,
      code: data.code
    }))
  }

  const getCities = (provinceName: string): { code: string; name: string }[] => {
    if (!provinceCityCache.value || !provinceCityCache.value[provinceName]) return []
    const cities = provinceCityCache.value[provinceName].cities
    return Object.entries(cities).map(([name, data]) => ({
      name,
      code: data.code
    }))
  }

  const getDistricts = (provinceName: string, cityName: string): string[] => {
    if (!provinceCityCache.value || !provinceCityCache.value[provinceName]) return []
    const cityData = provinceCityCache.value[provinceName].cities[cityName]
    return cityData?.districts || []
  }

  const getCityCode = (provinceName: string, cityName: string): string => {
    if (!provinceCityCache.value || !provinceCityCache.value[provinceName]) return ''
    return provinceCityCache.value[provinceName].cities[cityName]?.code || ''
  }

  const getProvinceCode = (provinceName: string): string => {
    if (!provinceCityCache.value || !provinceCityCache.value[provinceName]) return ''
    return provinceCityCache.value[provinceName].code || ''
  }

  const clearCache = () => {
    provinceCityCache.value = null
    isDataLoaded.value = false
  }

  return {
    provinceCityData: computed(() => provinceCityCache.value),
    loadProvinceCityData,
    getProvinces,
    getCities,
    getDistricts,
    getCityCode,
    getProvinceCode,
    clearCache
  }
}
