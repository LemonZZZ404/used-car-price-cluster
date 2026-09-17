import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authLogin, authLogout, authMe } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('used_car_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('used_car_user') || 'null'))

  const isLogin = computed(() => !!token.value)
  const isAdmin = computed(() => !!user.value?.is_staff)

  const setAuth = (t, u) => {
    token.value = t
    user.value = u
    localStorage.setItem('used_car_token', t)
    localStorage.setItem('used_car_user', JSON.stringify(u))
  }

  const clearAuth = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('used_car_token')
    localStorage.removeItem('used_car_user')
  }

  const login = async (username, password) => {
    const res = await authLogin({ username, password })
    if (res.code === 200 && res.data) {
      setAuth(res.data.token, res.data.user)
    }
    return res
  }

  const logout = async () => {
    try { await authLogout() } catch (e) { /* 忽略 */ }
    clearAuth()
  }

  // 启动时校验 token 是否仍有效
  const restore = async () => {
    if (!token.value) return false
    try {
      const res = await authMe()
      if (res.code === 200 && res.data) {
        user.value = res.data
        localStorage.setItem('used_car_user', JSON.stringify(res.data))
        return true
      }
      clearAuth()
      return false
    } catch (e) {
      clearAuth()
      return false
    }
  }

  return { token, user, isLogin, isAdmin, login, logout, restore, setAuth, clearAuth }
})
