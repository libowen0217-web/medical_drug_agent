<template>
  <div class="layout-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-title">社区药店多智能体</div>
        <div class="brand-subtitle">用药安全辅助系统</div>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="is-active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        面向社区药店、医生与药师的本地辅助工具，聚焦药物安全检查、症状问诊辅助和候选药协作评估。
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <section class="card-shell">
          <div class="card-body topbar-body">
            <div>
              <div class="topbar-title">社区药店多智能体用药安全辅助系统</div>
              <div class="topbar-subtitle">
                统一承接药物搜索、风险检查、症状问诊辅助和候选药评估，调试信息集中放在系统调试页面。
              </div>
            </div>
            <el-button type="primary" plain @click="settingVisible = true">设置</el-button>
          </div>
        </section>
      </header>

      <div class="content-shell">
        <RouterView :key="$route.fullPath" />
      </div>
    </div>

    <SettingDialog v-model="settingVisible" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import SettingDialog from '@/components/common/SettingDialog.vue'
import { useAppStateStore } from '@/stores/appState'

const settingVisible = ref(false)
const route = useRoute()
const store = useAppStateStore()

const navItems = [
  { path: '/drug-safety', label: '用药安全检查' },
  { path: '/symptom-consult', label: '症状问诊辅助' },
  { path: '/medication-debate', label: '候选药协作评估' },
  { path: '/debug', label: '系统调试与审计' },
]

watch(
  () => route.fullPath,
  () => {
    store.resetUiNavigationState()
  },
  { immediate: true }
)
</script>

<style scoped>
.layout-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
}

.sidebar {
  padding: 24px 18px;
  background: linear-gradient(180deg, #15397b 0%, #0f2d63 100%);
  color: #fff;
}

.brand {
  margin-bottom: 28px;
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
}

.brand-title {
  font-size: 22px;
  font-weight: 700;
}

.brand-subtitle {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.86);
  font-size: 14px;
  line-height: 1.6;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-item {
  padding: 14px 16px;
  border-radius: 14px;
  color: rgba(255, 255, 255, 0.88);
  transition: all 0.2s ease;
}

.nav-item:hover,
.nav-item.is-active {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.sidebar-footer {
  margin-top: 24px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  line-height: 1.7;
}

.main-shell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  margin: 20px 20px 0;
}

.topbar-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.topbar-title {
  color: var(--color-primary-dark);
  font-size: 22px;
  font-weight: 700;
}

.topbar-subtitle {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.content-shell {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (max-width: 1080px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    padding-bottom: 12px;
  }

  .topbar-body {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
