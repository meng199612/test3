<template>
  <div ref="container" class="viewer-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

const props = defineProps({
  pointData: { type: Object, default: null },
  pointSize: { type: Number, default: 0.02 }
})

const container = ref(null)
let scene, camera, renderer, controls, pointCloud, material

function initScene() {
  const el = container.value
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0f0f13)

  camera = new THREE.PerspectiveCamera(60, el.clientWidth / el.clientHeight, 0.1, 1000)
  camera.position.set(2, 1, 3)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(el.clientWidth, el.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  el.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.1

  const gridHelper = new THREE.GridHelper(5, 20, 0x444444, 0x333333)
  scene.add(gridHelper)

  animate()
}

function animate() {
  if (!renderer) return
  requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

function loadPointCloud(data) {
  if (!data || !data.vertices) return
  if (pointCloud) scene.remove(pointCloud)

  const positions = new Float32Array(data.vertices.length * 3)
  const colors = new Float32Array(data.vertices.length * 3)

  for (let i = 0; i < data.vertices.length; i++) {
    const v = data.vertices[i]
    positions[i * 3] = v[0]
    positions[i * 3 + 1] = v[1]
    positions[i * 3 + 2] = v[2]
    colors[i * 3] = v[3] / 255
    colors[i * 3 + 1] = v[4] / 255
    colors[i * 3 + 2] = v[5] / 255
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  material = new THREE.PointsMaterial({
    size: props.pointSize,
    vertexColors: true,
    sizeAttenuation: true
  })

  pointCloud = new THREE.Points(geometry, material)
  scene.add(pointCloud)

  const box = new THREE.Box3().setFromObject(pointCloud)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z) || 1
  camera.position.set(center.x + maxDim, center.y + maxDim * 0.5, center.z + maxDim)
  controls.target.copy(center)
  controls.update()
}

function updatePointSize(size) {
  if (material) {
    material.size = size
    material.needsUpdate = true
  }
}

function onResize() {
  if (!container.value || !renderer) return
  const w = container.value.clientWidth
  const h = container.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

watch(() => props.pointData, (newData) => {
  if (newData) loadPointCloud(newData)
})

watch(() => props.pointSize, (newSize) => {
  updatePointSize(newSize)
})

onMounted(() => {
  initScene()
  window.addEventListener('resize', onResize)
  if (props.pointData) loadPointCloud(props.pointData)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (renderer) {
    container.value?.removeChild(renderer.domElement)
    renderer.dispose()
  }
})
</script>

<style scoped>
.viewer-container { width: 100%; height: 100%; }
</style>
