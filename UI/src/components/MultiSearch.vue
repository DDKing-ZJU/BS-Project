<template>
  <div class="app-container">
    <!-- 顶栏 -->
    <header class="header">
      <h1>多平台比价搜索</h1>
      <div class="user-info">
        <span v-if="username" class="logged-in-status">
          <span class="status-text">已登录</span>
          <span class="username">{{ username }}</span>
        </span>
        <button v-if="username" @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="main-content">
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
                :disabled="taobaoLoading"
              >
                {{ taobaoLoading ? '登录中...' : '登录淘宝' }}
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
                :disabled="jdLoading"
              >
                {{ jdLoading ? '登录中...' : '登录京东' }}
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
              <div class="platform-tag taobao">淘宝</div>
              <img :src="item.image_url" :alt="item.title" class="product-image">
              <div class="product-info">
                <h4>{{ item.title }}</h4>
                <div class="price-info">
                  <span class="price">￥{{ item.price }}</span>
                  <button @click="showPriceHistory(item, 'taobao')" class="history-btn">查看历史价格</button>
                </div>
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
              <div class="platform-tag jd">京东</div>
              <img :src="item.image_url" :alt="item.title" class="product-image">
              <div class="product-info">
                <h4>{{ item.title }}</h4>
                <div class="price-info">
                  <span class="price">￥{{ item.price }}</span>
                  <button @click="showPriceHistory(item, 'jd')" class="history-btn">查看历史价格</button>
                </div>
                <p class="shop">{{ item.shop_name }}</p>
                <p class="location">{{ item.location }}</p>
                <p class="sales">月销 {{ item.sales }}</p>
                <a :href="item.item_url" target="_blank" class="view-btn">查看商品</a>
              </div>
            </div>
          </div>
        </div>

        <!-- 淘宝二维码弹窗 -->
        <transition name="modal">
          <div v-if="showTaobaoQrCode" class="qr-modal">
            <div class="qr-content">
              <div class="modal-header">
                <h3>淘宝登录</h3>
                <button class="close-button" @click="closeTaobaoLogin">&times;</button>
              </div>
              <div class="qr-container">
                <div v-if="taobaoLoadingQr" class="loading-text">
                  二维码加载中...
                </div>
                <img v-else :src="taobaoQrCode" alt="淘宝二维码">
              </div>
              <p>请使用淘宝APP扫码登录</p>
            </div>
          </div>
        </transition>

        <!-- 京东二维码弹窗 -->
        <transition name="modal">
          <div v-if="showJdQrCode" class="qr-modal">
            <div class="qr-content">
              <div class="modal-header">
                <h3>京东登录</h3>
                <button class="close-button" @click="closeJdLogin">&times;</button>
              </div>
              <div class="qr-container">
                <div v-if="jdLoadingQr" class="loading-text">
                  二维码加载中...
                </div>
                <img v-else :src="jdQrCode" alt="京东二维码">
              </div>
              <p>请使用京东APP扫码登录</p>
            </div>
          </div>
        </transition>

        <!-- 历史价格弹窗 -->
        <div v-if="showPriceModal" class="price-history-modal">
          <div class="modal-content">
            <h3>商品历史价格</h3>
            <div class="price-chart" ref="priceChart"></div>
            <button @click="closePriceModal" class="close-btn">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true
})

