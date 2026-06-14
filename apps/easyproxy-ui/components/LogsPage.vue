<script setup lang="ts">
import { LogFilterBar, LogTable, RotationHistoryTable } from 'ui'
import type { LogEntry } from 'ui'
import type { RotationEntry } from 'ui'

const ws = useWebSocket()
const activeTab = ref<'requests' | 'rotations'>('requests')

const logs = ref<LogEntry[]>([])
const rotations = ref<RotationEntry[]>([])
const loading = ref(false)
const logPage = ref(1)
const logTotal = ref(0)
const perPage = 50

const filters = reactive({
  since: '',
  until: '',
  methods: [] as string[],
  statusMin: '',
  statusMax: '',
  urlSearch: '',
  proxyIp: '',
  rateLimitedOnly: false,
})

const liveTail = ref(false)

const hasMoreLogs = computed(() => logs.value.length < logTotal.value)

async function fetchLogs(page = 1, append = false) {
  loading.value = true
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('per_page', String(perPage))
  if (filters.since) params.set('since', new Date(filters.since).toISOString())
  if (filters.until) params.set('until', new Date(filters.until).toISOString())
  if (filters.methods.length > 0) params.set('method', filters.methods.join(','))
  if (filters.statusMin) params.set('status_min', filters.statusMin)
  if (filters.statusMax) params.set('status_max', filters.statusMax)
  if (filters.urlSearch) params.set('search', filters.urlSearch)
  if (filters.proxyIp) params.set('proxy_address', filters.proxyIp)
  if (filters.rateLimitedOnly) params.set('rate_limited', 'true')

  try {
    if (activeTab.value === 'requests') {
      const res: any = await $fetch(`/api/v1/proxy/logs?${params}`)
      const entries = (res.logs ?? []).map((l: any) => ({
        id: l.id,
        timestamp: l.timestamp,
        method: l.method,
        url: l.url,
        status_code: l.status_code,
        proxy_id: l.proxy_id ?? null,
        proxy_address: l.proxy_address ?? null,
        duration_ms: l.duration_ms,
        bytes_sent: l.bytes_sent ?? 0,
        bytes_received: l.bytes_received ?? 0,
        user_agent: l.user_agent ?? null,
        rotated: l.rotated ?? false,
      }))
      if (append) {
        logs.value.push(...entries)
      } else {
        logs.value = entries
      }
      logTotal.value = res.total ?? 0
    } else {
      const res: any = await $fetch(`/api/v1/rotation-log?${params}`)
      rotations.value = (res.rotations ?? []).map((r: any) => ({
        id: r.id,
        timestamp: r.timestamp,
        reason: r.reason,
        trigger: r.trigger,
        from_proxy_id: r.from_proxy_id ?? null,
        from_proxy: r.from_proxy ?? null,
        to_proxy_id: r.to_proxy_id ?? null,
        to_proxy: r.to_proxy ?? null,
        retry_after_seconds: r.retry_after_seconds ?? null,
        request_url: r.request_url ?? null,
        retry_success: r.retry_success ?? null,
      }))
      logTotal.value = res.total ?? 0
    }
  } catch {
    if (!append) {
      logs.value = []
      rotations.value = []
    }
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  logPage.value = 1
  fetchLogs(1)
}

function resetFilters() {
  filters.since = ''
  filters.until = ''
  filters.methods = []
  filters.statusMin = ''
  filters.statusMax = ''
  filters.urlSearch = ''
  filters.proxyIp = ''
  filters.rateLimitedOnly = false
  applyFilters()
}

function loadMore() {
  if (hasMoreLogs.value && !loading.value) {
    logPage.value++
    fetchLogs(logPage.value, true)
  }
}

function switchTab(tab: 'requests' | 'rotations') {
  activeTab.value = tab
  logPage.value = 1
  fetchLogs(1)
}

async function exportCsv() {
  const params = new URLSearchParams()
  if (filters.since) params.set('since', new Date(filters.since).toISOString())
  if (filters.until) params.set('until', new Date(filters.until).toISOString())
  params.set('format', 'csv')

  try {
    const blob = await $fetch(`/api/v1/proxy/logs/export?${params}`, { responseType: 'blob' })
    const url = URL.createObjectURL(blob as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `easyproxy-logs-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // silent
  }
}

ws.on('request_log', (data: any) => {
  if (!liveTail.value) return
  const entry: LogEntry = {
    id: Date.now(),
    timestamp: data.timestamp ?? new Date().toISOString(),
    method: data.method,
    url: data.url,
    status_code: data.status_code,
    proxy_id: null,
    proxy_address: data.proxy_address ?? null,
    duration_ms: data.duration_ms ?? 0,
    bytes_sent: 0,
    bytes_received: 0,
    user_agent: null,
    rotated: false,
  }
  logs.value.unshift(entry)
  logTotal.value++
})

ws.on('rotation_completed', () => {
  if (activeTab.value === 'rotations') {
    fetchLogs(logPage.value)
  }
})

onMounted(() => fetchLogs())

const proxyOptions = computed(() => {
  const ips = new Set<string>()
  for (const log of logs.value) {
    if (log.proxy_address) ips.add(log.proxy_address)
  }
  return Array.from(ips).sort()
})
</script>

<template>
  <div class="logs-page">
    <!-- Tabs -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'requests' }"
        @click="switchTab('requests')"
      >
        Request Logs
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'rotations' }"
        @click="switchTab('rotations')"
      >
        Rotation History
      </button>

      <div class="tab-actions">
        <label v-if="activeTab === 'requests'" class="live-tail-toggle" title="Auto-append new logs">
          <input v-model="liveTail" type="checkbox">
          <span>Live</span>
        </label>
        <button
          v-if="activeTab === 'requests'"
          class="export-btn"
          @click="exportCsv"
        >
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <LogFilterBar
      v-if="activeTab === 'requests'"
      :filters="filters"
      :proxy-options="proxyOptions"
      @update:filters="Object.assign(filters, $event)"
      @apply="applyFilters"
      @reset="resetFilters"
    />

    <!-- Table -->
    <LogTable
      v-if="activeTab === 'requests'"
      :logs="logs"
      :loading="loading"
      :has-more="hasMoreLogs"
      @load-more="loadMore"
    />

    <RotationHistoryTable
      v-else
      :rotations="rotations"
      :loading="loading"
    />
  </div>
</template>

<style scoped>
.logs-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: flex;
  align-items: center;
  gap: 0;
  border-bottom: 2px solid var(--border);
  padding-bottom: 0;
}

.tab {
  padding: 10px 20px;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  transition: color 0.1s, border-color 0.1s;
}

.tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab:hover:not(.active) {
  color: var(--text-primary);
}

.tab-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-tail-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
}

.live-tail-toggle input {
  accent-color: var(--accent);
}

.export-btn {
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.1s;
}

.export-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
