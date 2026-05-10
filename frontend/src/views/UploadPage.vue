<template>
  <div class="upload-page">
    <div class="header">
      <h1>🔷 Pic2PointCloud</h1>
      <p>上传多张物体照片，自动生成 3D 点云</p>
    </div>
    <div class="upload-area"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="handleDrop"
      :class="{ dragging: dragOver }"
      @click="triggerFileInput">
      <div class="upload-hint">
        <div class="icon">📁</div>
        <p>拖拽图片到此处，或点击选择</p>
        <p class="sub">支持 JPG/PNG，建议 10-50 张</p>
      </div>
      <input ref="fileInput" type="file" multiple accept="image/*" @change="handleFileSelect" hidden>
    </div>
    <div v-if="files.length > 0" class="file-list">
      <h3>已选择 {{ files.length }} 张图片</h3>
      <div class="file-grid">
        <div v-for="(file, i) in files" :key="i" class="file-item">
          <button @click.stop="removeFile(i)" class="remove-btn" title="删除">×</button>
          <img :src="file.url" :alt="file.name">
          <span class="file-name">{{ file.name }}</span>
        </div>
      </div>
    </div>
    <button v-if="files.length >= 2" class="start-btn" @click="startUpload" :disabled="uploading">
      {{ uploading ? '上传中...' : '开始生成 3D' }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const fileInput = ref(null)
const files = ref([])
const uploading = ref(false)
const error = ref('')
const dragOver = ref(false)

function triggerFileInput() { fileInput.value.click() }

function handleDrop(e) {
  dragOver.value = false
  handleFiles(e.dataTransfer.files)
}

function handleFileSelect(e) {
  handleFiles(e.target.files)
}

function handleFiles(fileList) {
  error.value = ''
  const newFiles = []
  for (const f of fileList) {
    if (files.value.length + newFiles.length >= 50) break
    newFiles.push({
      name: f.name,
      file: f,
      url: URL.createObjectURL(f)
    })
  }
  files.value = [...files.value, ...newFiles]
}

function removeFile(index) {
  const file = files.value[index]
  if (file && file.url) {
    URL.revokeObjectURL(file.url)
  }
  files.value.splice(index, 1)
}

async function startUpload() {
  if (files.value.length < 2) {
    error.value = '至少需要 2 张图片'
    return
  }
  uploading.value = true
  error.value = ''
  const formData = new FormData()
  for (const f of files.value) {
    formData.append('files', f.file)
  }
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData })
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      const data = await res.json()
      if (res.ok) {
        router.push(`/processing/${data.session_id}`)
      } else {
        error.value = data.detail || `上传失败 (${res.status})`
      }
    } else {
      const text = await res.text()
      console.error('后端返回非 JSON:', res.status, text)
      error.value = `服务器错误: ${res.status}。请检查后端是否已启动。`
    }
  } catch (e) {
    console.error('上传失败:', e)
    error.value = '网络错误: ' + e.message + '。请确认后端服务已启动。'
  }
  uploading.value = false
}
</script>

<style scoped>
.upload-page { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.header { text-align: center; margin-bottom: 40px; }
.header h1 { font-size: 2em; margin-bottom: 8px; }
.upload-area {
  border: 2px dashed #444; border-radius: 16px; padding: 60px 20px;
  text-align: center; cursor: pointer; transition: all .3s;
  background: #1a1a24;
}
.upload-area:hover, .upload-area.dragging { border-color: #6c5ce7; background: #1e1e2e; }
.upload-hint .icon { font-size: 48px; margin-bottom: 16px; }
.upload-hint p { font-size: 18px; color: #ccc; }
.upload-hint .sub { font-size: 14px; color: #888; margin-top: 8px; }
.file-list { margin-top: 30px; }
.file-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
.file-item {
  width: 100px; text-align: center; position: relative;
}
.file-item img { width: 100%; height: 80px; object-fit: cover; border-radius: 6px; }
.file-item .file-name { font-size: 11px; color: #aaa; word-break: break-all; }
.remove-btn {
  position: absolute; top: -8px; right: -8px;
  width: 22px; height: 22px;
  border: none; border-radius: 50%;
  background: #ff6b6b; color: #fff;
  font-size: 14px; font-weight: bold;
  cursor: pointer; display: flex;
  align-items: center; justify-content: center;
  z-index: 10; opacity: 0.9;
  transition: transform 0.2s, opacity 0.2s;
}
.remove-btn:hover { transform: scale(1.1); opacity: 1; }
.start-btn {
  display: block; margin: 30px auto 0; padding: 14px 48px; font-size: 18px;
  background: #6c5ce7; color: #fff; border: none; border-radius: 10px;
  cursor: pointer; transition: background .3s;
}
.start-btn:hover { background: #5a4bd1; }
.start-btn:disabled { opacity: .5; cursor: not-allowed; }
.error { color: #ff6b6b; text-align: center; margin-top: 16px; }
</style>
