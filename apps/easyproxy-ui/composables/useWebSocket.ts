export function useWebSocket() {
  const proxyStore = useProxyStore()
  const poolStore = usePoolStore()

  const isConnected = ref(false)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 10

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = 'localhost:8000'
    const url = `${protocol}//${host}/ws`

    try {
      ws = new WebSocket(url)
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleEvent(msg)
      } catch {
        // ignore malformed
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      ws = null
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function handleEvent(msg: { type: string; data?: any }) {
    switch (msg.type) {
      case 'proxy_started':
      case 'proxy_stopped':
        proxyStore.fetchStatus()
        break
      case 'rotation_completed':
        proxyStore.fetchStatus()
        break
      case 'rate_limit_detected':
        proxyStore.fetchStatus()
        break
      case 'pool_stats':
        if (msg.data) {
          poolStore.total = msg.data.total
          poolStore.alive = msg.data.alive
          poolStore.dead = msg.data.dead
        }
        break
      case 'proxy_test_result':
        poolStore.fetchProxies()
        break
      case 'pool_refreshed':
        poolStore.fetchProxies()
        break
    }
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) return
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
    reconnectAttempts++
    reconnectTimer = setTimeout(connect, delay)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    reconnectAttempts = maxReconnectAttempts
    ws?.close()
    ws = null
    isConnected.value = false
  }

  function send(data: Record<string, any>) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { isConnected, connect, disconnect, send }
}
