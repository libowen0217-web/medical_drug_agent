import { createRouter, createWebHistory } from 'vue-router'

import DrugSafetyView from '@/views/DrugSafetyView.vue'
import SymptomConsultView from '@/views/SymptomConsultView.vue'
import MedicationDebateView from '@/views/MedicationDebateView.vue'
import SystemDebugView from '@/views/SystemDebugView.vue'
import { useAppStateStore } from '@/stores/appState'

const routes = [
  {
    path: '/',
    redirect: '/drug-safety',
  },
  {
    path: '/drug-safety',
    name: 'drug-safety',
    component: DrugSafetyView,
    meta: { title: '用药安全检查' },
  },
  {
    path: '/symptom-consult',
    name: 'symptom-consult',
    component: SymptomConsultView,
    meta: { title: '症状问诊辅助' },
  },
  {
    path: '/medication-debate',
    name: 'medication-debate',
    component: MedicationDebateView,
    meta: { title: '候选药协作评估' },
  },
  {
    path: '/debug',
    name: 'debug',
    component: SystemDebugView,
    meta: { title: '系统调试与审计' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(() => {
  const store = useAppStateStore()
  store.resetUiNavigationState()
  return true
})

export default router
