<script setup lang="ts">
export interface RotationEntry {
  id: number
  timestamp: string
  reason: string
  trigger: string
  from_proxy_id: number | null
  from_proxy: string | null
  to_proxy_id: number | null
  to_proxy: string | null
  retry_after_seconds: number | null
  request_url: string | null
  retry_success: boolean | null
}

const props = defineProps<{
  rotations: RotationEntry[]
  loading: boolean
}>()

const selectedId = ref<number | null>(null)

function toggleDetail(r: RotationEntry) {
  selectedId.value = selectedId.value === r.id ? null : r.id
}

function reasonColor(reason: string): string {
  if (reason === 'manual') return 'var(--accent)'
  if (reason === 'rate_limit_429') return 'var(--danger)'
  if (reason === 'scheduled') return 'var(--success)'
  if (reason === 'error') return 'var(--warning)'
  return 'var(--text-secondary)'
}

function reasonBg(reason: string): string {
  if (reason === 'manual') return 'rgba(59,130,246,0.12)'
  if (reason === 'rate_limit_429') return 'rgba(239,68,68,0.12)'
  if (reason === 'scheduled') return 'rgba(16,185,129,0.12)'
  if (reason === 'error') return 'rgba(245,158,11,0.12)'
  return 'rgba(107,114,128,0.12)'
}

function reasonLabel(reason: string): string {
  const map: Record<string, string> = {
    manual: 'Manual',
    rate_limit_429: 'Rate Limit',
    scheduled: 'Scheduled',
    error: 'Error',
    startup: 'Startup',
  }
  return map[reason] ?? reason
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
    return new Date(ts).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
  } catch {
    return ts
  }
}
</script>

<template>
  <div class="rotation-table">
    <div class="rotation-table-header">
      <span class="col-time">Time</span>
      <span class="col-reason">Reason</span>
      <span class="col-from">From</span>
      <span class="col-to">To</span>
      <span class="col-result">Result</span>
    </div>

    <div v-if="loading && rotations.length === 0" class="rot-empty">
      Loading rotation history…
    </div>
    <div v-else-if="rotations.length === 0" class="rot-empty">
      No rotations recorded yet.
    </div>

    <div
      v-for="r in rotations"
      :key="r.id"
      class="rotation-row"
      :class="{ expanded: selectedId === r.id }"
      @click="toggleDetail(r)"
    >
      <span class="col-time cell-mono">{{ formatTime(r.timestamp) }}</span>
      <span class="col-reason">
        <span class="reason-badge" :style="{ background: reasonBg(r.reason), color: reasonColor(r.reason) }">
          {{ reasonLabel(r.reason) }}
        </span>
      </span>
      <span class="col-from cell-mono">{{ r.from_proxy ?? '—' }}</span>
      <span class="col-to cell-mono">{{ r.to_proxy ?? '—' }}</span>
      <span class="col-result">
        <span v-if="r.retry_success === true" class="result-ok">✓</span>
        <span v-else-if="r.retry_success === false" class="result-fail">✗</span>
        <span v-else class="result-na">—</span>
      </span>

      <div v-if="selectedId === r.id" class="rotation-detail">
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Timestamp</span>
            <span>{{ formatFullTime(r.timestamp) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Trigger</span>
            <span>{{ r.trigger }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">From</span>
            <code>{{ r.from_proxy ?? '—' }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">To</span>
            <code>{{ r.to_proxy ?? '—' }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">Retry-After</span>
            <span>{{ r.retry_after_seconds ? `${r.retry_after_seconds}s` : 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Retry Success</span>
            <span>{{ r.retry_success === true ? 'Yes' : r.retry_success === false ? 'No' : 'N/A' }}</span>
          </div>
          <div v-if="r.request_url" class="detail-item full-width">
            <span class="detail-label">Request URL</span>
            <span class="cell-mono url-text">{{ r.request_url }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rotation-table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  overflow: hidden;
}

.rotation-table-header {
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

.rotation-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.1s;
}

.rotation-row:hover {
  background: var(--bg-secondary);
}

.rotation-row.expanded {
  background: var(--bg-secondary);
}

.col-time { width: 64px; flex-shrink: 0; }
.col-reason { width: 90px; flex-shrink: 0; }
.col-from { width: 120px; flex-shrink: 0; }
.col-to { width: 120px; flex-shrink: 0; }
.col-result { width: 36px; flex-shrink: 0; text-align: center; }

.cell-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.reason-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.result-ok { color: var(--success); font-weight: 700; }
.result-fail { color: var(--danger); font-weight: 700; }
.result-na { color: var(--text-secondary); }

.rot-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.rotation-detail {
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

.url-text {
  font-size: 11px;
  word-break: break-all;
}
</style>
