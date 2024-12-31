<template>
  <div class="tracking-container">
    <header class="header">
      <h1>商品追踪</h1>
      <div class="user-info">
        <span v-if="username" class="logged-in-status">
          <span class="status-text">已登录</span>
          <span class="username">{{ username }}</span>
        </span>
        <button v-if="username" @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </header>

    <!-- 邮箱设置部分 -->
    <div class="email-settings" v-if="!userEmail">
      <h2>设置通知邮箱</h2>
      <div class="email-input">
        <input 
          type="email" 
          v-model="emailInput" 
          placeholder="输入您的邮箱地址"
          @keyup.enter="saveEmail"
        >
        <button @click="saveEmail" :disabled="!isValidEmail">保存</button>
      </div>
    </div>

    <!-- 追踪列表 -->
    <div class="tracking-list">
      <h2>追踪商品列表</h2>
      <div class="tracking-grid">
        <div v-for="item in trackingItems" :key="item.id" class="tracking-card">
          <img :src="item.image_url" :alt="item.title" class="product-image">
          <div class="product-info">
            <h3>{{ item.title }}</h3>
            <p class="current-price">当前价格: ¥{{ item.current_price }}</p>
            <p class="target-price">目标价格: ¥{{ item.target_price }}</p>
            <p class="lowest-price">历史最低: ¥{{ item.lowest_price }}</p>
            <p class="platform-tag" :class="item.platform">{{ item.platform === 'taobao' ? '淘宝' : '京东' }}</p>
            <div class="price-chart" :ref="'chart_' + item.id"></div>
            <div class="actions">
              <button @click="showPriceHistory(item)" class="history-btn">查看历史价格</button>
              <button @click="updateTargetPrice(item)" class="target-btn">修改目标价格</button>
              <button @click="stopTracking(item.id)" class="stop-btn">取消追踪</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改目标价格弹窗 -->
    <div v-if="showTargetPriceModal" class="modal">
      <div class="modal-content">
        <h3>修改目标价格</h3>
        <input 
          type="number" 
          v-model="newTargetPrice" 
          step="0.01" 
          min="0"
          placeholder="输入新的目标价格"
        >
        <div class="modal-actions">
          <button @click="saveTargetPrice">保存</button>
          <button @click="showTargetPriceModal = false">取消</button>
        </div>
      </div>
    </div>

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

const api = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true
})

