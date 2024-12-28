import Vue from 'vue'
import Router from 'vue-router'
import HelloWorld from '@/components/HelloWorld'
import NewPage from '@/components/NewPage'
import SendMessage from '@/components/SendMessage'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
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
    }
  ]
})
