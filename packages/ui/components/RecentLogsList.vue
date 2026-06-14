<script setup lang="ts">
export interface LogEntry {
  id: number
  timestamp: string
  method: string
  url: string
  status_code: number
  proxy_ip: string
  duration_ms: number
  rate_limited: boolean
}

const props = defineProps<{
  logs: LogEntry[]
  liveTail: boolean
}>()

const emit = defineEmits<{
  'update:liveTail': [value: boolean]
  viewLog: [log: LogEntry]
  viewAll: []
}>()

const listRef = ref<HTMLElement | null>(null)
const userScrolled = ref(false)

function statusClass(code: number): string {
  if (code < 300) return 'status-2xx'
  if (code < 400) return 'status-3xx'
  if (code < 500) return 'status-4xx'
  return 'status-5xx'
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return ts
  }
}

watch(() => props.logs.length, () => {
  if (props.liveTail && !userScrolled.value) {
    nextTick(() => {
      if (listRef.value) {
        listRef.value.scrollTop = listRef.value.scrollHeight
      }
    })
  }
})

function onScroll() {
  if (!listRef.value) return
  const el = listRef.value
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
  userScrolled.value = !atBottom
}

function scrollToBottom() {
  userScrolled.value = false
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
}

const selectedLog = ref<LogEntry | null>(null)

function toggleDetail(log: LogEntry) {
  selectedLog.value = selectedLog.value?.id === log.id ? null : log
}
</script>

<template>
  <div class="recent-logs">
    <div class="logs-header">
      <span class="logs-title">Recent Logs</span>
      <div class="logs-actions">
        <label class="live-tail-toggle" title="Auto-scroll new entries">
          <input type="checkbox" :checked="liveTail" @change="emit('update:liveTail', ($event.target as HTMLInputElement).checked)">
          <span>Live Tail</span>
        </label>
        <button class="view-all-link" @click="emit('viewAll')">View all</button>
      </div>
    </div>

    <div
      ref="listRef"
      class="logs-list"
      @scroll="onScroll"
    >
      <div v-if="logs.length === 0" class="logs-empty">
        No logs yet. Start the proxy to see request logs.
      </div>
      <div
        v-for="log in logs"
        v-else
        :key="log.id"
        class="log-row"
        :class="{ selected: selectedLog?.id === log.id }"
        @click="toggleDetail(log)"
      >
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <span class="log-method">{{ log.method }}</span>
        <span class="log-url">{{ log.url }}</span>
        <span class="log-status" :class="statusClass(log.status_code)">{{ log.status_code }}</span>
        <span class="log-duration">{{ log.duration_ms }}ms</span>
        <span v-if="log.rate_limited" class="log-rate-limited" title="Rate limited">RL</span>
        <span class="log-ip">{{ log.proxy_ip }}</span>

        <div v-if="selectedLog?.id === log.id" class="log-detail">
          <div class="detail-row">
            <span class="detail-label">Time</span>
            <span>{{ log.timestamp }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Proxy</span>
            <code>{{ log.proxy_ip }}</code>
          </div>
          <div class="detail-row">
            <span class="detail-label">Duration</span>
            <span>{{ log.duration_ms }}ms</span>
          </div>
          <div v-if="log.rate_limited" class="detail-row warn">
            Rate limited — request was blocked
          </div>
        </div>
      </div>
    </div>

    <div v-if="userScrolled && liveTail" class="scroll-hint">
      <button class="scroll-btn" @click="scrollToBottom">
        New logs below ↓
      </button>
    </div>
  </div>
</template>

<style scoped>
.recent-logs {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  position: relative;
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.logs-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.logs-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.view-all-link {
  font-size: 11px;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.view-all-link:hover {
  text-decoration: underline;
}

.logs-list {
  max-height: 280px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logs-empty {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 24px 0;
  text-align: center;
}

.log-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  cursor: pointer;
  flex-wrap: wrap;
  position: relative;
}

.log-row:hover {
  background: var(--bg-secondary);
}

.log-row.selected {
  background: var(--bg-secondary);
}

.log-time {
  color: var(--text-secondary);
  flex-shrink: 0;
  width: 64px;
}

.log-method {
  font-weight: 600;
  color: var(--text-primary);
  width: 40px;
  flex-shrink: 0;
}

.log-url {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  min-width: 80px;
}

.log-status {
  font-weight: 600;
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}

.status-2xx { color: var(--success); }
.status-3xx { color: var(--accent); }
.status-4xx { color: var(--warning); }
.status-5xx { color: var(--danger); }

.log-duration {
  color: var(--text-secondary);
  width: 48px;
  text-align: right;
  flex-shrink: 0;
}

.log-rate-limited {
  font-size: 9px;
  font-weight: 700;
  color: var(--danger);
  background: var(--bg-secondary);
  padding: 1px 4px;
  border-radius: 3px;
}

.log-ip {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.log-detail {
  width: 100%;
  padding: 8px;
  margin-top: 4px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.detail-label {
  color: var(--text-secondary);
  width: 60px;
  flex-shrink: 0;
}

.detail-row.warn {
  color: var(--warning);
  font-weight: 500;
}

.scroll-hint {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
}

.scroll-btn {
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--accent);
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.scroll-btn:hover {
  background: var(--bg-secondary);
}
</style>
