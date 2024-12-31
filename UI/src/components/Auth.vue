<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="tabs">
        <button
          :class="{ active: isLogin }"
          @click="isLogin = true"
        >
          登录
        </button>
        <button
          :class="{ active: !isLogin }"
          @click="isLogin = false"
        >
          注册
        </button>
      </div>

      <!-- 登录表单 -->
      <form v-if="isLogin" @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            type="text"
            v-model="loginForm.username"
            required
            placeholder="请输入用户名"
          >
        </div>
        <div class="form-group">
          <label>密码</label>
          <input
            type="password"
            v-model="loginForm.password"
            required
            placeholder="请输入密码"
          >
        </div>
        <div v-if="loginError" class="error-message">{{ loginError }}</div>
        <button
          type="submit"
          :disabled="loading"
          :class="{ 'button-active': loginForm.username && loginForm.password && !loading }"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            type="text"
            v-model="registerForm.username"
            required
            placeholder="至少6位，只能包含字母、数字和下划线"
            @input="checkUsername"
          >
          <span v-if="usernameError" class="field-error">{{ usernameError }}</span>
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input
            type="email"
            v-model="registerForm.email"
            required
            placeholder="请输入有效的邮箱地址"
            @input="checkEmail"
          >
          <span v-if="emailError" class="field-error">{{ emailError }}</span>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input
            type="password"
            v-model="registerForm.password"
            required
            placeholder="至少6位"
          >
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input
            type="password"
            v-model="registerForm.confirmPassword"
            required
            placeholder="请再次输入密码"
          >
          <span v-if="passwordError" class="field-error">{{ passwordError }}</span>
        </div>
        <div v-if="registerError" class="error-message">{{ registerError }}</div>
        <button
          type="submit"
          :disabled="loading || !isRegisterFormValid"
          :class="{ 'button-active': isRegisterFormValid && !loading }"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debounce } from 'lodash'

export default {
  name: 'Auth',
  data () {
    return {
      isLogin: true,
      loading: false,
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      loginError: '',
      registerError: '',
      usernameError: '',
      emailError: '',
      passwordError: ''
    }
  },
  computed: {
    isRegisterFormValid () {
      return this.registerForm.username &&
             this.registerForm.email &&
             this.registerForm.password &&
             this.registerForm.confirmPassword &&
             !this.usernameError &&
             !this.emailError &&
             !this.passwordError
    }
  },
  watch: {
    'registerForm.confirmPassword': {
      handler (newVal) {
        if (!newVal || !this.registerForm.password) {
          this.passwordError = ''
        } else if (newVal !== this.registerForm.password) {
          this.passwordError = '两次输入的密码不一致'
        } else {
          this.passwordError = ''
        }
      },
      immediate: true
    },
    'registerForm.password': {
      handler (newVal) {
        if (!newVal || !this.registerForm.confirmPassword) {
          this.passwordError = ''
        } else if (newVal !== this.registerForm.confirmPassword) {
          this.passwordError = '两次输入的密码不一致'
        } else {
          this.passwordError = ''
        }
      },
      immediate: true
    }
  },
  methods: {
    // 使用 debounce 防止频繁请求
    checkUsername: debounce(async function () {
      if (!this.registerForm.username) {
        this.usernameError = ''
        return
      }

      // 检查用户名格式
      if (!/^[a-zA-Z0-9_]{6,}$/.test(this.registerForm.username)) {
        this.usernameError = '用户名必须至少6位，只能包含字母、数字和下划线'
        return
      }

      try {
        const response = await axios.get(`http://localhost:5000/api/auth/check_username/${this.registerForm.username}`)
        if (response.data.exists) {
          this.usernameError = '该用户名已被使用'
        } else {
          this.usernameError = ''
        }
      } catch (error) {
        console.error('检查用户名失败:', error)
      }
    }, 500),

    // 使用 debounce 防止频繁请求
    checkEmail: debounce(async function () {
      if (!this.registerForm.email) {
        this.emailError = ''
        return
      }

      // 检查邮箱格式
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.registerForm.email)) {
        this.emailError = '请输入有效的邮箱地址'
        return
      }

      try {
        const response = await axios.get(`http://localhost:5000/api/auth/check_email/${this.registerForm.email}`)
        if (response.data.exists) {
          this.emailError = '该邮箱已被使用'
        } else {
          this.emailError = ''
        }
      } catch (error) {
        console.error('检查邮箱失败:', error)
      }
    }, 500),

    async handleLogin () {
      this.loading = true
      this.loginError = ''

      try {
        const response = await axios.post('http://localhost:5000/api/auth/login', {
          username: this.loginForm.username,
          password: this.loginForm.password
        })

        if (response.data.status === 'success') {
          // 保存token
          localStorage.setItem('auth_token', response.data.token)
          // 跳转到主页
          this.$router.push({ name: 'MultiSearch' })
        }
      } catch (error) {
        this.loginError = (error.response && error.response.data && error.response.data.detail) || '登录失败，请重试'
      } finally {
        this.loading = false
      }
    },

    async handleRegister () {
      // 如果有错误，不允许提交
      if (this.usernameError || this.emailError || this.passwordError) {
        return
      }

      this.loading = true
      this.registerError = ''

      try {
        const response = await axios.post('http://localhost:5000/api/auth/register', {
          username: this.registerForm.username,
          email: this.registerForm.email,
          password: this.registerForm.password
        })

        if (response.data.status === 'success') {
          // 保存token
          localStorage.setItem('auth_token', response.data.token)
          // 跳转到主页
          this.$router.push({ name: 'MultiSearch' })
        }
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          this.registerError = error.response.data.detail
        } else {
          this.registerError = '注册失败，请重试'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.auth-box {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.tabs button {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #666;
}

.tabs button.active {
  color: #1890ff;
  border-bottom: 2px solid #1890ff;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 14px;
  color: #333;
}

.form-group input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 5px;
}

.field-error {
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 2px;
}

button[type="submit"] {
  padding: 10px;
  background: #d9d9d9;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

button[type="submit"].button-active {
  background: #1890ff;
  cursor: pointer;
}

button[type="submit"].button-active:hover {
  background: #40a9ff;
}

button[type="submit"]:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}
</style>
