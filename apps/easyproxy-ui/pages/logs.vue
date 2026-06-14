<script setup lang="ts">
const activeTab = ref<'requests' | 'rotations'>('requests')
const logs = ref<any[]>([])
const rotations = ref<any[]>([])
const loading = ref(false)

const filters = reactive({
  status: '',
  method: '',
  since: '',
  until: '',
})

async function fetchLogs() {
  loading.value = true
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.method) params.set('method', filters.method)
  if (filters.since) params.set('since', filters.since)
  if (filters.until) params.set('until', filters.until)
  params.set('per_page', '50')

  try {
    if (activeTab.value === 'requests') {
      const res: any = await $fetch(`/api/v1/proxy/logs?${params}`)
      logs.value = res.logs ?? []
    } else {
      const res: any = await $fetch(`/api/v1/rotation-log?${params}`)
      rotations.value = res.rotations ?? []
    }
  } catch {
    logs.value = []
    rotations.value = []
  } finally {
    loading.value = false
  }
}

async function exportCsv() {
  const params = new URLSearchParams()
  if (filters.since) params.set('since', filters.since)
  if (filters.until) params.set('until', filters.until)
  params.set('format', 'csv')

  const blob = await $fetch(`/api/v1/proxy/logs/export?${params}`, { responseType: 'blob' })
  const url = URL.createObjectURL(blob as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `easyproxy-logs-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(fetchLogs)
</script>

<template>
  <div class="logs-page">
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'requests' }"
        @click="activeTab = 'requests'; fetchLogs()"
      >
        Request Logs
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'rotations' }"
        @click="activeTab = 'rotations'; fetchLogs()"
      >
        Rotation History
      </button>
    </div>
    <div class="filter-bar">
      <input v-model="filters.method" class="filter-input" placeholder="Method (GET, POST...)" @input="fetchLogs">
      <input v-model="filters.status" class="filter-input" placeholder="Status (200, 429...)" @input="fetchLogs">
      <input v-model="filters.since" type="date" class="filter-input" @change="fetchLogs">
      <input v-model="filters.until" type="date" class="filter-input" @change="fetchLogs">
      <button class="btn btn-secondary" @click="exportCsv">Export CSV</button>
    </div>
    <div class="log-table-wrapper">
      <table v-if="activeTab === 'requests'" class="log-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Method</th>
            <th>URL</th>
            <th>Status</th>
            <th>Proxy</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td class="cell-mono">{{ new Date(log.timestamp).toLocaleTimeString() }}</td>
            <td>{{ log.method }}</td>
            <td class="cell-url">{{ log.url }}</td>
            <td>
              <span class="status-badge" :class="{
                'status-2xx': log.status_code >= 200 && log.status_code < 300,
                'status-4xx': log.status_code >= 400 && log.status_code < 500,
                'status-5xx': log.status_code >= 500,
              }">
                {{ log.status_code }}
              </span>
            </td>
            <td class="cell-mono">{{ log.proxy_address ?? '—' }}</td>
            <td>{{ log.duration_ms }}ms</td>
          </tr>
        </tbody>
      </table>
      <table v-else class="log-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Reason</th>
            <th>From</th>
            <th>To</th>
            <th>Request</th>
            <th>Success</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rotations" :key="r.id">
            <td class="cell-mono">{{ new Date(r.timestamp).toLocaleTimeString() }}</td>
            <td>
              <span class="reason-badge" :class="'reason-' + r.reason">{{ r.reason }}</span>
            </td>
            <td class="cell-mono">{{ r.from_proxy ?? '—' }}</td>
            <td class="cell-mono">{{ r.to_proxy ?? '—' }}</td>
            <td class="cell-url">{{ r.request_url ?? '—' }}</td>
            <td>{{ r.retry_success ? '✓' : (r.retry_success === false ? '✗' : '—') }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="loading">Loading...</div>
    </div>
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
  gap: 0;
  border-bottom: 2px solid var(--border);
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
}

.tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.filter-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.btn-secondary {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.log-table-wrapper {
  flex: 1;
  overflow-y: auto;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.log-table th {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}

.cell-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.cell-url {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.status-2xx { background: rgba(16,185,129,0.15); color: var(--success); }
.status-4xx { background: rgba(245,158,11,0.15); color: var(--warning); }
.status-5xx { background: rgba(239,68,68,0.15); color: var(--danger); }

.reason-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.reason-rate_limit_429 { background: rgba(239,68,68,0.15); color: var(--danger); }
.reason-manual { background: rgba(59,130,246,0.15); color: var(--accent); }
.reason-scheduled { background: rgba(16,185,129,0.15); color: var(--success); }

.loading {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}
</style>
