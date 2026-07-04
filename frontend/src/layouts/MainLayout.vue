<template>
  <div class="layout-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">Rx</div>
        <div>
          <div class="brand-title">社区药店</div>
          <div class="brand-subtitle">用药安全辅助</div>
        </div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="is-active"
        >
          <span class="nav-dot" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <button class="settings-entry" title="系统设置" type="button" @click="settingVisible = true">
        <span class="settings-icon">⚙</span>
        <span>系统设置</span>
      </button>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <section class="topbar-card">
          <div>
            <div class="topbar-title">社区药店多智能体用药安全辅助系统</div>
            <div class="topbar-subtitle">面向药师柜台场景，辅助完成用药风险评估、症状问诊、候选药对比与审计追溯。</div>
          </div>
        </section>
      </header>

      <main class="content-shell">
        <RouterView :key="$route.fullPath" />
      </main>
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
  { path: '/debug', label: '审计追溯中心' },
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
  grid-template-columns: 228px 1fr;
}

.sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px 14px 22px;
  background: linear-gradient(180deg, #15397b 0%, #0f2d63 100%);
  color: #fff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.1);
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 13px;
  background: #fff;
  color: #15397b;
  font-weight: 850;
}

.brand-title {
  font-size: 18px;
  font-weight: 850;
}

.brand-subtitle {
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.84);
  font-size: 13px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item,
.settings-entry {
  display: flex;
  align-items: center;
  gap: 9px;
  border-radius: 13px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.nav-item {
  padding: 12px 13px;
}

.nav-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.42);
}

.nav-item:hover,
.nav-item.is-active,
.settings-entry:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.nav-item.is-active .nav-dot {
  background: #7dd3fc;
}

.settings-entry {
  width: 100%;
  margin-top: auto;
  min-height: 38px;
  padding: 8px 13px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  cursor: pointer;
}

.settings-icon {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
}

.main-shell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  padding: 16px 20px 0;
}

.topbar-card {
  width: min(100%, 1240px);
  margin: 0 auto;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(10px);
}

.topbar-title {
  color: var(--color-primary-dark);
  font-size: 20px;
  font-weight: 850;
}

.topbar-subtitle {
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.content-shell {
  padding: 20px 20px 28px;
}

@media (max-width: 1080px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    height: auto;
  }

  .nav-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .settings-entry {
    margin-top: 16px;
  }
}

@media (max-width: 640px) {
  .nav-list {
    grid-template-columns: 1fr;
  }
}
</style>
