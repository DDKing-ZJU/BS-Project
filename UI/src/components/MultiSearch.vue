<template>
  <div class="multi-search">
    <div class="platform-selection">
      <h2>选择搜索平台</h2>
      <div class="platform-controls">
        <div class="platform-item">
          <label>
            <input type="checkbox" v-model="platforms.taobao" @change="checkLoginStatus('taobao')">
            淘宝
          </label>
          <button
            v-if="platforms.taobao && !taobaoClientId"
            @click="loginTaobao"
            class="login-button"
            :disabled="taobaoLoggingIn"
          >
            {{ taobaoLoggingIn ? '登录中...' : '登录淘宝' }}
          </button>
          <span v-else-if="platforms.taobao && taobaoClientId" class="login-status">已登录</span>
        </div>
        <div class="platform-item">
          <label>
            <input type="checkbox" v-model="platforms.jd" @change="checkLoginStatus('jd')">
            京东
          </label>
          <button
            v-if="platforms.jd && !jdClientId"
            @click="loginJd"
            class="login-button"
            :disabled="jdLoggingIn"
          >
            {{ jdLoggingIn ? '登录中...' : '登录京东' }}
          </button>
          <span v-else-if="platforms.jd && jdClientId" class="login-status">已登录</span>
        </div>
        <div class="platform-item">
          <label>
            <input type="checkbox" v-model="showTop20">
            Top20
          </label>
        </div>
      </div>
    </div>
    <div class="search-section">
      <div class="search-input">
        <input
          type="text"
          v-model="keyword"
          placeholder="输入搜索关键词"
          @keyup.enter="search"
          :disabled="loading"
        >
        <button
          @click="search"
          :disabled="!canSearch || loading"
          class="search-button"
        >
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      正在搜索...
    </div>

    <div class="search-results">

      <!-- Top20搜索结果 -->
      <div v-if="showTop20 && top20Results" class="platform-results">
        <h3>Top20搜索结果</h3>
        <div class="results-grid">
          <div v-for="(item, index) in top20Results" :key="'top20-' + index" class="result-card">
            <img :src="item.image" :alt="item.title" class="product-image">
            <div class="product-info">
              <h4>{{ item.title }}</h4>
              <p class="price">¥{{ item.price }}</p>
              <p class="shop">{{ item.shop }}</p>
              <p class="location">{{ item.location }}</p>
              <p class="sales">月销 {{ item.sales }}</p>
              <a :href="item.url" target="_blank" class="view-btn">查看商品</a>
              <span v-if="item.platform === 'taobao'" class="platform-tag taobao">淘宝</span>
              <span v-else-if="item.platform === 'jd'" class="platform-tag jd">京东</span>
            </div>
          </div>
        </div>
      </div>
    </div>

      <!-- 淘宝搜索结果 -->
      <div v-if="platforms.taobao" class="platform-results">
        <h3>淘宝搜索结果</h3>
        <div v-if="taobaoError" class="error-message">{{ taobaoError }}</div>
        <div v-else-if="taobaoResults" class="results-grid">
          <div v-for="(item, index) in taobaoResults" :key="'taobao-' + index" class="result-card">
            <img :src="item.image_url" :alt="item.title" class="product-image">
            <div class="product-info">
              <h4>{{ item.title }}</h4>
              <p class="price">¥{{ item.price }}</p>
              <p class="shop">{{ item.shop_name }}</p>
              <p class="location">{{ item.location }}</p>
              <p class="sales">月销 {{ item.sales }}</p>
              <a :href="item.item_url" target="_blank" class="view-btn">查看商品</a>
            </div>
          </div>
        </div>
      </div>

      <!-- 京东搜索结果 -->
      <div v-if="platforms.jd" class="platform-results">
        <h3>京东搜索结果</h3>
        <div v-if="jdError" class="error-message">{{ jdError }}</div>
        <div v-else-if="jdResults" class="results-grid">
          <div v-for="(item, index) in jdResults" :key="'jd-' + index" class="result-card">
            <img :src="item.image_url" :alt="item.title" class="product-image">
            <div class="product-info">
              <h4>{{ item.title }}</h4>
              <p class="price">¥{{ item.price }}</p>
              <p class="shop">{{ item.shop_name }}</p>
              <p class="location">{{ item.location }}</p>
              <p class="sales">月销 {{ item.sales }}</p>
              <a :href="item.item_url" target="_blank" class="view-btn">查看商品</a>
            </div>
          </div>
        </div>
      </div>

    <!-- 淘宝二维码弹窗 -->
    <div v-if="showTaobaoQrCode" class="qr-modal">
      <div class="qr-content">
        <h3>淘宝登录</h3>
        <img :src="taobaoQrCode" alt="淘宝二维码">
        <p>请使用淘宝APP扫码登录</p>
      </div>
    </div>

    <!-- 京东二维码弹窗 -->
    <div v-if="showJdQrCode" class="qr-modal">
      <div class="qr-content">
        <h3>京东登录</h3>
        <img :src="jdQrCode" alt="京东二维码">
        <p>请使用京东APP扫码登录</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'MultiSearch',
  data () {
    return {
      platforms: {
        taobao: false,
        jd: false
      },
      showTop20: false,
      keyword: '',
      loading: false,
      taobaoLoggingIn: false,
      jdLoggingIn: false,
      // 淘宝相关
      taobaoSessionId: null,
      taobaoClientId: localStorage.getItem('taobao_client_id'),
      taobaoResults: null,
      taobaoError: null,
      needTaobaoLogin: false,
      showTaobaoQrCode: false,
      taobaoQrCode: null,
      taobaoCheckLoginInterval: null,
      // 京东相关
      jdSessionId: null,
      jdClientId: localStorage.getItem('jd_client_id'),
      jdResults: null,
      jdError: null,
      needJdLogin: false,
      showJdQrCode: false,
      jdQrCode: null,
      jdCheckLoginInterval: null,
      top20Results: null
    }
  },
  computed: {
    canSearch () {
      return (this.platforms.taobao || this.platforms.jd) && this.keyword.trim()
    }
  },
  methods: {
    async checkLoginStatus (platform) {
      if (platform === 'taobao' && this.platforms.taobao) {
        if (!this.taobaoClientId) {
          this.needTaobaoLogin = true
          this.taobaoError = '请先登录淘宝后再搜索'
        }
      } else if (platform === 'jd' && this.platforms.jd) {
        if (!this.jdClientId) {
          this.needJdLogin = true
          this.jdError = '请先登录京东后再搜索'
        }
      } else if (platform === 'taobao' && !this.platforms.taobao) {
        // 取消选择淘宝时，清除相关结果
        this.taobaoResults = null
        this.taobaoError = null
        this.needTaobaoLogin = false
      } else if (platform === 'jd' && !this.platforms.jd) {
        // 取消选择京东时，清除相关结果
        this.jdResults = null
        this.jdError = null
        this.needJdLogin = false
      }
    },
    async search () {
      if (!this.canSearch || this.loading) return
      this.loading = true

      // 重置结果
      this.top20Results = null

      const searchPromises = []

      if (this.platforms.taobao) {
        this.taobaoResults = null
        this.taobaoError = null
        searchPromises.push(this.searchTaobao())
      }

      if (this.platforms.jd) {
        this.jdResults = null
        this.jdError = null
        searchPromises.push(this.searchJd())
      }

      try {
        await Promise.all(searchPromises)
        // 如果两个平台都选中且搜索成功，则生成Top20结果
        if (this.showTop20) {
          this.generateTop20Results()
        }
      } catch (error) {
        console.error('搜索出错:', error)
      } finally {
        this.loading = false
      }
    },

    generateTop20Results () {
      // 合并两个平台的结果
      const allResults = []

      // 处理淘宝结果
      if (this.taobaoResults && this.taobaoResults.length) {
        const taobaoItems = this.taobaoResults.slice(0, 20).map(item => ({
          ...item,
          platform: 'taobao',
          price: parseFloat(item.price),
          url: item.item_url,
          image: item.image_url,
          shop: item.shop_name
        }))
        allResults.push(...taobaoItems)
      }

      // 处理京东结果
      if (this.jdResults && this.jdResults.length) {
        const jdItems = this.jdResults.slice(0, 20).map(item => ({
          ...item,
          platform: 'jd',
          price: parseFloat(item.price),
          url: item.item_url,
          image: item.image_url,
          shop: item.shop_name
        }))
        allResults.push(...jdItems)
      }

      // 按价格升序排序并取前20个
      this.top20Results = allResults
        .sort((a, b) => a.price - b.price)
        .slice(0, 20)
    },
    async searchTaobao () {
      if (!this.taobaoClientId) {
        this.taobaoError = '请先登录淘宝'
        this.needTaobaoLogin = true
        this.taobaoLoggingIn = false
        return
      }
      try {
        const response = await axios.post('http://localhost:5000/api/taobao/search_taobao', {
          keyword: this.keyword
        }, {
          headers: {
            'X-Client-ID': this.taobaoClientId
          }
        })
        if (response.data.status === 'success') {
          this.taobaoResults = response.data.data
          this.taobaoError = null
        } else {
          this.taobaoError = response.data.message || '搜索失败'
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          // 401表示未授权，清除登录状态
          this.taobaoClientId = null
          localStorage.removeItem('taobao_client_id')
          this.needTaobaoLogin = true
          this.taobaoError = '登录已过期，请重新登录'
        } else {
          this.taobaoError = '搜索失败，请重试'
        }
      }
    },
    async searchJd () {
      if (!this.jdClientId) {
        this.jdError = '请先登录京东'
        this.needJdLogin = true
        this.jdLoggingIn = false
        return
      }
      try {
        const response = await axios.post('http://localhost:5000/api/jd/search', {
          keyword: this.keyword
        }, {
          headers: {
            'X-Client-ID': this.jdClientId
          }
        })
        if (response.data.status === 'success') {
          this.jdResults = response.data.results
          this.jdError = null
        } else {
          this.jdError = response.data.message || '搜索失败'
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          // 401表示未授权，清除登录状态
          this.jdClientId = null
          localStorage.removeItem('jd_client_id')
          this.needJdLogin = true
          this.jdError = '登录已过期，请重新登录'
        } else {
          this.jdError = '搜索失败，请重试'
        }
      }
    },
    async loginTaobao () {
      if (this.taobaoLoggingIn) return
      this.taobaoLoggingIn = true
      try {
        const response = await axios.get('http://localhost:5000/api/taobao/get_qr_code')
        if (response.data.status === 'success') {
          this.taobaoSessionId = response.data.data.session_id
          this.taobaoQrCode = response.data.data.qr_code
          this.showTaobaoQrCode = true
          let retryCount = 0
          const maxRetries = 30
          let accountSet = false
          this.taobaoCheckLoginInterval = setInterval(async () => {
            try {
              retryCount++
              if (retryCount > maxRetries) {
                clearInterval(this.taobaoCheckLoginInterval)
                this.showTaobaoQrCode = false
                this.taobaoError = '登录超时，请重试'
                this.taobaoLoggingIn = false
                return
              }
              const statusResponse = await axios.post('http://localhost:5000/api/taobao/check_login', {
                session_id: this.taobaoSessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                clearInterval(this.taobaoCheckLoginInterval)
                this.showTaobaoQrCode = false
                try {
                  const accountResponse = await axios.post('http://localhost:5000/api/taobao/SetAccount', {
                    message: 'new_session',
                    session_id: this.taobaoSessionId
                  })
                  if (accountResponse.data.status === 'success') {
                    accountSet = true
                    this.taobaoClientId = accountResponse.data.client_id
                    localStorage.setItem('taobao_client_id', accountResponse.data.client_id)
                    this.taobaoError = null
                    this.needTaobaoLogin = false
                  }
                } catch (error) {
                  console.error('设置淘宝账号失败:', error)
                  this.taobaoError = '登录失败，请重试'
                }
              }
            } catch (error) {
              console.error('检查淘宝登录状态失败:', error)
            } finally {
              if (accountSet) {
                this.taobaoLoggingIn = false
              }
            }
          }, 2000)
        }
      } catch (error) {
        console.error('获取淘宝二维码失败:', error)
        this.taobaoError = '登录失败，请重试'
        this.taobaoLoggingIn = false
      }
    },
    async loginJd () {
      if (this.jdLoggingIn) return
      this.jdLoggingIn = true
      try {
        const response = await axios.get('http://localhost:5000/api/jd/get_qr_code')
        if (response.data.status === 'success') {
          this.jdSessionId = response.data.data.session_id
          this.jdQrCode = response.data.data.qr_code_url
          this.showJdQrCode = true
          let retryCount = 0
          const maxRetries = 30
          let accountSet = false
          this.jdCheckLoginInterval = setInterval(async () => {
            try {
              retryCount++
              if (retryCount > maxRetries) {
                clearInterval(this.jdCheckLoginInterval)
                this.showJdQrCode = false
                this.jdError = '登录超时，请重试'
                this.jdLoggingIn = false
                return
              }
              const statusResponse = await axios.post('http://localhost:5000/api/jd/check_login', {
                session_id: this.jdSessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                clearInterval(this.jdCheckLoginInterval)
                this.showJdQrCode = false
                try {
                  const accountResponse = await axios.post('http://localhost:5000/api/jd/SetAccount', {
                    message: 'new_session',
                    session_id: this.jdSessionId
                  })
                  if (accountResponse.data.status === 'success') {
                    accountSet = true
                    this.jdClientId = accountResponse.data.client_id
                    localStorage.setItem('jd_client_id', this.jdClientId)
                    this.needJdLogin = false
                    this.jdError = null
                  }
                } catch (error) {
                  console.error('设置京东账号失败:', error)
                  this.jdError = '登录失败，请重试'
                }
              }
            } catch (error) {
              console.error('检查京东登录状态失败:', error)
            } finally {
              if (accountSet) {
                this.jdLoggingIn = false
              }
            }
          }, 2000)
        }
      } catch (error) {
        console.error('获取京东二维码失败:', error)
        this.jdError = '登录失败，请重试'
        this.jdLoggingIn = false
      }
    }
  }
}
</script>

<style scoped>
.multi-search {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.platform-selection {
  margin-bottom: 20px;
}

.platform-selection h2 {
  margin-bottom: 10px;
}

.platform-controls {
  display: flex;
  gap: 30px;
  align-items: center;
}

.platform-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.platform-item label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.login-button {
  padding: 5px 15px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.login-button:hover {
  background-color: #40a9ff;
}

.login-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.login-status {
  color: #52c41a;
  font-size: 14px;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  display: flex;
  gap: 10px;
}

.search-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.search-input input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.search-input button {
  padding: 10px 20px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-input button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #666;
}

.search-results {
  margin-top: 20px;
}

.platform-results {
  margin-bottom: 30px;
}

.platform-results h3 {
  margin-bottom: 15px;
  color: #333;
}

.error-message {
  color: #ff4d4f;
  margin-bottom: 10px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  padding: 10px;
}

.result-card {
  position: relative;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-bottom: 1px solid #f0f0f0;
}

.product-info {
  padding: 12px;
}

.product-info h4 {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.price {
  color: #ff4d4f;
  font-size: 18px;
  font-weight: bold;
  margin: 8px 0;
}

.shop, .location, .sales {
  color: #666;
  font-size: 12px;
  margin: 4px 0;
}

.view-btn {
  display: block;
  text-align: center;
  padding: 8px 0;
  margin-top: 10px;
  background-color: #1890ff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.view-btn:hover {
  background-color: #40a9ff;
}

.platform-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
}

.platform-tag.taobao {
  background-color: #ff4400;
}

.platform-tag.jd {
  background-color: #e1251b;
}

.qr-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.qr-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.qr-content img {
  max-width: 200px;
  margin: 15px 0;
}

.qr-content h3 {
  margin-bottom: 15px;
  color: #333;
}

.qr-content p {
  color: #666;
  margin-top: 10px;
}
</style>
