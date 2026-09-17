import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
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
    meta: { title: '模型分析', adminOnly: true }
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
  },
  {
    path: '/lineage',
    name: 'DataLineage',
    component: () => import('@/views/DataLineage.vue'),
    meta: { title: '数据血缘', adminOnly: true }
  },
  {
    path: '/system',
    name: 'SystemStatus',
    component: () => import('@/views/SystemStatus.vue'),
    meta: { title: '系统状态', adminOnly: true }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/About.vue'),
    meta: { title: '关于项目', adminOnly: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫：登录态 + 管理员权限
router.beforeEach(async (to) => {
  const token = localStorage.getItem('used_car_token')
  const userStr = localStorage.getItem('used_car_user')
  let user = null
  try { user = userStr ? JSON.parse(userStr) : null } catch (e) { user = null }

  // 公开页（登录页）放行
  if (to.meta.public) {
    return token ? '/dashboard' : true
  }

  // 未登录 → 登录页
  if (!token || !user) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 管理员专属页校验
  if (to.meta.adminOnly && !user.is_staff) {
    return '/dashboard'
  }

  return true
})

export default router
