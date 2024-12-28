<template>
  <div class="container">
    <h1>有什么可以帮忙的？</h1>
    <div class="search-bar">
      <input type="text" placeholder="给'ChatGPT'发送消息" />
      <button>⇧</button>
    </div>
    <div class="buttons">
      <button>创建图片</button>
      <button>总结文本</button>
      <button>构思</button>
      <button>给我惊喜</button>
      <button>代码</button>
      <button>更多</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelpInterface',
};
</script>

<style scoped>
.container {
  text-align: center;
  margin-top: 50px;
}

h1 {
  font-weight: bold;
  margin-bottom: 20px;
}

.search-bar {
  display: inline-flex;
  align-items: center;
  border-radius: 25px;
  background-color: #f0f0f0;
  padding: 10px;
  margin-bottom: 20px;
}

input {
  border: none;
  background: transparent;
  font-size: 16px;
  padding: 5px;
  outline: none;
  width: 200px;
}

button {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
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
</style>

在Linux服务器上部署时，你需要：

安装Chrome浏览器：
sudo apt-get update
sudo apt-get install -y google-chrome-stable
安装必要的依赖：
sudo apt-get install -y xvfb libxi6 libgconf-2-4
下载对应版本的ChromeDriver并给予执行权限：
chmod +x ./chromedriver
这样的代码现在应该能够在Windows和Linux环境下都正常工作了。如果还有任何问题，请告诉我。
