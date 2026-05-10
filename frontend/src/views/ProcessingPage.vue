<template>
  <div class="processing-page">
    <h1>正在生成 3D 点云...</h1>
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="progress-text">{{ message }}</p>
      <p class="progress-percent">{{ Math.round(progress) }}%</p>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const progress = ref(0)
const message = ref('准备中...')
const error = ref('')
let ws = null

onMounted(() => {
  const sid = route.params.sid
  connectWebSocket(sid)
  fetch(`/api/reconstruct/${sid}`, { method: 'POST' }).catch(e => {
    error.value = '无法启动重建: ' + e.message
  })
})

function connectWebSocket(sid) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/${sid}`)

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.type === 'progress') {
      progress.value = data.percent
      message.value = data.message
    } else if (data.type === 'complete') {
      progress.value = 100
      message.value = '完成!'
      setTimeout(() => router.push(`/viewer/${sid}`), 500)
    } else if (data.type === 'error') {
      error.value = data.message
    }
  }

  ws.onerror = () => { error.value = 'WebSocket 连接失败' }
}

onBeforeUnmount(() => { if (ws) ws.close() })
</script>

<style scoped>
.processing-page {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 100vh; padding: 40px;
}
.progress-container { width: 400px; max-width: 90%; margin-top: 40px; }
.progress-bar {
  width: 100%; height: 12px; background: #222; border-radius: 6px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 6px; transition: width .3s ease;
}
.progress-text { margin-top: 20px; color: #aaa; text-align: center; }
.progress-percent { margin-top: 8px; font-size: 24px; font-weight: bold; text-align: center; }
.error { color: #ff6b6b; margin-top: 20px; }
</style>
