import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动附加 Token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('used_car_token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    // 401/403 且非登录接口：跳转登录
    if ((status === 401 || status === 403) && !error.config?.url?.includes('/auth/')) {
      localStorage.removeItem('used_car_token')
      localStorage.removeItem('used_car_user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    console.error('API Error:', error)
    ElMessage.error(error.response?.data?.message || error.message || '请求失败')
    return Promise.reject(error)
  }
)

// ============ 认证接口 ============
export const authLogin = (data) => request.post('/auth/login/', data)
export const authLogout = () => request.post('/auth/logout/')
export const authMe = () => request.get('/auth/me/')

// ============ 看板接口 ============
export const getDashboardSummary = () => request.get('/dashboard/summary/')

// ============ 统计接口 ============
export const getBrandPriceTop10 = () => request.get('/stat/brand-price/top10/')
export const getAgePriceChart = () => request.get('/stat/age-price/chart/')
export const getPriceDistributionChart = () => request.get('/stat/price-distribution/chart/')
export const getStatAggregate = (params) => request.get('/stat/aggregate/', { params })
export const getMarketCompare = (params) => request.get('/stat/market-compare/', { params })

// ============ 模型分析接口 ============
export const getModelAnalysis = () => request.get('/model/analysis/')

// ============ 模型训练（Celery 异步） ============
export const trainStart = () => request.post('/train/start/')
export const trainStatus = () => request.get('/train/status/')

// ============ 车辆接口 ============
export const getCarList = (params) => request.get('/cars/', { params })
export const getCarBrands = () => request.get('/cars/brands/')
export const getCarCities = () => request.get('/cars/cities/')
export const searchCars = (params) => request.get('/cars/search/', { params })

// ============ 预测接口 ============
export const predictPrice = (data) => request.post('/prediction/predict/', data)
export const getPredictionHistory = (params) => request.get('/prediction/history/', { params })
export const getModelInfo = () => request.get('/prediction/model-info/')

// ============ 健康检查 ============
export const healthCheck = () => request.get('/health/')

export default request
