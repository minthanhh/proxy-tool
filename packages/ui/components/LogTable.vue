<script setup lang="ts">
export interface LogEntry {
  id: number
  timestamp: string
  method: string
  url: string
  status_code: number
  proxy_id: number | null
  proxy_address: string | null
  duration_ms: number
  bytes_sent: number
  bytes_received: number
  user_agent: string | null
  rotated: boolean
}

const props = defineProps<{
  logs: LogEntry[]
  loading: boolean
  hasMore: boolean
}>()

const emit = defineEmits<{
  viewDetail: [log: LogEntry]
  copyUrl: [url: string]
  loadMore: []
}>()

const selectedId = ref<number | null>(null)

function toggleDetail(log: LogEntry) {
  selectedId.value = selectedId.value === log.id ? null : log.id
}

function statusColor(code: number): string {
  if (code < 300) return 'var(--success)'
  if (code < 400) return 'var(--accent)'
  if (code < 500) return 'var(--warning)'
  return 'var(--danger)'
}

function statusBg(code: number): string {
  if (code < 300) return 'rgba(16,185,129,0.12)'
  if (code < 400) return 'rgba(59,130,246,0.12)'
  if (code < 500) return 'rgba(245,158,11,0.12)'
  return 'rgba(239,68,68,0.12)'
}

function durationWidth(ms: number): number {
  return Math.min((ms / 5000) * 100, 100)
}

function durationColor(ms: number): string {
  if (ms < 500) return 'var(--success)'
  if (ms < 2000) return 'var(--warning)'
  return 'var(--danger)'
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return ts
  }
}

function formatFullTime(ts: string): string {
  try {
    return new Date(ts).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return ts
  }
}

async function copyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(url)
  } catch {
    // silent
  }
}

const sentinelRef = ref<HTMLElement | null>(null)

onMounted(() => {
  if (!sentinelRef.value) return
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && props.hasMore && !props.loading) {
        emit('loadMore')
      }
    },
    { rootMargin: '200px' }
  )
  observer.observe(sentinelRef.value)
  onUnmounted(() => observer.disconnect())
})
</script>

<template>
  <div class="log-table">
    <div class="log-table-header">
      <span class="col-time">Time</span>
      <span class="col-method">Method</span>
      <span class="col-url">URL</span>
      <span class="col-status">Status</span>
      <span class="col-proxy">Proxy</span>
      <span class="col-duration">Duration</span>
    </div>

    <div v-if="loading && logs.length === 0" class="log-empty">
      Loading logs…
    </div>
    <div v-else-if="logs.length === 0" class="log-empty">
      No logs match your filters.
    </div>

    <div
      v-for="log in logs"
      :key="log.id"
      class="log-row"
      :class="{ expanded: selectedId === log.id }"
      @click="toggleDetail(log)"
    >
      <span class="col-time cell-mono">{{ formatTime(log.timestamp) }}</span>
      <span class="col-method cell-mono">{{ log.method }}</span>
      <span class="col-url cell-mono cell-url" :title="log.url">{{ log.url }}</span>
      <span class="col-status">
        <span class="status-badge" :style="{ background: statusBg(log.status_code), color: statusColor(log.status_code) }">
          {{ log.status_code }}
        </span>
      </span>
      <span class="col-proxy cell-mono">{{ log.proxy_address ?? '—' }}</span>
      <span class="col-duration">
        <span class="duration-bar-wrapper">
          <span class="duration-bar" :style="{ width: durationWidth(log.duration_ms) + '%', background: durationColor(log.duration_ms) }" />
        </span>
        <span class="duration-text" :style="{ color: durationColor(log.duration_ms) }">{{ log.duration_ms }}ms</span>
      </span>

      <div v-if="selectedId === log.id" class="log-detail">
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Timestamp</span>
            <span>{{ formatFullTime(log.timestamp) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Method</span>
            <span>{{ log.method }}</span>
          </div>
          <div class="detail-item full-width">
            <span class="detail-label">URL</span>
            <span class="cell-url">{{ log.url }}</span>
            <button class="copy-btn" @click.stop="copyUrl(log.url)" title="Copy URL">Copy</button>
          </div>
          <div class="detail-item">
            <span class="detail-label">Status</span>
            <span :style="{ color: statusColor(log.status_code) }">{{ log.status_code }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Duration</span>
            <span>{{ log.duration_ms }}ms</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Proxy</span>
            <code>{{ log.proxy_address ?? '—' }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">Sent</span>
            <span>{{ log.bytes_sent }} B</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Received</span>
            <span>{{ log.bytes_received }} B</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Rotated</span>
            <span>{{ log.rotated ? 'Yes' : 'No' }}</span>
          </div>
          <div v-if="log.user_agent" class="detail-item full-width">
            <span class="detail-label">User-Agent</span>
            <span class="cell-mono ua-text">{{ log.user_agent }}</span>
          </div>
        </div>
      </div>
    </div>

    <div ref="sentinelRef" class="sentinel" />

    <div v-if="loading && logs.length > 0" class="log-loading-more">
      Loading more…
    </div>
  </div>
</template>

<style scoped>
.log-table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  overflow: hidden;
}

.log-table-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-secondary);
}

.log-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.1s;
}

.log-row:hover {
  background: var(--bg-secondary);
}

.log-row.expanded {
  background: var(--bg-secondary);
}

.col-time { width: 64px; flex-shrink: 0; }
.col-method { width: 44px; flex-shrink: 0; font-weight: 600; }
.col-url { flex: 1; min-width: 100px; }
.col-status { width: 52px; flex-shrink: 0; text-align: center; }
.col-proxy { width: 130px; flex-shrink: 0; }
.col-duration { width: 100px; flex-shrink: 0; display: flex; align-items: center; gap: 6px; }

.cell-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.cell-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 600;
  font-size: 11px;
}

.duration-bar-wrapper {
  width: 40px;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}

.duration-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s;
}

.duration-text {
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.log-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.log-detail {
  width: 100%;
  padding: 12px;
  margin-top: 4px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.ua-text {
  font-size: 11px;
  word-break: break-all;
}

.copy-btn {
  background: none;
  border: 1px solid var(--border);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  color: var(--accent);
  cursor: pointer;
  margin-top: 4px;
  width: fit-content;
}

.copy-btn:hover {
  background: var(--bg-secondary);
}

.sentinel {
  height: 1px;
}

.log-loading-more {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
