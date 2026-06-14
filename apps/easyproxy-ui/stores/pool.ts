export interface Proxy {
  id: number
  address: string
  port: number
  protocol: 'http' | 'https' | 'socks5'
  username: string | null
  password: string | null
  region: string | null
  status: 'alive' | 'dead' | 'untested'
  latency_ms: number | null
  last_checked_at: string | null
  source: string
  residential_provider: string | null
  error_count: number
  success_count: number
}

export const usePoolStore = defineStore('pool', () => {
  const proxies = ref<Proxy[]>([])
  const total = ref(0)
  const alive = ref(0)
  const dead = ref(0)
  const loading = ref(false)

  async function fetchProxies(params?: Record<string, string>) {
    loading.value = true
    try {
      const query = new URLSearchParams(params)
      const data: any = await $fetch(`/api/v1/pool?${query}`)
      proxies.value = data.proxies ?? []
      total.value = data.total ?? 0
    } catch {
      proxies.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const data: any = await $fetch('/api/v1/pool/stats')
      total.value = data.total ?? 0
      alive.value = data.alive ?? 0
      dead.value = data.dead ?? 0
    } catch {
      // pool not yet implemented
    }
  }

  async function addProxy(body: Partial<Proxy>) {
    const data: any = await $fetch('/api/v1/pool', { method: 'POST', body })
    await fetchProxies()
    return data.proxy_id
  }

  async function updateProxy(id: number, body: Partial<Proxy>) {
    await $fetch(`/api/v1/pool/${id}`, { method: 'PUT', body })
    await fetchProxies()
  }

  async function removeProxy(id: number) {
    await $fetch(`/api/v1/pool/${id}`, { method: 'DELETE' })
    await fetchProxies()
  }

  async function importProxies(body: { format: string; content: string }) {
    return await $fetch('/api/v1/pool/import', { method: 'POST', body })
  }

  async function testProxies(body?: { proxy_ids?: number[] }) {
    return await $fetch('/api/v1/pool/test', { method: 'POST', body })
  }

  return {
    proxies, total, alive, dead, loading,
    fetchProxies, fetchStats, addProxy, updateProxy, removeProxy,
    importProxies, testProxies,
  }
})