export default {
  name: 'TrackingList',
  data() {
    return {
      username: '',
      userEmail: localStorage.getItem('userEmail'),
      emailInput: '',
      trackingItems: [],
      showTargetPriceModal: false,
      showPriceModal: false,
      selectedItem: null,
      newTargetPrice: '',
      priceChart: null
    }
  },
  computed: {
    isValidEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(this.emailInput)
    }
  },
  methods: {
    async fetchUserInfo() {
      try {
        const response = await api.get('/api/auth/user')
        if (response.data.success) {
          this.username = response.data.username
          this.userEmail = response.data.email
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    },

    async fetchTrackingItems() {
      try {
        const response = await api.get('/api/tracking/items')
        if (response.data.success) {
          this.trackingItems = response.data.items
          // 为每个商品初始化价格图表
          this.$nextTick(() => {
            this.trackingItems.forEach(item => {
              this.initializeMiniChart(item)
            })
          })
        }
      } catch (error) {
        console.error('获取追踪商品失败:', error)
      }
    },

    async saveEmail() {
      if (!this.isValidEmail) return

      try {
        const response = await api.post('/api/tracking/email', {
          email: this.emailInput
        })
        if (response.data.success) {
          this.userEmail = this.emailInput
          localStorage.setItem('userEmail', this.emailInput)
          this.emailInput = ''
        }
      } catch (error) {
        console.error('保存邮箱失败:', error)
      }
    },

    async updateTargetPrice(item) {
      this.selectedItem = item
      this.newTargetPrice = item.target_price
      this.showTargetPriceModal = true
    },

    async saveTargetPrice() {
      if (!this.selectedItem || !this.newTargetPrice) return

      try {
        const response = await api.put(`/api/tracking/target-price/${this.selectedItem.id}`, {
          target_price: this.newTargetPrice
        })
        if (response.data.success) {
          const index = this.trackingItems.findIndex(item => item.id === this.selectedItem.id)
          if (index !== -1) {
            this.trackingItems[index].target_price = this.newTargetPrice
          }
          this.showTargetPriceModal = false
          this.selectedItem = null
          this.newTargetPrice = ''
        }
      } catch (error) {
        console.error('更新目标价格失败:', error)
      }
    },

    async stopTracking(itemId) {
      try {
        const response = await api.delete(`/api/tracking/items/${itemId}`)
        if (response.data.success) {
          this.trackingItems = this.trackingItems.filter(item => item.id !== itemId)
        }
      } catch (error) {
        console.error('取消追踪失败:', error)
      }
    },

    async showPriceHistory(item) {
      this.selectedItem = item
      this.showPriceModal = true
      
      try {
        const response = await api.get(`/api/item/price-history/${item.id}`)
        if (response.data.success) {
          this.$nextTick(() => {
            this.initializePriceChart(response.data.history)
          })
        }
      } catch (error) {
        console.error('获取价格历史失败:', error)
      }
    },

    initializeMiniChart(item) {
      const chartDom = this.$refs[`chart_${item.id}`][0]
      const chart = echarts.init(chartDom)
      
      const option = {
        grid: {
          top: 10,
          right: 10,
          bottom: 10,
          left: 30
        },
        xAxis: {
          type: 'category',
          data: item.price_history.map(p => p.date),
          show: false
        },
        yAxis: {
          type: 'value',
          show: false
        },
        series: [{
          data: item.price_history.map(p => p.price),
          type: 'line',
          smooth: true
        }]
      }
      
      chart.setOption(option)
    },

    initializePriceChart(history) {
      if (this.priceChart) {
        this.priceChart.dispose()
      }

      const chartDom = this.$refs.priceChart
      this.priceChart = echarts.init(chartDom)
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: history.map(item => item.date)
        },
        yAxis: {
          type: 'value',
          name: '价格'
        },
        series: [{
          name: '商品价格',
          type: 'line',
          data: history.map(item => item.price),
          markLine: {
            data: [
              { 
                name: '目标价格',
                yAxis: this.selectedItem.target_price,
                lineStyle: { color: '#ff4444' }
              }
            ]
          }
        }]
      }
      
      this.priceChart.setOption(option)
    },

    closePriceModal() {
      this.showPriceModal = false
      if (this.priceChart) {
        this.priceChart.dispose()
        this.priceChart = null
      }
    },

    handleLogout() {
      localStorage.removeItem('userEmail')
      this.$emit('logout')
    }
  },
  mounted() {
    this.fetchUserInfo()
    this.fetchTrackingItems()
  },
  beforeDestroy() {
    if (this.priceChart) {
      this.priceChart.dispose()
    }
  }
}
</script>

<style scoped>
.tracking-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.email-settings {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.email-input {
  display: flex;
  gap: 10px;
}

.email-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.tracking-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.tracking-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.product-info {
  padding: 15px;
}

.product-info h3 {
  margin: 0 0 10px;
  font-size: 16px;
  line-height: 1.4;
}

.current-price, .target-price, .lowest-price {
  margin: 5px 0;
  font-size: 14px;
}

.platform-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 5px;
}

.platform-tag.taobao {
  background: #ff4400;
  color: white;
}

.platform-tag.jd {
  background: #e1251b;
  color: white;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.actions button {
  flex: 1;
  padding: 6px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.history-btn {
  background: #4CAF50;
  color: white;
}

.target-btn {
  background: #2196F3;
  color: white;
}

.stop-btn {
  background: #f44336;
  color: white;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-width: 300px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.price-history-modal .modal-content {
  width: 80%;
  max-width: 800px;
}

.price-chart {
  height: 400px;
  margin: 20px 0;
}
</style>
