export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Record<string, any>>({
    general: { auto_start: false, minimize_to_tray: true, theme: 'system' },
    proxy: { port: 8080, auto_configure_system_proxy: true, bind_address: '127.0.0.1' },
    rotation: { strategy: 'round-robin', schedule_enabled: false, schedule_interval_minutes: 10, auto_rotate_on_429: true, retry_attempts: 3 },
    sticky_session: { enabled: true, ttl_seconds: 300, reset_on_error: true },
    logs: { max_entries: 10000, log_level: 'info' },
    health_check: { interval_seconds: 60, test_url: 'http://httpbin.org/ip', timeout_seconds: 10 },
  })

  const loading = ref(false)

  async function fetchSettings() {
    loading.value = true
    try {
      const data: any = await $fetch('/api/v1/settings')
      if (data) settings.value = data
    } catch {
      // use defaults
    } finally {
      loading.value = false
    }
  }

  async function updateSettings(patch: Record<string, any>) {
    loading.value = true
    try {
      await $fetch('/api/v1/settings', { method: 'PUT', body: patch })
      await fetchSettings()
    } finally {
      loading.value = false
    }
  }

  return { settings, loading, fetchSettings, updateSettings }
})
