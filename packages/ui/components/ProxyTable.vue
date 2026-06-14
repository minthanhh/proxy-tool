<script setup lang="ts">
export interface ProxyRow {
  id: number
  address: string
  port: number
  protocol: 'http' | 'https' | 'socks5'
  region: string | null
  status: 'alive' | 'dead' | 'untested'
  latency_ms: number | null
  last_checked_at: string | null
  source: string
  error_count: number
  success_count: number
}

export interface SortState {
  column: string
  direction: 'asc' | 'desc'
}

const props = defineProps<{
  proxies: ProxyRow[]
  sort: SortState
  selectedIds: number[]
  loading: boolean
}>()

const emit = defineEmits<{
  sort: [column: string]
  toggleSelect: [id: number]
  selectAll: []
  edit: [proxy: ProxyRow]
  delete: [id: number]
  test: [ids: number[]]
}>()

const allSelected = computed(() =>
  props.proxies.length > 0 && props.selectedIds.length === props.proxies.length
)

function sortIcon(column: string) {
  if (props.sort.column !== column) return '—'
  return props.sort.direction === 'asc' ? '↑' : '↓'
}

function formatLatency(ms: number | null): string {
  if (ms === null) return '—'
  return `${ms}ms`
}

function latencyWidth(ms: number | null): number {
  if (ms === null) return 0
  return Math.min((ms / 1000) * 100, 100)
}

function latencyColor(ms: number | null): string {
  if (ms === null) return 'var(--text-secondary)'
  if (ms < 200) return 'var(--success)'
  if (ms < 500) return 'var(--warning)'
  return 'var(--danger)'
}

function formatDate(ts: string | null): string {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

const confirmDeleteId = ref<number | null>(null)

function requestDelete(id: number) {
  confirmDeleteId.value = id
}

function confirmDelete() {
  if (confirmDeleteId.value !== null) {
    emit('delete', confirmDeleteId.value)
    confirmDeleteId.value = null
  }
}

function cancelDelete() {
  confirmDeleteId.value = null
}

function protocolColor(p: string): string {
  if (p === 'socks5') return 'var(--accent)'
  if (p === 'https') return 'var(--success)'
  return 'var(--text-secondary)'
}
</script>

<template>
  <div class="proxy-table-wrapper">
    <table class="proxy-table">
      <thead>
        <tr>
          <th class="col-check">
            <input type="checkbox" :checked="allSelected" :indeterminate="selectedIds.length > 0 && !allSelected" @change="emit('selectAll')">
          </th>
          <th class="col-address sortable" @click="emit('sort', 'address')">
            Address <span class="sort-icon">{{ sortIcon('address') }}</span>
          </th>
          <th class="col-protocol sortable" @click="emit('sort', 'protocol')">
            Protocol <span class="sort-icon">{{ sortIcon('protocol') }}</span>
          </th>
          <th class="col-region sortable" @click="emit('sort', 'region')">
            Region <span class="sort-icon">{{ sortIcon('region') }}</span>
          </th>
          <th class="col-status sortable" @click="emit('sort', 'status')">
            Status <span class="sort-icon">{{ sortIcon('status') }}</span>
          </th>
          <th class="col-latency sortable" @click="emit('sort', 'latency_ms')">
            Latency <span class="sort-icon">{{ sortIcon('latency_ms') }}</span>
          </th>
          <th class="col-checked">Last Check</th>
          <th class="col-actions">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading && proxies.length === 0">
          <td colspan="8" class="loading-cell">
            <span class="loading-spinner" />
            Loading proxies…
          </td>
        </tr>
        <tr v-else-if="proxies.length === 0">
          <td colspan="8" class="empty-cell">
            No proxies yet. Add one or import from file.
          </td>
        </tr>
        <tr
          v-for="p in proxies"
          v-else
          :key="p.id"
          class="proxy-row"
        >
          <td class="col-check">
            <input type="checkbox" :checked="selectedIds.includes(p.id)" @change="emit('toggleSelect', p.id)">
          </td>
          <td class="col-address">
            <code class="address-text">{{ p.address }}:{{ p.port }}</code>
          </td>
          <td class="col-protocol">
            <span class="protocol-badge" :style="{ color: protocolColor(p.protocol) }">
              {{ p.protocol.toUpperCase() }}
            </span>
          </td>
          <td class="col-region">
            {{ p.region ?? '—' }}
          </td>
          <td class="col-status">
            <span class="status-indicator">
              <span class="status-dot" :class="p.status" />
              <span class="status-text">{{ p.status }}</span>
            </span>
          </td>
          <td class="col-latency">
            <div v-if="p.latency_ms !== null" class="latency-bar-wrapper">
              <div class="latency-bar" :style="{ width: latencyWidth(p.latency_ms) + '%', background: latencyColor(p.latency_ms) }" />
            </div>
            <span class="latency-text" :style="{ color: latencyColor(p.latency_ms) }">
              {{ formatLatency(p.latency_ms) }}
            </span>
          </td>
          <td class="col-checked">
            <span class="checked-text">{{ formatDate(p.last_checked_at) }}</span>
          </td>
          <td class="col-actions">
            <button class="action-btn" title="Edit" @click="emit('edit', p)">Edit</button>
            <button v-if="confirmDeleteId !== p.id" class="action-btn action-danger" title="Delete" @click="requestDelete(p.id)">Delete</button>
            <template v-else>
              <button class="action-btn action-danger" @click="confirmDelete">Confirm</button>
              <button class="action-btn" @click="cancelDelete">Cancel</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.proxy-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
}

.proxy-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.proxy-table th {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  user-select: none;
}

.proxy-table th.sortable {
  cursor: pointer;
}

.proxy-table th.sortable:hover {
  color: var(--text-primary);
}

.sort-icon {
  display: inline-block;
  width: 12px;
  font-size: 10px;
}

.proxy-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.proxy-row:hover {
  background: var(--bg-secondary);
}

.col-check {
  width: 36px;
  text-align: center;
}

.col-check input[type="checkbox"] {
  accent-color: var(--accent);
}

.address-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.protocol-badge {
  font-size: 11px;
  font-weight: 600;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status-text {
  text-transform: capitalize;
  font-size: 12px;
}

.latency-bar-wrapper {
  width: 60px;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
}

.latency-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s;
}

.latency-text {
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

.checked-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.loading-cell, .empty-cell {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.action-btn {
  background: none;
  border: 1px solid var(--border);
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  margin-right: 4px;
}

.action-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.action-danger:hover {
  border-color: var(--danger);
  color: var(--danger);
}
</style>
