import Vue from 'vue'
import Router from 'vue-router'
import HelloWorld from '@/components/HelloWorld'
import NewPage from '@/components/NewPage'
import SendMessage from '@/components/SendMessage'
import MultiSearch from '@/components/MultiSearch'
import Auth from '@/components/Auth'

Vue.use(Router)

const routes = [
  {
    path: '/',
    name: 'MultiSearch',
    component: MultiSearch,
    meta: { requiresAuth: true }
  },
  {
    path: '/single',
    name: 'HelloWorld',
    component: HelloWorld
  },
  {
    path: '/GetTitle',
    name: 'NewPage',
    component: NewPage
  },
  {
    path: '/sendmessage',
    name: 'SendMessage',
    component: SendMessage
  },
  {
    path: '/auth',
    name: 'Auth',
    component: Auth
  }
]

const router = new Router({
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('auth_token')

  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 需要认证的路由
    if (!token) {
      // 未登录，重定向到登录页
      next({ name: 'Auth' })
    } else {
      next()
    }
  } else if (to.name === 'Auth' && token) {
    // 已登录用户访问登录页，重定向到首页
    next({ name: 'MultiSearch' })
  } else {
    next()
  }
})

export default router
