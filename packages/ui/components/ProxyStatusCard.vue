<script setup lang="ts">
const props = defineProps<{
  running: boolean
  currentIp: string
  strategy: string
  uptimeSeconds: number
  starting: boolean
  stopping: boolean
  rotating: boolean
}>()

const emit = defineEmits<{
  start: []
  stop: []
  rotate: []
}>()

const showCopied = ref(false)

async function copyIp() {
  if (!props.currentIp) return
  try {
    await navigator.clipboard.writeText(props.currentIp)
    showCopied.value = true
    setTimeout(() => { showCopied.value = false }, 1500)
  } catch {
    // fallback silent
  }
}

const uptimeFormatted = computed(() => {
  const s = props.uptimeSeconds
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${sec}s`
  return `${sec}s`
})
</script>

<template>
  <div class="proxy-status-card">
    <div class="status-section">
      <div class="status-row">
        <span class="status-dot" :class="running ? 'running' : 'stopped'" />
        <span class="status-label">{{ running ? 'Proxy Running' : 'Proxy Stopped' }}</span>
        <span v-if="running" class="uptime" :title="`Uptime: ${uptimeFormatted}`">
          {{ uptimeFormatted }}
        </span>
      </div>
      <div v-if="running && currentIp" class="ip-row">
        <span class="ip-label">Current IP</span>
        <code class="ip-value">{{ currentIp }}</code>
        <button class="icon-btn" title="Copy IP" @click="copyIp">
          <span v-if="showCopied" class="copied-tip">Copied</span>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
      </div>
      <div v-if="running" class="strategy-badge" :title="`Rotation strategy: ${strategy}`">
        {{ strategy }}
      </div>
    </div>

    <div class="actions-section">
      <button
        class="btn btn-primary"
        :class="{ loading: starting || stopping }"
        :disabled="starting || stopping || rotating"
        :title="running ? 'Stop proxy (Space)' : 'Start proxy (Space)'"
        @click="running ? emit('stop') : emit('start')"
      >
        <span v-if="starting" class="spinner" />
        <span v-else-if="stopping" class="spinner" />
        <span v-else>{{ running ? 'Stop' : 'Start' }}</span>
      </button>
      <button
        class="btn btn-secondary"
        :class="{ rotating: rotating }"
        :disabled="!running || starting || stopping || rotating"
        title="Rotate IP (R)"
        @click="emit('rotate')"
      >
        <svg v-if="rotating" class="spin-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
        Rotate
      </button>
    </div>
  </div>
</template>

<style scoped>
.proxy-status-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-label {
  font-size: 16px;
  font-weight: 600;
}

.uptime {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
}

.ip-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ip-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.ip-value {
  font-size: 13px;
  font-weight: 600;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 4px;
  position: relative;
}

.icon-btn:hover {
  background: var(--bg-secondary);
  color: var(--accent);
}

.copied-tip {
  font-size: 10px;
  color: var(--success);
  white-space: nowrap;
}

.strategy-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  text-transform: capitalize;
  width: fit-content;
}

.actions-section {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 13px;
  transition: opacity 0.15s, transform 0.1s;
}

.btn:active {
  transform: scale(0.97);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  min-width: 72px;
  justify-content: center;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.loading {
  pointer-events: none;
}

.rotating {
  pointer-events: none;
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

.spin-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
