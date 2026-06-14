export const useProxyStore = defineStore('proxy', () => {
  const running = ref(false)
  const port = ref(8080)
  const currentIp = ref('')
  const currentProxyId = ref<number | null>(null)
  const currentProxy = ref('')
  const strategy = ref('round-robin')
  const uptimeSeconds = ref(0)
  const requestsServed = ref(0)
  const rateLimitsDetected = ref(0)
  const rotationsPerformed = ref(0)

  async function fetchStatus() {
    try {
      const data: any = await $fetch('/api/v1/proxy/status')
      running.value = data.running
      port.value = data.port
      currentIp.value = data.current_proxy ?? ''
      currentProxyId.value = data.current_proxy_id
      currentProxy.value = data.current_proxy ?? ''
      strategy.value = data.strategy
      uptimeSeconds.value = data.uptime_seconds
      requestsServed.value = data.requests_served
      rateLimitsDetected.value = data.rate_limits_detected
      rotationsPerformed.value = data.rotations_performed
    } catch {
      running.value = false
    }
  }

  async function startProxy() {
    await $fetch('/api/v1/proxy/start', { method: 'POST', body: { port: port.value } })
    await fetchStatus()
  }

  async function stopProxy() {
    await $fetch('/api/v1/proxy/stop', { method: 'POST' })
    await fetchStatus()
  }

  async function rotate() {
    const data: any = await $fetch('/api/v1/proxy/rotate', { method: 'POST' })
    currentIp.value = data.current_proxy ?? ''
    currentProxyId.value = data.current_proxy_id
    await fetchStatus()
  }

  return {
    running, port, currentIp, currentProxyId, currentProxy,
    strategy, uptimeSeconds, requestsServed, rateLimitsDetected, rotationsPerformed,
    fetchStatus, startProxy, stopProxy, rotate,
  }
})
