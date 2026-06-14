<script setup lang="ts">
const proxyStore = useProxyStore()
const poolStore = usePoolStore()
const ws = useWebSocket()

const stats = computed(() => [
  { label: 'Requests Today', value: proxyStore.requestsServed, color: 'var(--accent)' },
  { label: 'Rate Limits', value: proxyStore.rateLimitsDetected, color: 'var(--warning)' },
  { label: 'Rotations', value: proxyStore.rotationsPerformed, color: 'var(--success)' },
  { label: 'Active Proxies', value: poolStore.alive, color: 'var(--success)' },
])

onMounted(() => {
  proxyStore.fetchStatus()
  poolStore.fetchStats()
})
</script>

<template>
  <div class="dashboard">
    <div class="status-card">
      <div class="status-indicator">
        <span class="status-dot" :class="proxyStore.running ? 'running' : 'stopped'" />
        <span class="status-text">{{ proxyStore.running ? 'Proxy Running' : 'Proxy Stopped' }}</span>
      </div>
      <div v-if="proxyStore.currentIp" class="current-ip-display">
        <span class="ip-label">Current IP</span>
        <span class="ip-value">{{ proxyStore.currentIp }}</span>
        <button class="copy-btn" title="Copy IP" @click="navigator.clipboard.writeText(proxyStore.currentIp ?? '')">
          Copy
        </button>
      </div>
      <div class="quick-actions">
        <button class="btn btn-primary" @click="proxyStore.running ? proxyStore.stopProxy() : proxyStore.startProxy()">
          {{ proxyStore.running ? 'Stop' : 'Start' }}
        </button>
        <button class="btn btn-secondary" :disabled="!proxyStore.running" @click="proxyStore.rotate()">
          Rotate
        </button>
      </div>
    </div>
    <div class="stats-grid">
      <div v-for="s in stats" :key="s.label" class="stat-card">
        <span class="stat-value" :style="{ color: s.color }">{{ s.value }}</span>
        <span class="stat-label">{{ s.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px;
}

.status-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-text {
  font-size: 16px;
  font-weight: 600;
}

.current-ip-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ip-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.ip-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
}

.copy-btn {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--accent);
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 13px;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
