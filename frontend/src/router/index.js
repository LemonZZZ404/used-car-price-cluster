import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据看板' }
  },
  {
    path: '/predict',
    name: 'Predict',
    component: () => import('@/views/Predict.vue'),
    meta: { title: '价格预测' }
  },
  {
    path: '/model-analysis',
    name: 'ModelAnalysis',
    component: () => import('@/views/ModelAnalysis.vue'),
    meta: { title: '模型分析' }
  },
  {
    path: '/cars',
    name: 'CarList',
    component: () => import('@/views/CarList.vue'),
    meta: { title: '车辆列表' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '预测历史' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
