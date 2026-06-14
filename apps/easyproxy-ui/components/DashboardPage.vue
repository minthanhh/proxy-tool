<script setup lang="ts">
import { ProxyStatusCard, StatsGrid, RequestTimelineChart, RecentLogsList } from 'ui'

interface LogEntry {
  id: number
  timestamp: string
  method: string
  url: string
  status_code: number
  proxy_ip: string
  duration_ms: number
  rate_limited: boolean
}

const proxyStore = useProxyStore()
const poolStore = usePoolStore()
const ws = useWebSocket()
const router = useRouter()

const starting = ref(false)
const stopping = ref(false)
const rotating = ref(false)
const liveTail = ref(true)
const loading = ref(true)

const recentLogs = ref<LogEntry[]>([])

const timelineData = computed(() => {
  const now = Date.now()
  const buckets: { time: string; value: number }[] = []
  for (let i = 11; i >= 0; i--) {
    const t = new Date(now - i * 5 * 60000)
    buckets.push({
      time: t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      value: 0,
    })
  }
  for (const log of recentLogs.value) {
    const logT = new Date(log.timestamp).getTime()
    const idx = Math.floor((logT - (now - 60 * 60000)) / (5 * 60000))
    if (idx >= 0 && idx < 12) buckets[idx].value++
  }
  return buckets
})

onMounted(async () => {
  await Promise.all([
    proxyStore.fetchStatus(),
    poolStore.fetchStats(),
    fetchRecentLogs(),
  ])
  loading.value = false
})

ws.on('request_log', (data: any) => {
  recentLogs.value.unshift({
    id: data.id,
    timestamp: data.timestamp,
    method: data.method,
    url: data.url,
    status_code: data.status_code,
    proxy_ip: data.proxy_ip,
    duration_ms: data.duration_ms,
    rate_limited: data.rate_limited ?? false,
  })
  if (recentLogs.value.length > 50) {
    recentLogs.value = recentLogs.value.slice(0, 50)
  }
})

async function fetchRecentLogs() {
  try {
    const data: any = await $fetch('/api/v1/proxy/logs?limit=20')
    recentLogs.value = (data.logs ?? []).map((l: any) => ({
      id: l.id,
      timestamp: l.timestamp,
      method: l.method,
      url: l.url,
      status_code: l.status_code,
      proxy_ip: l.proxy_ip,
      duration_ms: l.duration_ms,
      rate_limited: l.rate_limited ?? false,
    }))
  } catch {
    // API not ready yet
  }
}

async function handleStart() {
  starting.value = true
  try {
    await proxyStore.startProxy()
  } finally {
    starting.value = false
  }
}

async function handleStop() {
  stopping.value = true
  try {
    await proxyStore.stopProxy()
  } finally {
    stopping.value = false
  }
}

async function handleRotate() {
  rotating.value = true
  try {
    await proxyStore.rotate()
  } finally {
    rotating.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
  if (e.code === 'Space') {
    e.preventDefault()
    proxyStore.running ? handleStop() : handleStart()
  } else if (e.code === 'KeyR' && !e.ctrlKey && !e.metaKey) {
    e.preventDefault()
    if (proxyStore.running) handleRotate()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="dashboard-page">
    <!-- Skeleton loading -->
    <div v-if="loading" class="skeleton-grid">
      <div class="skeleton-card wide" />
      <div class="skeleton-row">
        <div v-for="n in 4" :key="n" class="skeleton-card" />
      </div>
      <div class="skeleton-card tall" />
      <div class="skeleton-card tall" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!proxyStore.running && proxyStore.requestsServed === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <path d="M8 21h8M12 17v4"/>
        </svg>
      </div>
      <h2 class="empty-title">Proxy is not running</h2>
      <p class="empty-desc">Start the proxy to see your stats, request logs, and real-time dashboard.</p>
      <button class="empty-start-btn" :disabled="starting" @click="handleStart">
        <span v-if="starting" class="spinner" />
        <span v-else>Start Proxy</span>
      </button>
    </div>

    <!-- Dashboard content -->
    <template v-else>
      <ProxyStatusCard
        :running="proxyStore.running"
        :current-ip="proxyStore.currentIp"
        :strategy="proxyStore.strategy"
        :uptime-seconds="proxyStore.uptimeSeconds"
        :starting="starting"
        :stopping="stopping"
        :rotating="rotating"
        @start="handleStart"
        @stop="handleStop"
        @rotate="handleRotate"
      />

      <StatsGrid
        :requests="proxyStore.requestsServed"
        :rate-limits="proxyStore.rateLimitsDetected"
        :rotations="proxyStore.rotationsPerformed"
        :active-proxies="poolStore.alive"
        @navigate="router.push('/logs')"
      />

      <RequestTimelineChart :data="timelineData" />

      <RecentLogsList
        :logs="recentLogs"
        :live-tail="liveTail"
        @update:live-tail="liveTail = $event"
        @view-all="router.push('/logs')"
      />
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Skeleton */
.skeleton-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.skeleton-card {
  background: var(--bg-secondary);
  border-radius: 10px;
  height: 80px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-card.wide {
  height: 64px;
}

.skeleton-card.tall {
  height: 120px;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.empty-desc {
  font-size: 13px;
  color: var(--text-secondary);
  max-width: 320px;
  line-height: 1.5;
  margin-bottom: 24px;
}

.empty-start-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 13px;
  background: var(--accent);
  color: #fff;
  min-width: 140px;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}

.empty-start-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.empty-start-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
