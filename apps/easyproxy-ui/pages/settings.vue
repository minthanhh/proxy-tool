<script setup lang="ts">
const settingsStore = useSettingsStore()

const sections = [
  {
    title: 'General',
    fields: [
      { key: 'general.auto_start', label: 'Auto-start with system', type: 'toggle' },
      { key: 'general.minimize_to_tray', label: 'Minimize to tray on close', type: 'toggle' },
      { key: 'general.theme', label: 'Theme', type: 'select', options: ['system', 'light', 'dark'] },
    ],
  },
  {
    title: 'Rotation',
    fields: [
      { key: 'rotation.strategy', label: 'Strategy', type: 'select', options: ['round-robin', 'random', 'low-latency-first'] },
      { key: 'rotation.auto_rotate_on_429', label: 'Auto-rotate on 429', type: 'toggle' },
      { key: 'rotation.retry_attempts', label: 'Max retry attempts', type: 'number' },
    ],
  },
  {
    title: 'Sticky Session',
    fields: [
      { key: 'sticky_session.enabled', label: 'Enable sticky session', type: 'toggle' },
      { key: 'sticky_session.ttl_seconds', label: 'TTL (seconds)', type: 'number' },
      { key: 'sticky_session.reset_on_error', label: 'Reset on error', type: 'toggle' },
    ],
  },
]

onMounted(() => {
  settingsStore.fetchSettings()
})

function getValue(key: string): any {
  const parts = key.split('.')
  let obj: any = settingsStore.settings
  for (const p of parts) {
    if (obj && typeof obj === 'object' && p in obj) {
      obj = obj[p]
    } else {
      return undefined
    }
  }
  return obj
}

async function handleChange(key: string, value: any) {
  const parts = key.split('.')
  const payload = parts.reduceRight((acc, k, i) => {
    return i === parts.length - 1 ? { [k]: value } : { [k]: acc }
  }, {})
  await settingsStore.updateSettings(payload)
}
</script>

<template>
  <div class="settings-page">
    <h2 class="page-title">Settings</h2>
    <div v-for="section in sections" :key="section.title" class="settings-section">
      <h3 class="section-title">{{ section.title }}</h3>
      <div class="section-body">
        <div v-for="field in section.fields" :key="field.key" class="settings-row">
          <span class="row-label">{{ field.label }}</span>
          <div class="row-control">
            <input
              v-if="field.type === 'toggle'"
              type="checkbox"
              :checked="getValue(field.key)"
              @change="handleChange(field.key, ($event.target as HTMLInputElement).checked)"
            >
            <select
              v-else-if="field.type === 'select'"
              :value="getValue(field.key)"
              class="form-select"
              @change="handleChange(field.key, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
            </select>
            <input
              v-else-if="field.type === 'number'"
              type="number"
              :value="getValue(field.key)"
              class="form-input"
              @change="handleChange(field.key, parseInt(($event.target as HTMLInputElement).value))"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 600px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 16px 20px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-body {
  padding: 12px 20px 16px;
}

.settings-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.settings-row:last-child {
  border-bottom: none;
}

.row-label {
  font-size: 14px;
}

.form-select,
.form-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}
</style>