export default {
  name: 'MultiSearch',
  data () {
    return {
      username: '', // 添加用户名字段
      platforms: {
        taobao: false,
        jd: false
      },
      showTop20: false,
      keyword: '',
      loading: false,
      taobaoLoading: false,
      jdLoading: false,
      taobaoLoadingQr: true,
      jdLoadingQr: true,
      // 淘宝相关
      taobaoSessionId: null,
      taobaoClientId: localStorage.getItem('taobao_client_id'),
      taobaoResults: null,
      taobaoError: null,
      needTaobaoLogin: false,
      showTaobaoQrCode: false,
      taobaoQrCode: '',
      taobaoCheckLoginInterval: null,
      // 京东相关
      jdSessionId: null,
      jdClientId: localStorage.getItem('jd_client_id'),
      jdResults: null,
      jdError: null,
      needJdLogin: false,
      showJdQrCode: false,
      jdQrCode: '',
      jdCheckLoginInterval: null,
      top20Results: null,
      showPriceModal: false,
      priceChart: null,
      currentItemPrice: null
    }
  },
  computed: {
    canSearch () {
      return (this.platforms.taobao || this.platforms.jd) && this.keyword.trim()
    }
  },
  methods: {
    // 添加登出方法
    handleLogout () {
      localStorage.removeItem('auth_token')
      this.$router.push('/auth')
    },

    // 获取用户信息
    async fetchUserInfo () {
      try {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          this.username = ''
          return
        }

        const response = await api.get('/api/auth/verify', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.data.status === 'success') {
          this.username = response.data.user
          console.log('User verified:', this.username) // 添加日志
        } else {
          this.username = ''
          localStorage.removeItem('auth_token')
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.username = ''
        localStorage.removeItem('auth_token')
      }
    },
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
        this.taobaoLoading = false
        return
      }
      try {
        const response = await api.post('/api/taobao/search_taobao', {
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
        this.jdLoading = false
        return
      }
      try {
        const response = await api.post('/api/jd/search', {
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
      this.taobaoLoading = true
      this.showTaobaoQrCode = true // 立即显示弹窗
      this.taobaoLoadingQr = true

      try {
        const response = await api.get('/api/taobao/get_qr_code')
        if (response.data.status === 'success') {
          this.taobaoSessionId = response.data.data.session_id
          this.taobaoQrCode = response.data.data.qr_code
          this.taobaoLoadingQr = false
          let retryCount = 0
          const maxRetries = 30
          let accountSet = false

          // 开始轮询登录状态
          this.taobaoCheckLoginInterval = setInterval(async () => {
            try {
              retryCount++
              if (retryCount > maxRetries) {
                clearInterval(this.taobaoCheckLoginInterval)
                this.showTaobaoQrCode = false
                this.taobaoError = '登录超时，请重试'
                this.taobaoLoading = false
                return
              }
              const statusResponse = await api.post('/api/taobao/check_login', {
                session_id: this.taobaoSessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                clearInterval(this.taobaoCheckLoginInterval)
                this.showTaobaoQrCode = false
                try {
                  const accountResponse = await api.post('/api/taobao/SetAccount', {
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
      this.jdLoading = true
      this.showJdQrCode = true // 立即显示弹窗
      this.jdLoadingQr = true

      try {
        const response = await api.get('/api/jd/get_qr_code')
        if (response.data.status === 'success') {
          this.jdSessionId = response.data.data.session_id
          this.jdQrCode = response.data.data.qr_code_url
          this.jdLoadingQr = false
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
              const statusResponse = await api.post('/api/jd/check_login', {
                session_id: this.jdSessionId
              })
              if (statusResponse.data.status === 'success' && !accountSet) {
                clearInterval(this.jdCheckLoginInterval)
                this.showJdQrCode = false
                try {
                  const accountResponse = await api.post('/api/jd/SetAccount', {
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
                this.jdLoading = false
      }
            }
          }, 2000)
        }
      } catch (error) {
        console.error('获取京东二维码失败:', error)
        this.jdError = '登录失败，请重试'
        this.jdLoading = false
      }
    },
    
    closeTaobaoLogin() {
      this.showTaobaoQrCode = false
      this.taobaoLoading = false
      this.taobaoQrCode = ''
      if (this.taobaoLoginInterval) {
        clearInterval(this.taobaoLoginInterval)
      }
    },

    closeJdLogin() {
      this.showJdQrCode = false
      this.jdLoading = false
      this.jdQrCode = ''
      if (this.jdLoginInterval) {
        clearInterval(this.jdLoginInterval)
      }
    },

    async showPriceHistory (item, platform) {
      try {
        this.showPriceModal = true
        console.log('Requesting price history for:', platform, item.id) // 添加调试日志
        const response = await api.get(`/api/item/price-history/${platform}/${item.id}`)
        console.log('Price history response:', response.data) // 添加调试日志

        // 等待DOM更新后初始化图表
        this.$nextTick(() => {
          if (this.priceChart) {
            this.priceChart.dispose()
          }
          const chartDom = this.$refs.priceChart
          this.priceChart = echarts.init(chartDom, null, {
            renderer: 'svg',
            width: 'auto',
            height: 'auto'
          })

          const option = {
            title: {
              text: '商品价格走势',
              left: 'center',
              textStyle: {
                fontSize: 14
              }
            },
            grid: {
              top: 40,
              right: 20,
              bottom: 60,
              left: 50,
              containLabel: true
            },
            tooltip: {
              trigger: 'axis',
              formatter: '{b}: ￥{c}',
              confine: true
            },
            xAxis: {
              type: 'category',
              data: response.data.dates,
              axisLabel: {
                rotate: 45,
                fontSize: 10,
                interval: 'auto'
              }
            },
            yAxis: {
              type: 'value',
              axisLabel: {
                formatter: '￥{value}',
                fontSize: 10
              }
            },
            series: [{
              data: response.data.prices,
              type: 'line',
              smooth: true,
              symbolSize: 6,
              lineStyle: {
                width: 2
              }
            }]
          }

          this.priceChart.setOption(option)

          // 添加窗口大小变化的响应处理函数
          const handleResize = () => {
            if (this.priceChart) {
              this.priceChart.resize()
            }
          }

          window.addEventListener('resize', handleResize)

          // 在组件实例上保存清理函数
          this._cleanupChart = () => {
            window.removeEventListener('resize', handleResize)
            if (this.priceChart) {
              this.priceChart.dispose()
              this.priceChart = null
            }
          }
        })
      } catch (error) {
        console.error('获取价格历史失败:', error)
        let errorMessage = '获取价格历史数据失败'
        if (error.response && error.response.data && error.response.data.error) {
          errorMessage += ': ' + error.response.data.error
        } else if (error.message) {
          errorMessage += ': ' + error.message
        }
        alert(errorMessage)
      }
    },

    closePriceModal () {
      this.showPriceModal = false
      if (this.priceChart) {
        this.priceChart.dispose()
        this.priceChart = null
      }
    }
  },
  mounted () {
    this.fetchUserInfo() // 组件加载时获取用户信息
  },
  beforeDestroy () {
    // 清理图表相关资源
    if (this._cleanupChart) {
      this._cleanupChart()
    }
  }
}
</script>

<style scoped>
/* 顶部样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logged-in-status {
  margin-right: 1rem;
}

.status-text {
  color: #42b983;  /* 绿色 */
  font-weight: bold;
}

.username {
  margin-left: 0.5rem;
  font-weight: bold;
}

/* 商品卡片样式 */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 1rem;
}

.result-card {
  position: relative;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s;
}

.result-card:hover {
  transform: translateY(-5px);
}

.platform-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: bold;
  z-index: 1;
}

.platform-tag.taobao {
  background-color: #ff4400;
}

.platform-tag.jd {
  background-color: #e1251b;
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: contain;
  background-color: #f5f5f5;
  border-bottom: 1px solid #eee;
}

.product-info {
  padding: 1rem;
}

.product-info h4 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  line-height: 1.4;
  height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.price-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.price {
  color: #ff4400;
  font-size: 1.2rem;
  font-weight: bold;
  margin: 0.5rem 0;
}

.history-btn {
  padding: 5px 10px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.history-btn:hover {
  background-color: #e0e0e0;
}

.shop, .location, .sales {
  color: #666;
  font-size: 0.9rem;
  margin: 0.3rem 0;
}

.view-btn {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #1890ff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.view-btn:hover {
  background-color: #40a9ff;
}

.price-history-modal {
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

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
}

.price-chart {
  width: 100%;
  height: 400px;
  margin: 20px 0;
}

.close-btn {
  display: block;
  margin: 0 auto;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.close-btn:hover {
  background-color: #45a049;
}

/* 弹窗样式 */
.qr-modal {
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

.qr-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
  width: 300px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close-button:hover {
  color: #000;
}

/* 过渡动画 */
.modal-enter-active, .modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.modal-enter-to, .modal-leave-from {
  opacity: 1;
  transform: scale(1);
}

/* 二维码容器样式 */
.qr-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  margin: 15px 0;
}

.loading-text {
  font-size: 16px;
  color: #666;
}

.qr-container img {
  max-width: 100%;
  height: auto;
}
</style>
