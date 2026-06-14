<script setup lang="ts">
const poolStore = usePoolStore()

const searchQuery = ref('')
const filterProtocol = ref<'all' | 'http' | 'https' | 'socks5'>('all')
const filterStatus = ref<'all' | 'alive' | 'dead' | 'untested'>('all')

const filteredProxies = computed(() => {
  let list = poolStore.proxies
  if (filterProtocol.value !== 'all') {
    list = list.filter(p => p.protocol === filterProtocol.value)
  }
  if (filterStatus.value !== 'all') {
    list = list.filter(p => p.status === filterStatus.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(p => p.address.includes(q) || p.region?.toLowerCase().includes(q))
  }
  return list
})

onMounted(() => {
  poolStore.fetchProxies()
})
</script>

<template>
  <div class="proxy-manager">
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" @click="$router.push('/proxy/add')">Add</button>
        <button class="btn btn-secondary">Import</button>
        <button class="btn btn-secondary" @click="poolStore.testProxies()">Test All</button>
      </div>
      <div class="toolbar-right">
        <select v-model="filterProtocol" class="filter-select">
          <option value="all">All Protocols</option>
          <option value="http">HTTP</option>
          <option value="https">HTTPS</option>
          <option value="socks5">SOCKS5</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="all">All Status</option>
          <option value="alive">Alive</option>
          <option value="dead">Dead</option>
          <option value="untested">Untested</option>
        </select>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="search-input"
        >
      </div>
    </div>
    <div class="pool-stats">
      <span>Total: <strong>{{ poolStore.total }}</strong></span>
      <span class="stat-alive">Alive: <strong>{{ poolStore.alive }}</strong></span>
      <span class="stat-dead">Dead: <strong>{{ poolStore.dead }}</strong></span>
    </div>
    <table class="proxy-table">
      <thead>
        <tr>
          <th>Address</th>
          <th>Port</th>
          <th>Protocol</th>
          <th>Region</th>
          <th>Status</th>
          <th>Latency</th>
          <th>Requests</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in filteredProxies" :key="p.id">
          <td class="cell-mono">{{ p.address }}</td>
          <td>{{ p.port }}</td>
          <td>{{ p.protocol.toUpperCase() }}</td>
          <td>{{ p.region ?? '—' }}</td>
          <td>
            <span class="status-dot" :class="p.status" />
            {{ p.status }}
          </td>
          <td>{{ p.latency_ms ? `${p.latency_ms}ms` : '—' }}</td>
          <td>{{ p.success_count }}</td>
          <td>
            <button class="action-btn" title="Edit">✎</button>
            <button class="action-btn" title="Delete" @click="poolStore.removeProxy(p.id)">🗑</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.proxy-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-left,
.toolbar-right {
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

.filter-select,
.search-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.pool-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.pool-stats .stat-alive { color: var(--success); }
.pool-stats .stat-dead { color: var(--danger); }

.proxy-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.proxy-table th {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.proxy-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}

.cell-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.action-btn {
  background: none;
  border: none;
  padding: 4px 6px;
  font-size: 14px;
  opacity: 0.6;
}

.action-btn:hover {
  opacity: 1;
}
</style>
