<template>
  <div>
    <div class="main-container">
      <div class="platform-switch">
        <button :class="{ active: currentPlatform === 'taobao' }" @click="switchPlatform('taobao')">淘宝</button>
        <button :class="{ active: currentPlatform === 'jd' }" @click="switchPlatform('jd')">京东</button>
      </div>
      <div class="container" v-if="currentPlatform === 'taobao'">
        <h1>淘宝商品搜索</h1>
        <div v-if="isLoggedIn" class="login-status logged-in">已登录</div>
        <div v-else class="login-status logged-out">未登录，请先登录淘宝</div>
        <div class="search-bar">
          <input
            type="text"
            v-model="keyword"
            placeholder="输入商品关键词"
            @keyup.enter="searchTaobao"
          />
          <div class="button-container">
            <button @click="searchTaobao" :disabled="!isLoggedIn">搜索</button>
          </div>
        </div>
        <div class="buttons">
          <div v-if="!isLoggedIn">
            <button @click="loginTaobao">登录</button>
          </div>
          <button @click="clearResults">清除结果</button>
        </div>
        <!-- 搜索结果展示区域 -->
        <div class="response-area">
          <div v-if="loading">搜索中...</div>
          <div v-else>
            <p v-if="error" class="error">{{ error }}</p>
            <div v-else-if="searchResults" class="search-results">
              <div v-if="typeof searchResults === 'string'" v-html="searchResults"></div>
              <div v-else class="results-grid">
                <div v-for="(item, index) in searchResults" :key="item.id || index" class="result-item">
                  <div class="item-image">
                    <img :src="item.image_url" :alt="item.title">
                  </div>
                  <div class="item-info">
                    <h3 class="item-title">{{ item.title }}</h3>
                    <p class="item-price">¥{{ item.price }}</p>
                    <p class="item-sales">销量: {{ item.sales }}</p>
                    <p class="item-shop">{{ item.shop_name }}</p>
                    <p class="item-location">{{ item.location }}</p>
                    <a :href="item.item_url" target="_blank" class="item-link">查看详情</a>
                  </div>
                </div>
              </div>
              <div class="pagination">
                <button @click="prevPage" :disabled="currentPage <= 1">上一页</button>
                <span>第 {{ currentPage }} 页</span>
                <button @click="nextPage">下一页</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="container" v-else>
        <h1>京东商品搜索</h1>
        <div v-if="isJdLoggedIn" class="login-status logged-in">已登录</div>
        <div v-else class="login-status logged-out">未登录，请先登录京东</div>
        <div class="search-bar">
          <input
            type="text"
            v-model="jdKeyword"
            placeholder="输入商品关键词"
            @keyup.enter="searchJd"
          />
          <div class="button-container">
            <button @click="searchJd" :disabled="!isJdLoggedIn">搜索</button>
          </div>
        </div>
        <div class="buttons">
          <div v-if="!isJdLoggedIn">
            <button @click="loginJd">登录</button>
          </div>
          <button @click="clearJdResults">清除结果</button>
        </div>
        <!-- 京东搜索结果展示区域 -->
        <div class="response-area">
          <div v-if="jdLoading">搜索中...</div>
          <div v-else>
            <p v-if="jdError" class="error">{{ jdError }}</p>
            <div v-else-if="jdSearchResults" class="search-results">
              <div v-if="typeof jdSearchResults === 'string'" v-html="jdSearchResults"></div>
              <div v-else class="results-grid">
                <div v-for="(item, index) in jdSearchResults" :key="item.id || index" class="result-item">
                  <div class="item-image">
                    <img :src="item.image_url" :alt="item.title">
                  </div>
                  <div class="item-info">
                    <h3 class="item-title">{{ item.title }}</h3>
                    <p class="item-price">¥{{ item.price }}</p>
                    <p class="item-sales">销量: {{ item.sales }}</p>
                    <p class="item-shop">{{ item.shop_name }}</p>
                    <a :href="item.item_url" target="_blank" class="item-link">查看详情</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 淘宝二维码模态框 -->
    <div v-if="showQrCode" class="qr-code-modal">
      <div class="qr-code-container">
        <h2>请使用淘宝APP扫描二维码登录</h2>
        <img :src="qrCode" alt="淘宝登录二维码" />
        <button @click="showQrCode = false">关闭</button>
      </div>
    </div>

    <!-- 京东二维码模态框 -->
    <div v-if="jdShowQrCode" class="qr-code-modal">
      <div class="qr-code-container">
        <h2>请使用京东APP扫描二维码登录</h2>
        <img :src="jdQrCode" alt="京东登录二维码" />
        <button @click="jdShowQrCode = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'HelloWorld',
  data () {
    return {
      currentPlatform: 'taobao',
      // 淘宝相关数据
      keyword: '',
      searchResults: null,
      error: null,
      loading: false,
      showQrCode: false,
      qrCode: null,
      sessionId: null,
      clientId: localStorage.getItem('taobao_client_id'),
      needLogin: false,
      checkLoginInterval: null,
      currentPage: 1,
      debug: false,
      // 京东相关数据
      jdKeyword: '',
      jdSearchResults: null,
      jdError: null,
      jdLoading: false,
      jdShowQrCode: false,
      jdQrCode: null,
      jdSessionId: null,
      jdClientId: localStorage.getItem('jd_client_id'),
      jdNeedLogin: false,
      jdCheckLoginInterval: null,
      jdCurrentPage: 1
    }
  },
  computed: {
    isLoggedIn () {
      return !!this.clientId
    },
    isJdLoggedIn () {
      return !!this.jdClientId
    }
  },
  methods: {
    switchPlatform (platform) {
      // 如果当前有搜索操作正在进行，先将其标记为完成
      this.loading = false
      this.jdLoading = false
      // 清除搜索结果和错误信息
      if (platform === 'taobao') {
        this.clearResults()
        this.jdSearchResults = null
        this.jdError = null
      } else {
        this.clearJdResults()
        this.searchResults = null
        this.error = null
      }
      // 最后切换平台
      this.currentPlatform = platform
    },
    async loginTaobao () {
      try {
        const response = await axios.get('http://localhost:5000/api/taobao/get_qr_code')
        if (response.data.status === 'success') {
          this.sessionId = response.data.data.session_id
          this.qrCode = response.data.data.qr_code
          this.showQrCode = true
          let retryCount = 0
          const maxRetries = 30 // 最多尝试30次，即60秒
          let accountSet = false // 标记是否已经设置过账号
          // 开始轮询检查登录状态
          this.checkLoginInterval = setInterval(async () => {
            try {
              retryCount++
              if (retryCount >= maxRetries) {
                clearInterval(this.checkLoginInterval)
                this.showQrCode = false
                this.error = '登录超时，请重试'
                return
              }
              const statusResponse = await axios.post('http://localhost:5000/api/taobao/check_login', {
                session_id: this.sessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                // 登录成功且未设置过账号，停止轮询
                clearInterval(this.checkLoginInterval)
                this.showQrCode = false
                // 设置账号（只执行一次）
                try {
                  const accountResponse = await axios.post('http://localhost:5000/api/taobao/SetAccount', {
                    message: 'new_session',
                    session_id: this.sessionId
                  })
                  if (accountResponse.data.status === 'success') {
                    accountSet = true // 标记已设置账号
                    this.clientId = accountResponse.data.client_id
                    localStorage.setItem('taobao_client_id', accountResponse.data.client_id)
                    this.error = null
                  }
                } catch (error) {
                  console.error('设置淘宝账号失败:', error)
                  this.error = '设置账号失败，请重试'
                }
              } else if (statusResponse.data.status === 'error') {
                clearInterval(this.checkLoginInterval)
                this.showQrCode = false
                this.error = statusResponse.data.message
              }
            } catch (error) {
              console.error('检查淘宝登录状态错误:', error)
              clearInterval(this.checkLoginInterval)
              this.showQrCode = false
              this.error = '登录失败，请重试'
            }
          }, 2000)
        } else {
          this.error = response.data.message || '获取二维码失败'
        }
      } catch (error) {
        console.error('淘宝登录错误:', error)
        this.error = '登录失败，请重试'
      }
    },
    async searchTaobao () {
      if (!this.keyword.trim()) {
        this.error = '请输入搜索关键词'
        return
      }
      if (!this.clientId) {
        this.error = '请先登录淘宝'
        this.needLogin = true
        return
      }
      this.loading = true
      this.error = null
      this.needLogin = false
      try {
        console.log('发送搜索请求:', { keyword: this.keyword, page: this.currentPage, clientId: this.clientId })
        const response = await axios.post('http://localhost:5000/api/taobao/search_taobao', { keyword: this.keyword, page: this.currentPage }, { headers: { 'X-Client-ID': this.clientId, 'Content-Type': 'application/json' } })
        console.log('搜索响应:', response.data)
        if (response.data && response.data.status === 'success') {
          this.searchResults = response.data.data
          this.error = null
        } else if (response.data) {
          this.error = response.data.message || '搜索失败'
          this.needLogin = response.data.code === 'LOGIN_REQUIRED' || response.data.code === 'LOGIN_EXPIRED'
          if (this.needLogin) {
            localStorage.removeItem('taobao_client_id')
            this.clientId = null
          }
        } else {
          this.error = '搜索失败'
        }
      } catch (error) {
        console.error('搜索错误:', error)
        if (error.response) {
          console.log('错误状态码:', error.response.status)
          console.log('错误响应数据:', error.response.data)
          this.error = error.response.data.message
          if (error.response.status === 401 || (error.response.data && (error.response.data.code === 'LOGIN_REQUIRED' || error.response.data.code === 'LOGIN_EXPIRED'))) {
            this.needLogin = true
            localStorage.removeItem('taobao_client_id')
            this.clientId = null
            this.error = '请先登录淘宝'
          }
        } else {
          this.error = error.message || '搜索请求失败'
        }
      } finally {
        this.loading = false
      }
    },
    clearResults () {
      this.searchResults = null
      this.error = null
      this.currentPage = 1
    },
    async loginJd () {
      try {
        const response = await axios.get('http://localhost:5000/api/jd/get_qr_code', {
          client_id: this.jdClientId || Date.now().toString()
        })
        // debug response
        console.log(response.data)
        if (response.data.status === 'success') {
          this.jdSessionId = response.data.data.session_id
          this.jdQrCode = response.data.data.qr_code_url
          this.jdShowQrCode = true
          let retryCount = 0
          const maxRetries = 30 // 最多尝试30次，即60秒
          let accountSet = false // 标记是否已经设置过账号
          // 开始轮询检查登录状态
          this.jdCheckLoginInterval = setInterval(async () => {
            try {
              retryCount++
              if (retryCount >= maxRetries) {
                clearInterval(this.jdCheckLoginInterval)
                this.jdShowQrCode = false
                this.jdError = '登录超时，请重试'
                return
              }
              const statusResponse = await axios.post('http://localhost:5000/api/jd/check_login', {
                session_id: this.jdSessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                // 登录成功且未设置过账号，停止轮询
                clearInterval(this.jdCheckLoginInterval)
                this.jdShowQrCode = false
                // 设置账号（只执行一次）
                try {
                  const accountResponse = await axios.post('http://localhost:5000/api/jd/SetAccount', {
                    message: 'new_session',
                    session_id: this.jdSessionId
                  })
                  if (accountResponse.data.status === 'success') {
                    accountSet = true // 标记已设置账号
                    this.jdClientId = accountResponse.data.client_id
                    localStorage.setItem('jd_client_id', accountResponse.data.client_id)
                    this.jdError = null
                  }
                } catch (error) {
                  console.error('设置京东账号失败:', error)
                  this.jdError = '设置账号失败，请重试'
                }
              } else if (statusResponse.data.status === 'error') {
                clearInterval(this.jdCheckLoginInterval)
                this.jdShowQrCode = false
                this.jdError = statusResponse.data.message
              }
            } catch (error) {
              console.error('检查京东登录状态错误:', error)
              clearInterval(this.jdCheckLoginInterval)
              this.jdShowQrCode = false
              this.jdError = '登录失败，请重试'
            }
          }, 2000)
        } else {
          this.jdError = response.data.message || '获取二维码失败'
        }
      } catch (error) {
        console.error('京东登录错误:', error)
        this.jdError = '登录失败，请重试'
      }
    },
    async searchJd () {
      if (!this.jdKeyword.trim()) {
        this.jdError = '请输入搜索关键词'
        return
      }
      if (!this.jdClientId) {
        this.jdError = '请先登录京东'
        this.jdNeedLogin = true
        return
      }
      this.jdLoading = true
      this.jdError = null
      this.jdNeedLogin = false
      try {
        const response = await axios.post('http://localhost:5000/api/jd/search', {
          keyword: this.jdKeyword,
          page: this.jdCurrentPage
        }, {
          headers: {
            'X-Client-ID': this.jdClientId,
            'Content-Type': 'application/json'
          }
        })
        if (response.data && response.data.status === 'success') {
          this.jdSearchResults = response.data.results
          this.jdError = null
        } else if (response.data) {
          this.jdError = response.data.message || '搜索失败'
          this.jdNeedLogin = response.data.code === 'LOGIN_REQUIRED'
          if (this.jdNeedLogin) {
            localStorage.removeItem('jd_client_id')
            this.jdClientId = null
          }
        }
      } catch (error) {
        console.error('京东搜索错误:', error)
        if (error.response && error.response.status === 401) {
          this.jdNeedLogin = true
          localStorage.removeItem('jd_client_id')
          this.jdClientId = null
          this.jdError = '请先登录京东'
        } else {
          this.jdError = '搜索失败，请重试'
        }
      } finally {
        this.jdLoading = false
      }
    },
    clearJdResults () {
      this.jdSearchResults = null
      this.jdError = null
      this.jdCurrentPage = 1
    }
  }
}
</script>

<style scoped>
html, body {
  height: 100%;
  margin: 0;
}

.main-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: hsl(0, 0%, 100%);
  border-radius: 20px; /* 圆角 */
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5); /* 黑色阴影 */
}

