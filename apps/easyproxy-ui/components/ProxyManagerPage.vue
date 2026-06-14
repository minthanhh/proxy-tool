<script setup lang="ts">
import { ProxyTable, ProxyFormModal, ImportPreviewModal } from 'ui'
import type { ProxyRow } from 'ui'
import type { ProxyFormData } from 'ui'

const poolStore = usePoolStore()

const currentTab = ref('all')
const searchQuery = ref('')
const selectedIds = ref<number[]>([])
const sort = ref({ column: 'address', direction: 'asc' as 'asc' | 'desc' })
const page = ref(1)
const perPage = 50
const showFormModal = ref(false)
const showImportModal = ref(false)
const editingProxy = ref<ProxyFormData | null>(null)
const saving = ref(false)
const importing = ref(false)
const testing = ref(false)

const tabFilter = computed(() => {
  switch (currentTab.value) {
    case 'http': return { protocol: 'http' }
    case 'https': return { protocol: 'https' }
    case 'socks5': return { protocol: 'socks5' }
    case 'alive': return { status: 'alive' }
    case 'dead': return { status: 'dead' }
    default: return {}
  }
})

const filteredProxies = computed(() => {
  let list = poolStore.proxies
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(p => p.address.includes(q) || p.region?.toLowerCase().includes(q))
  }
  return list
})

const tabs = [
  { key: 'all', label: 'All' },
  { key: 'http', label: 'HTTP' },
  { key: 'https', label: 'HTTPS' },
  { key: 'socks5', label: 'SOCKS5' },
  { key: 'alive', label: 'Alive' },
  { key: 'dead', label: 'Dead' },
]

onMounted(() => fetchProxies())

watch([currentTab, page], () => fetchProxies())

async function fetchProxies() {
  const params: Record<string, string> = {
    page: String(page.value),
    per_page: String(perPage),
    ...tabFilter.value,
  }
  if (sort.value.column) {
    params.sort_by = sort.value.column
    params.sort_dir = sort.value.direction
  }
  await poolStore.fetchProxies(params)
}

function handleSort(column: string) {
  if (sort.value.column === column) {
    sort.value.direction = sort.value.direction === 'asc' ? 'desc' : 'asc'
  } else {
    sort.value = { column, direction: 'asc' }
  }
  fetchProxies()
}

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

function selectAll() {
  if (selectedIds.value.length === filteredProxies.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredProxies.value.map(p => p.id)
  }
}

function openAddModal() {
  editingProxy.value = null
  showFormModal.value = true
}

function openEditModal(proxy: ProxyRow) {
  editingProxy.value = {
    address: proxy.address,
    port: proxy.port,
    protocol: proxy.protocol,
    username: proxy.username ?? '',
    password: proxy.password ?? '',
    region: proxy.region ?? '',
  }
  showFormModal.value = true
}

async function handleSave(data: ProxyFormData) {
  saving.value = true
  try {
    const body = {
      address: data.address,
      port: data.port,
      protocol: data.protocol,
      username: data.username || null,
      password: data.password || null,
      region: data.region || null,
    }
    if (editingProxy.value) {
      const proxy = poolStore.proxies.find(p => p.address === data.address && p.port === data.port)
      if (proxy) await poolStore.updateProxy(proxy.id, body)
    } else {
      await poolStore.addProxy(body)
    }
    showFormModal.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  await poolStore.removeProxy(id)
  selectedIds.value = selectedIds.value.filter(sid => sid !== id)
}

async function handleImport(body: { format: string; content: string; protocol?: string; region?: string }) {
  importing.value = true
  try {
    await poolStore.importProxies(body)
    showImportModal.value = false
    await fetchProxies()
  } finally {
    importing.value = false
  }
}

async function handleTestAll() {
  testing.value = true
  try {
    const ids = selectedIds.value.length > 0 ? selectedIds.value : undefined
    await poolStore.testProxies(ids ? { proxy_ids: ids } : undefined)
    await fetchProxies()
  } finally {
    testing.value = false
  }
}

async function handleTestSelected() {
  if (selectedIds.value.length === 0) return
  testing.value = true
  try {
    await poolStore.testProxies({ proxy_ids: selectedIds.value })
    await fetchProxies()
  } finally {
    testing.value = false
  }
}

async function handleDeleteSelected() {
  for (const id of [...selectedIds.value]) {
    await poolStore.removeProxy(id)
  }
  selectedIds.value = []
}

const totalPages = computed(() => Math.max(1, Math.ceil(poolStore.total / perPage)))
</script>

<template>
  <div class="proxy-manager-page">
    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key; page = 1"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" @click="openAddModal">Add</button>
        <button class="btn btn-secondary" @click="showImportModal = true">Import</button>
        <button class="btn btn-secondary" :disabled="testing" @click="handleTestAll">
          <span v-if="testing" class="spinner" />
          <span v-else>Test All</span>
        </button>
        <button
          v-if="selectedIds.length > 0"
          class="btn btn-secondary"
          :disabled="testing"
          @click="handleTestSelected"
        >
          Test ({{ selectedIds.length }})
        </button>
        <button
          v-if="selectedIds.length > 0"
          class="btn btn-danger"
          @click="handleDeleteSelected"
        >
          Delete ({{ selectedIds.length }})
        </button>
      </div>
      <div class="toolbar-right">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search address or region…"
          class="search-input"
        >
      </div>
    </div>

    <!-- Stats -->
    <div class="pool-stats">
      <span>Total: <strong>{{ poolStore.total }}</strong></span>
      <span class="stat-alive">Alive: <strong>{{ poolStore.alive }}</strong></span>
      <span class="stat-dead">Dead: <strong>{{ poolStore.dead }}</strong></span>
    </div>

    <!-- Table -->
    <ProxyTable
      :proxies="filteredProxies"
      :sort="sort"
      :selected-ids="selectedIds"
      :loading="poolStore.loading"
      @sort="handleSort"
      @toggle-select="toggleSelect"
      @select-all="selectAll"
      @edit="openEditModal"
      @delete="handleDelete"
    />

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="page--">← Prev</button>
      <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++">Next →</button>
    </div>

    <!-- Modals -->
    <ProxyFormModal
      :open="showFormModal"
      :saving="saving"
      :proxy="editingProxy"
      @save="handleSave"
      @cancel="showFormModal = false"
    />

    <ImportPreviewModal
      :open="showImportModal"
      :importing="importing"
      @import="handleImport"
      @cancel="showImportModal = false"
    />
  </div>
</template>

<style scoped>
.proxy-manager-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: flex;
  gap: 2px;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 2px;
  width: fit-content;
}

.tab {
  padding: 6px 16px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}

.tab.active {
  background: var(--surface);
  color: var(--text-primary);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

.tab:hover:not(.active) {
  color: var(--text-primary);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left, .toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.btn-danger {
  background: var(--danger);
  color: #fff;
}

.search-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  width: 220px;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.pool-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.pool-stats .stat-alive { color: var(--success); }
.pool-stats .stat-dead { color: var(--danger); }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0;
}

.pagination button {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  border-color: var(--accent);
}

.page-info {
  font-size: 13px;
  color: var(--text-secondary);
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
