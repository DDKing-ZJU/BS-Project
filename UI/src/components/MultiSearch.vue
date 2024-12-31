<template>
  <div class="multi-search-container">
    <!-- 顶栏 -->
    <div class="top-bar">
      <div class="left-buttons">
        <button
          class="nav-button"
          @click="$router.push('/tracking')"
        >
          我的收藏
        </button>
      </div>
      <div class="right-buttons">
        <button
          v-if="!isLoggedIn"
          class="nav-button"
          @click="$router.push('/auth')"
        >
          登录/注册
        </button>
        <button
          v-else
          class="nav-button"
          @click="handleLogout"
        >
          退出登录
        </button>
      </div>
    </div>

    <div class="main-content">
      <!-- 侧边栏 -->
      <div :class="['sidebar', { 'collapsed': sidebarCollapsed }]" style="z-index: 1000;">
        <button class="collapse-btn" @click="toggleSidebar">
          {{ sidebarCollapsed ? '›' : '‹' }}
        </button>
        <div class="sidebar-content" v-show="!sidebarCollapsed">
          <div class="search-section">
            <div class="platform-select">
              <label>选择平台：</label>
              <select v-model="selectedPlatform">
                <option value="both">全部</option>
                <option value="taobao">淘宝</option>
                <option value="jd">京东</option>
              </select>
            </div>

            <div class="search-box">
              <input
                type="text"
                v-model="keyword"
                @keyup.enter="search"
                placeholder="输入关键词搜索"
                :disabled="loading"
              >
              <button @click="search" :disabled="loading">
                {{ loading ? '搜索中...' : '搜索' }}
              </button>
            </div>
          </div>

          <div class="platform-status">
            <h3>平台状态</h3>
            
            <!-- 淘宝状态 -->
            <div class="platform-item" v-if="selectedPlatform === 'both' || selectedPlatform === 'taobao'">
              <div class="platform-header">
                <span class="platform-name">淘宝</span>
              </div>
              <div class="login-status">
                <span :class="{ 'status-dot': true, 'logged-in': taobaoClientId }"></span>
                {{ taobaoClientId ? '已登录' : '未登录' }}
              </div>
              <button
                v-if="!taobaoClientId"
                @click="loginTaobao"
                :disabled="taobaoLoading"
                class="login-button"
              >
                {{ taobaoLoading ? '登录中...' : '登录淘宝' }}
              </button>
            </div>

            <!-- 京东状态 -->
            <div class="platform-item" v-if="selectedPlatform === 'both' || selectedPlatform === 'jd'">
              <div class="platform-header">
                <span class="platform-name">京东</span>
              </div>
              <div class="login-status">
                <span :class="{ 'status-dot': true, 'logged-in': jdClientId }"></span>
                {{ jdClientId ? '已登录' : '未登录' }}
              </div>
              <button
                v-if="!jdClientId"
                @click="loginJd"
                :disabled="jdLoading"
                class="login-button"
              >
                {{ jdLoading ? '登录中...' : '登录京东' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="content" style="position: relative; z-index: 1;">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="loading" class="loading">
          <div class="loading-spinner"></div>
          <p>正在搜索商品...</p>
        </div>

        <div v-else-if="!loading && !taobaoResults && !jdResults && !error && !taobaoError && !jdError" class="no-results">
          <p>暂无搜索结果</p>
        </div>

        <div v-else class="search-results">
          <!-- Top20搜索结果 -->
          <div v-if="showTop20 && top20Results" class="platform-section">
            <h3>Top20搜索结果</h3>
            <div class="results-grid">
              <div v-for="(item, index) in top20Results" :key="'top20-' + index" class="result-card">
                <div class="platform-tag top20">Top20</div>
                <img :src="item.image" :alt="item.title" class="product-image">
                <div class="product-info">
                  <h4>{{ item.title }}</h4>
                  <p class="price">¥{{ item.price }}</p>
                  <p class="shop">{{ item.shop }}</p>
                  <div class="actions">
                    <a :href="item.url" target="_blank" class="view-btn">查看详情</a>
                    <button @click="showPriceHistory(item, item.platform)" class="history-btn">
                      历史价格
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 淘宝搜索结果 -->
          <div v-if="taobaoResults && taobaoResults.length" class="platform-section">
            <h3>淘宝搜索结果</h3>
            <div class="results-grid">
              <div v-for="(item, index) in taobaoResults" :key="'taobao-' + index" class="result-card">
                <div class="platform-tag taobao">淘宝</div>
                <img :src="item.image_url" :alt="item.title" class="product-image">
                <div class="product-info">
                  <h4>{{ item.title }}</h4>
                  <p class="price">¥{{ item.price }}</p>
                  <p class="shop">{{ item.shop_name }}</p>
                  <div class="actions">
                    <a :href="item.item_url" target="_blank" class="view-btn">查看详情</a>
                    <button @click="showPriceHistory(item, 'taobao')" class="history-btn">
                      历史价格
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 京东搜索结果 -->
          <div v-if="jdResults && jdResults.length" class="platform-section">
            <h3>京东搜索结果</h3>
            <div class="results-grid">
              <div v-for="(item, index) in jdResults" :key="'jd-' + index" class="result-card">
                <div class="platform-tag jd">京东</div>
                <img :src="item.image_url" :alt="item.title" class="product-image">
                <div class="product-info">
                  <h4>{{ item.title }}</h4>
                  <p class="price">¥{{ item.price }}</p>
                  <p class="shop">{{ item.shop_name }}</p>
                  <div class="actions">
                    <a :href="item.item_url" target="_blank" class="view-btn">查看详情</a>
                    <button @click="showPriceHistory(item, 'jd')" class="history-btn">
                      历史价格
                    </button>
                  </div>
                </div>
              </div>
            </div>
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
      selectedPlatform: 'both', // 添加平台选择
      loading: false,
      error: null, // 添加错误信息
      results: [], // 添加搜索结果数组
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
      currentItemPrice: null,
      sidebarCollapsed: false // 添加侧边栏折叠状态
    }
  },
  computed: {
    canSearch () {
      return this.selectedPlatform && this.keyword.trim()
    },
    isLoggedIn () {
      return !!localStorage.getItem('auth_token')
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
          console.log('User verified:', this.username)
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

      try {
        // 清空之前的结果
        this.taobaoResults = null
        this.jdResults = null
        this.top20Results = null
        this.error = null
        this.taobaoError = null
        this.jdError = null

        // 创建搜索任务数组
        const searchTasks = []

        // 根据选择的平台添加搜索任务
        if (this.selectedPlatform === 'both' || this.selectedPlatform === 'taobao') {
          searchTasks.push(this.searchTaobao())
        }
        if (this.selectedPlatform === 'both' || this.selectedPlatform === 'jd') {
          searchTasks.push(this.searchJd())
        }

        // 同时执行所有搜索任务
        await Promise.all(searchTasks)

        // 如果启用了 Top20，生成 Top20 结果
        if (this.selectedPlatform === 'both') {
          this.generateTop20Results()
        }
      } catch (error) {
        console.error('搜索出错:', error)
        this.error = '搜索过程中出现错误，请重试'
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

    closeTaobaoLogin () {
      this.showTaobaoQrCode = false
      this.taobaoLoading = false
      this.taobaoQrCode = ''
      if (this.taobaoLoginInterval) {
        clearInterval(this.taobaoLoginInterval)
      }
    },

    closeJdLogin () {
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
    },
    toggleSidebar () {
      this.sidebarCollapsed = !this.sidebarCollapsed
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
.multi-search-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

/* 顶栏样式 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-button {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  background-color: transparent;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  right: 0;
  top: 60px;
  width: 250px;
  height: calc(100vh - 60px);
  background: white;
  padding: 20px;
  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  transition: width 0.3s;
  z-index: 1000;
}

.sidebar.collapsed {
  width: 50px;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.search-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.platform-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.platform-select label {
  color: #1890ff;
  font-weight: 500;
}

.platform-select select {
  padding: 0.8rem;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  background-color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: border-color 0.3s;
}

.platform-select select:hover,
.platform-select select:focus {
  border-color: #1890ff;
  outline: none;
}

.search-box {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-box input {
  padding: 0.8rem;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.search-box input:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.search-box button {
  padding: 0.8rem;
  border: none;
  border-radius: 8px;
  background-color: #1890ff;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-box button:hover:not(:disabled) {
  background-color: #40a9ff;
}

.search-box button:disabled {
  background-color: #d9d9d9;
  cursor: not-allowed;
}

.platform-status {
  margin-bottom: 20px;
}

.platform-status h3 {
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;
}

.platform-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 15px;
}

.platform-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.platform-logo {
  width: 24px;
  height: 24px;
  margin-right: 10px;
  object-fit: contain;
}

.login-status {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  background: #ff4d4f;
}

.status-dot.logged-in {
  background: #52c41a;
}

.login-button {
  width: 100%;
  padding: 8px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-align: center;
  text-decoration: none;
  transition: all 0.3s;
}

.login-button:hover:not(:disabled) {
  background: #40a9ff;
}

.login-button:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.collapse-btn {
  position: absolute;
  top: 10px;
  left: 10px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

/* 内容区域样式 */
.content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

/* 搜索结果样式 */
.search-results {
  padding: 20px;
  margin-right: 250px;
  transition: margin-right 0.3s;
}

.sidebar.collapsed + .content .search-results {
  margin-right: 50px;
}

.platform-section {
  margin-bottom: 30px;
}

.platform-section h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
  padding-left: 10px;
  border-left: 4px solid #1890ff;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.result-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
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

.platform-tag.top20 {
  background-color: #1890ff;
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: contain;
  background-color: #f5f5f5;
}

.product-info {
  padding: 15px;
}

.product-info h4 {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.price {
  color: #ff4400;
  font-size: 18px;
  font-weight: bold;
  margin: 10px 0;
}

.shop {
  color: #666;
  font-size: 12px;
  margin-bottom: 10px;
}

.actions {
  display: flex;
  gap: 10px;
}

.view-btn, .history-btn {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-align: center;
  text-decoration: none;
  transition: all 0.3s;
}

.view-btn {
  background: #1890ff;
  color: white;
}

.view-btn:hover {
  background: #40a9ff;
}

.history-btn {
  background: #f0f0f0;
  color: #666;
}

.history-btn:hover {
  background: #e0e0e0;
}

/* 加载和错误状态 */
.loading, .no-results {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  color: #ff4d4f;
  padding: 10px;
  margin-bottom: 10px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
}

/* 价格历史弹窗 */
.price-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.price-chart {
  height: 400px;
}
</style>
