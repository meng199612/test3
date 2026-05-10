<template>
  <div class="viewer-page">
    <div class="toolbar">
      <button @click="goHome" class="btn-back">← 重新上传</button>
      <span class="info">点数: {{ info.points }} | 图片: {{ info.images }} 张</span>
      <a :href="`/api/download/${sid}`" class="btn-download" download>⬇ 下载 PLY</a>
    </div>
    <div v-if="loading" class="loading">加载点云数据中...</div>
    <div v-else class="viewer-wrapper">
      <PointCloudViewer :pointData="pointData" />
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PointCloudViewer from '../components/PointCloudViewer.vue'

const route = useRoute()
const router = useRouter()
const sid = route.params.sid
const loading = ref(true)
const error = ref('')
const pointData = ref(null)
const info = ref({ points: 0, images: 0 })

onMounted(async () => {
  try {
    const res = await fetch(`/api/pointcloud/${sid}`)
    const contentType = res.headers.get('content-type') || ''
    if (!res.ok) {
      if (contentType.includes('application/json')) {
        const errData = await res.json()
        throw new Error(errData.detail || `数据加载失败 (${res.status})`)
      }
      throw new Error(`数据加载失败 (${res.status})`)
    }
    if (!contentType.includes('application/json')) {
      throw new Error('服务器返回了非 JSON 数据，请确认重建是否完成')
    }
    const data = await res.json()
    pointData.value = data
    info.value.points = data.n_points || data.vertices.length
  } catch (e) {
    console.error('点云加载失败:', e)
    error.value = e.message
  }
  loading.value = false
})

function goHome() { router.push('/') }
</script>

<style scoped>
.viewer-page { width: 100vw; height: 100vh; display: flex; flex-direction: column; }
.toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: #1a1a24; z-index: 10;
}
.btn-back, .btn-download {
  padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; text-decoration: none;
}
.btn-back { background: #333; color: #ccc; border: none; }
.btn-download { background: #6c5ce7; color: #fff; border: none; }
.info { color: #aaa; font-size: 14px; }
.viewer-wrapper { flex: 1; }
.loading { display: flex; align-items: center; justify-content: center; height: 100%; color: #888; font-size: 18px; }
.error { color: #ff6b6b; text-align: center; padding: 20px; }
</style>
