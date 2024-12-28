<template>
  <div>
    <h1>发送消息</h1>
    <input v-model="message" placeholder="输入消息" />
    <button @click="sendMessage">发送</button>
    <button @click="sendMessage2">发送2</button>
    <p v-if="response">{{ response }}</p>
    <p v-if="response2">{{ response2 }}</p>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SendMessage',
  data () {
    return {
      message: '',
      response: '',
      response2: ''
    }
  },
  methods: {
    async sendMessage () {
      try {
        const response = await axios.post('http://localhost:5000/send_message', {
          message: this.message
        })
        this.response = JSON.stringify(response.data, null, 2)
      } catch (error) {
        this.response = 'Error: ' + JSON.stringify(error.response.data, null, 2)
      }
    },
    async sendMessage2 () {
      try {
        const response = await axios.post('http://localhost:5000/get_arona_icu', {
          message: this.message
        })
        this.response2 = JSON.stringify(response.data, null, 2)
      } catch (error) {
        this.response2 = 'Error: ' + JSON.stringify(error.response.data, null, 2)
      }
    }
  }
}
</script>

<style scoped>
h1 {
  color: #42b983;
}
</style>
