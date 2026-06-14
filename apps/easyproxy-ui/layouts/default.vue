<script setup lang="ts">
const proxyStore = useProxyStore()
const { data: health } = await useFetch('/health')
const appVersion = health.value?.version ?? '0.1.0'

const navItems = [
  { label: 'Dashboard', icon: '◉', to: '/' },
  { label: 'Proxy Manager', icon: '⊞', to: '/proxy' },
  { label: 'Residential', icon: '⬡', to: '/residential' },
  { label: 'Settings', icon: '⚙', to: '/settings' },
  { label: 'Logs', icon: '☰', to: '/logs' },
]

const isCollapsed = ref(false)

onMounted(() => {
  proxyStore.fetchStatus()
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <span class="sidebar-logo">EasyProxy</span>
        <span class="sidebar-version">v{{ appVersion }}</span>
      </div>
      <nav class="sidebar-nav">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: $route.path === item.to }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </NuxtLink>
      </nav>
      <div class="sidebar-footer">
        <span class="status-dot" :class="proxyStore.running ? 'running' : 'stopped'" />
        <span class="footer-status">
          {{ proxyStore.running ? 'Proxy Running' : 'Proxy Stopped' }}
        </span>
      </div>
    </aside>
    <main class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ navItems.find(n => $route.path === n.to)?.label ?? 'Dashboard' }}</span>
        </div>
        <div class="topbar-right">
          <div v-if="proxyStore.currentIp" class="current-ip" title="Current IP">
            <span class="status-dot running" />
            {{ proxyStore.currentIp }}
          </div>
        </div>
      </header>
      <div class="page-content">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  color: var(--text-sidebar);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.sidebar-logo {
  font-size: 18px;
  font-weight: 700;
  display: block;
}

.sidebar-version {
  font-size: 11px;
  color: var(--text-sidebar-muted);
  margin-top: 2px;
  display: block;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--text-sidebar-muted);
  text-decoration: none;
  transition: all 0.15s;
  font-size: 14px;
}

.nav-item:hover {
  background: rgba(255,255,255,0.06);
  color: var(--text-sidebar);
}

.nav-item.active {
  background: var(--accent);
  color: #fff;
}

.nav-icon {
  width: 20px;
  text-align: center;
  font-size: 14px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-sidebar-muted);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  height: var(--topbar-height);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-primary);
  flex-shrink: 0;
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
}

.current-ip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
