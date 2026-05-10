import { createRouter, createWebHistory } from 'vue-router'
import UploadPage from '../views/UploadPage.vue'
import ProcessingPage from '../views/ProcessingPage.vue'
import ViewerPage from '../views/ViewerPage.vue'
const routes = [
  { path: '/', name: 'Upload', component: UploadPage },
  { path: '/processing/:sid', name: 'Processing', component: ProcessingPage },
  { path: '/viewer/:sid', name: 'Viewer', component: ViewerPage },
]
const router = createRouter({ history: createWebHistory(), routes })
export default router