.main-container::before {
    content: '';
    position: absolute;
    top: -10px;
    left: -10px;
    right: 0%;
    bottom: -10px;
    background: linear-gradient(45deg, black, transparent); /* 黑色渐变 */
    border-radius: 30px; /* 更大的圆角 */
    z-index: -1; /* 置于主容器下方 */
}

.container {
  text-align: center;
}

h1 {
  font-weight: bold;
  margin-bottom: 20px;
}

.search-bar {
  display: inline-flex;
  align-items: center;
  border-radius: 30px;
  background-color: #f0f0f0;
  padding: 10px;
  margin-bottom: 20px;
  box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
  width: 80%;
}

input {
  border: none;
  background: transparent;
  font-size: 16px;
  padding: 10px 1%;
  outline: none;
  width: 90%;
}

.button-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  width: 10%;
}

button {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  padding: 0px 10px;
}

.buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.buttons button {
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: background-color 0.3s;
}

.buttons button:hover {
  background-color: #e0e0e0;
}

.response-area {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.error {
  color: red;
  margin: 10px 0;
}

.search-results {
  margin-top: 20px;
  text-align: left;
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.pagination button {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.debug-info {
  background-color: #f5f5f5;
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  text-align: left;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  padding: 20px;
}

.result-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  background-color: white;
  transition: all 0.3s ease;
}

.result-item:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.item-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 10px;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info {
  padding: 5px 0;
}

.item-title {
  font-size: 14px;
  margin: 8px 0;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-price {
  color: #ff4400;
  font-size: 18px;
  font-weight: bold;
  margin: 8px 0;
}

.item-sales, .item-shop, .item-location {
  color: #666;
  font-size: 12px;
  margin: 4px 0;
}

.item-link {
  display: inline-block;
  margin-top: 8px;
  padding: 6px 12px;
  background: #ff4400;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 12px;
  transition: background 0.3s;
}

.item-link:hover {
  text-decoration: none;
  color: #ff6600;
}

.qr-code-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.qr-code-container {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.qr-code-container img {
  max-width: 200px;
  margin: 20px 0;
}

.qr-code-container button {
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.qr-code-container button:hover {
  background-color: #40a9ff;
}

.login-button {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #ff4400;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.login-button:hover {
  background-color: #ff5500;
}

.login-status {
  margin: 10px 0;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
}

.logged-in {
  background-color: #e6f4ea;
  color: #1e8e3e;
}

.logged-out {
  background-color: #fce8e6;
  color: #d93025;
}

.platform-switch {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.platform-switch button {
  padding: 10px 20px;
  margin: 0 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  background-color: #f0f0f0;
}

.platform-switch button.active {
  background-color: #1890ff;
  color: white;
}
</style>
