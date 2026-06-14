<script setup lang="ts">
export interface LogFilters {
  since: string
  until: string
  methods: string[]
  statusMin: string
  statusMax: string
  urlSearch: string
  proxyIp: string
  rateLimitedOnly: boolean
}

const props = defineProps<{
  filters: LogFilters
  proxyOptions: string[]
}>()

const emit = defineEmits<{
  'update:filters': [filters: LogFilters]
  apply: []
  reset: []
}>()

const allMethods = ['GET', 'POST', 'PUT', 'DELETE', 'CONNECT', 'PATCH', 'HEAD', 'OPTIONS']

const statusRanges = [
  { label: '2xx (Success)', min: '200', max: '299' },
  { label: '3xx (Redirect)', min: '300', max: '399' },
  { label: '4xx (Client Error)', min: '400', max: '499' },
  { label: '5xx (Server Error)', min: '500', max: '599' },
]

const expanded = ref(false)

const activeFilterCount = computed(() => {
  let count = 0
  if (props.filters.since) count++
  if (props.filters.until) count++
  if (props.filters.methods.length > 0) count++
  if (props.filters.statusMin || props.filters.statusMax) count++
  if (props.filters.urlSearch) count++
  if (props.filters.proxyIp) count++
  if (props.filters.rateLimitedOnly) count++
  return count
})

function toggleMethod(method: string) {
  const methods = [...props.filters.methods]
  const idx = methods.indexOf(method)
  if (idx === -1) methods.push(method)
  else methods.splice(idx, 1)
  emit('update:filters', { ...props.filters, methods })
}

function setStatusRange(min: string, max: string) {
  if (props.filters.statusMin === min && props.filters.statusMax === max) {
    emit('update:filters', { ...props.filters, statusMin: '', statusMax: '' })
  } else {
    emit('update:filters', { ...props.filters, statusMin: min, statusMax: max })
  }
}
</script>

<template>
  <div class="log-filter-bar">
    <div class="filter-top-row">
      <div class="filter-badges" v-if="activeFilterCount > 0">
        <span class="badge-count">{{ activeFilterCount }} active</span>
        <button class="reset-link" @click="emit('reset')">Clear all</button>
      </div>
      <button class="toggle-btn" @click="expanded = !expanded">
        {{ expanded ? 'Hide filters' : 'Show filters' }}
        <span class="toggle-arrow" :class="{ open: expanded }">▾</span>
      </button>
    </div>

    <Transition name="fade">
      <div v-if="expanded" class="filter-body">
        <div class="filter-section">
          <span class="filter-section-label">Date Range</span>
          <div class="filter-row">
            <label class="filter-field">
              From
              <input v-model="filters.since" type="datetime-local" class="filter-input" @change="emit('apply')">
            </label>
            <label class="filter-field">
              To
              <input v-model="filters.until" type="datetime-local" class="filter-input" @change="emit('apply')">
            </label>
          </div>
        </div>

        <div class="filter-section">
          <span class="filter-section-label">HTTP Method</span>
          <div class="filter-chips">
            <button
              v-for="m in allMethods"
              :key="m"
              class="chip"
              :class="{ active: filters.methods.includes(m) }"
              @click="toggleMethod(m)"
            >
              {{ m }}
            </button>
          </div>
        </div>

        <div class="filter-section">
          <span class="filter-section-label">Status Code</span>
          <div class="filter-chips">
            <button
              v-for="r in statusRanges"
              :key="r.label"
              class="chip"
              :class="{ active: filters.statusMin === r.min }"
              @click="setStatusRange(r.min, r.max)"
            >
              {{ r.label }}
            </button>
          </div>
        </div>

        <div class="filter-section">
          <span class="filter-section-label">URL</span>
          <input v-model="filters.urlSearch" type="text" placeholder="Search URL..." class="filter-input filter-input-wide" @input="emit('apply')">
        </div>

        <div class="filter-section">
          <span class="filter-section-label">Proxy IP</span>
          <select v-model="filters.proxyIp" class="filter-input" @change="emit('apply')">
            <option value="">All proxies</option>
            <option v-for="ip in proxyOptions" :key="ip" :value="ip">{{ ip }}</option>
          </select>
        </div>

        <div class="filter-section">
          <label class="filter-checkbox">
            <input v-model="filters.rateLimitedOnly" type="checkbox" @change="emit('apply')">
            Rate limited only
          </label>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.log-filter-bar {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
}

.filter-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.badge-count {
  color: var(--text-secondary);
}

.reset-link {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.reset-link:hover {
  text-decoration: underline;
}

.toggle-btn {
  background: none;
  border: none;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-arrow {
  font-size: 10px;
  transition: transform 0.15s;
  display: inline-block;
}

.toggle-arrow.open {
  transform: rotate(180deg);
}

.filter-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid var(--border);
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.filter-row {
  display: flex;
  gap: 8px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: var(--text-secondary);
}

.filter-input {
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 12px;
  font-family: inherit;
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent);
}

.filter-input-wide {
  width: 100%;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip {
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: transparent;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.1s;
}

.chip.active {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}

.chip:hover:not(.active) {
  border-color: var(--accent);
  color: var(--accent);
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.filter-checkbox input {
  accent-color: var(--accent);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
