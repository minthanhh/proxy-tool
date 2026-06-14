<script setup lang="ts">
const config = ref({
  provider: '',
  apiKey: '',
  zone: '',
  country: 'auto',
  poolSize: 50,
  connected: false,
})

const { data: remoteConfig } = await useFetch('/api/v1/residential/config')
if (remoteConfig.value) {
  config.value = { ...config.value, ...remoteConfig.value as any }
}

async function saveConfig() {
  await $fetch('/api/v1/residential/config', {
    method: 'PUT',
    body: config.value,
  })
}

async function refreshPool() {
  await $fetch('/api/v1/residential/refresh', { method: 'POST' })
}
</script>

<template>
  <div class="residential-page">
    <h2 class="page-title">Residential Proxy Configuration</h2>
    <div class="config-card">
      <div class="form-group">
        <label>Provider</label>
        <select v-model="config.provider" class="form-input">
          <option value="">Select provider...</option>
          <option value="brightdata">BrightData</option>
          <option value="oxylabs">Oxylabs</option>
          <option value="smartproxy">Smartproxy</option>
        </select>
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input v-model="config.apiKey" type="password" class="form-input" placeholder="Enter API key">
      </div>
      <div class="form-group">
        <label>Country</label>
        <select v-model="config.country" class="form-input">
          <option value="auto">Auto</option>
          <option value="us">United States</option>
          <option value="gb">United Kingdom</option>
          <option value="de">Germany</option>
          <option value="jp">Japan</option>
        </select>
      </div>
      <button class="btn btn-primary" @click="saveConfig">Save Configuration</button>
    </div>
    <div class="connection-status">
      <div class="status-header">
        <span class="status-dot" :class="config.connected ? 'running' : 'stopped'" />
        <span>{{ config.connected ? 'Connected' : 'Disconnected' }}</span>
      </div>
      <div class="status-details">
        <div>Pool: {{ config.poolSize }} IPs configured</div>
      </div>
      <button class="btn btn-secondary" :disabled="!config.connected" @click="refreshPool">
        Refresh Now
      </button>
    </div>
  </div>
</template>

<style scoped>
.residential-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 600px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.config-card,
.connection-status {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-input {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.btn {
  padding: 8px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  font-size: 13px;
  align-self: flex-start;
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.status-details {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
