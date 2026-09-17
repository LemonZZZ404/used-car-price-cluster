<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-icon">
          <el-icon :size="26"><Van /></el-icon>
        </div>
        <div class="logo-title">二手车价格评估系统</div>
        <div class="logo-sub">Big Data + Machine Learning Platform</div>
      </div>

      <!-- 角色切换：普通用户 / 管理员 -->
      <div class="role-switch">
        <div
          class="role-item"
          :class="{ active: role === 'user' }"
          @click="switchRole('user')"
        >
          <el-icon :size="16"><User /></el-icon>
          <span>普通用户</span>
        </div>
        <div
          class="role-item"
          :class="{ active: role === 'admin' }"
          @click="switchRole('admin')"
        >
          <el-icon :size="16"><Setting /></el-icon>
          <span>管理员</span>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tip">
        <el-alert :type="role === 'admin' ? 'warning' : 'info'" :closable="false" show-icon>
          <template #title>
            <div class="tip-text">
              <template v-if="role === 'admin'">
                管理员 <b>admin / 200412230</b>：全部功能，含
                <b>模型管理</b>（一键重训）与<b>大数据链路</b>（血缘/系统/项目）
              </template>
              <template v-else>
                普通用户 <b>user / 123456</b>：数据看板 / 价格预测 / 车辆列表 / 预测历史
              </template>
            </div>
          </template>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Van, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const role = ref('user')

const form = reactive({ username: 'user', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const switchRole = (r) => {
  if (role.value === r) return
  role.value = r
  form.username = r === 'admin' ? 'admin' : 'user'
  form.password = ''
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await userStore.login(form.username, form.password)
      if (res.code === 200) {
        ElMessage.success(`欢迎回来，${res.data.user.username}`)
        router.push('/dashboard')
      }
    } catch (e) { /* 错误提示由拦截器处理 */ }
    finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0F1E3A 0%, #16294D 50%, #1B3A6B 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before,
.login-page::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(45, 107, 255, 0.25), transparent 70%);
}

.login-page::before {
  width: 500px;
  height: 500px;
  top: -150px;
  right: -100px;
}

.login-page::after {
  width: 400px;
  height: 400px;
  bottom: -120px;
  left: -80px;
}

.login-card {
  width: 420px;
  max-width: calc(100vw - 40px);
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px 30px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.login-logo {
  text-align: center;
  margin-bottom: 24px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin: 0 auto 14px;
  box-shadow: 0 8px 20px rgba(45, 107, 255, 0.4);
}

.logo-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.logo-sub {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 6px;
  letter-spacing: 0.5px;
}

/* 角色切换 */
.role-switch {
  display: flex;
  background: #F3F4F6;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 22px;
}

.role-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.role-item.active {
  background: #fff;
  color: #2D6BFF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.role-item:not(.active):hover {
  color: #374151;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  background: linear-gradient(90deg, #2D6BFF, #4A7DFF);
  border: none;
}

.login-btn:hover {
  background: linear-gradient(90deg, #1B4FD8, #2D6BFF);
}

.login-tip {
  margin-top: 6px;
}

.tip-text {
  font-size: 12.5px;
  line-height: 1.8;
  color: #4B5563;
}
</style>
