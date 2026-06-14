<script setup lang="ts">
interface PreviewEntry {
  index: number
  address: string
  port: number
  protocol: string
  region: string
}

const props = defineProps<{
  open: boolean
  importing: boolean
}>()

const emit = defineEmits<{
  import: [body: { format: string; content: string; protocol?: string; region?: string }]
  cancel: []
}>()

const rawContent = ref('')
const format = ref<'txt' | 'csv'>('txt')
const defaultProtocol = ref('http')
const defaultRegion = ref('')
const parseError = ref('')
const previewData = ref<PreviewEntry[]>([])

watch(() => props.open, (opening) => {
  if (opening) {
    rawContent.value = ''
    defaultProtocol.value = 'http'
    defaultRegion.value = ''
    parseError.value = ''
    previewData.value = []
  }
})

function parseContent() {
  parseError.value = ''
  previewData.value = []

  if (!rawContent.value.trim()) {
    parseError.value = 'No content to import'
    return
  }

  if (format.value === 'txt') {
    const lines = rawContent.value.trim().split('\n').map(l => l.trim()).filter(Boolean)
    const entries: PreviewEntry[] = []
    for (let i = 0; i < lines.length; i++) {
      const parts = lines[i].split(':')
      if (parts.length < 2) {
        parseError.value = `Line ${i + 1}: invalid format (expected address:port)`
        continue
      }
      const addr = parts[0]
      const p = parseInt(parts[1], 10)
      if (!addr || isNaN(p) || p < 1 || p > 65535) {
        parseError.value = `Line ${i + 1}: invalid address or port`
        continue
      }
      entries.push({ index: i + 1, address: addr, port: p, protocol: defaultProtocol.value, region: defaultRegion.value })
    }
    previewData.value = entries
  } else {
    const lines = rawContent.value.trim().split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length < 2) {
      parseError.value = 'CSV must have a header row and at least one data row'
      return
    }
    const headers = lines[0].toLowerCase().split(',').map(h => h.trim())
    const ipIdx = headers.indexOf('ip')
    const portIdx = headers.indexOf('port')
    if (ipIdx === -1 || portIdx === -1) {
      parseError.value = 'CSV must have "ip" and "port" columns'
      return
    }
    const protoIdx = headers.indexOf('protocol')
    const regionIdx = headers.indexOf('region')

    const entries: PreviewEntry[] = []
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(',').map(c => c.trim())
      const address = cols[ipIdx]
      const p = parseInt(cols[portIdx], 10)
      if (!address || isNaN(p) || p < 1 || p > 65535) {
        parseError.value = `Line ${i + 1}: invalid address or port`
        continue
      }
      const protocol = protoIdx !== -1 && cols[protoIdx] ? cols[protoIdx] : defaultProtocol.value
      const region = regionIdx !== -1 && cols[regionIdx] ? cols[regionIdx] : defaultRegion.value
      entries.push({ index: i + 1, address, port: p, protocol, region })
    }
    previewData.value = entries
  }
}

function handleImport() {
  emit('import', {
    format: format.value,
    content: rawContent.value.trim(),
    protocol: defaultProtocol.value || undefined,
    region: defaultRegion.value || undefined,
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-overlay" @click.self="emit('cancel')">
        <div class="modal-content wide" role="dialog" aria-label="Import proxies">
          <div class="modal-header">
            <h3>Import Proxies</h3>
            <button class="close-btn" @click="emit('cancel')">✕</button>
          </div>

          <div class="modal-body">
            <div class="import-options">
              <label class="radio-label">
                <input v-model="format" type="radio" value="txt">
                TXT (address:port per line)
              </label>
              <label class="radio-label">
                <input v-model="format" type="radio" value="csv">
                CSV (ip,port,protocol,region)
              </label>
            </div>

            <div class="form-row">
              <label class="form-label">
                Default Protocol
                <select v-model="defaultProtocol" class="form-select">
                  <option value="http">HTTP</option>
                  <option value="https">HTTPS</option>
                  <option value="socks5">SOCKS5</option>
                </select>
              </label>
              <label class="form-label">
                Default Region
                <input v-model="defaultRegion" type="text" placeholder="(optional)" class="form-input" maxlength="2">
              </label>
            </div>

            <label class="form-label">
              Paste proxy list
              <textarea
                v-model="rawContent"
                class="form-textarea"
                :placeholder="format === 'txt' ? '45.67.89.10:3128\n98.76.54.32:8080' : 'ip,port,protocol,region\n45.67.89.10,3128,http,US'"
                rows="6"
              />
            </label>

            <button class="btn btn-secondary" @click="parseContent" :disabled="!rawContent.trim()">
              Preview
            </button>

            <div v-if="parseError" class="parse-error">{{ parseError }}</div>

            <div v-if="previewData.length > 0" class="preview-section">
              <div class="preview-header">
                <span class="preview-title">{{ previewData.length }} proxies parsed</span>
              </div>
              <div class="preview-table-wrapper">
                <table class="preview-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Address</th>
                      <th>Port</th>
                      <th>Protocol</th>
                      <th>Region</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="entry in previewData.slice(0, 20)" :key="entry.index">
                      <td>{{ entry.index }}</td>
                      <td><code>{{ entry.address }}</code></td>
                      <td>{{ entry.port }}</td>
                      <td>{{ entry.protocol.toUpperCase() }}</td>
                      <td>{{ entry.region || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="previewData.length > 20" class="preview-more">
                  … and {{ previewData.length - 20 }} more
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
            <button
              class="btn btn-primary"
              :disabled="importing || previewData.length === 0"
              @click="handleImport"
            >
              <span v-if="importing" class="spinner" />
              <span v-else>Import {{ previewData.length }} proxies</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content.wide {
  width: 640px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 15px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--text-secondary);
  padding: 4px;
  cursor: pointer;
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  flex: 1;
}

.form-input, .form-select {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-textarea {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  resize: vertical;
  min-height: 80px;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.import-options {
  display: flex;
  gap: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
}

.radio-label input {
  accent-color: var(--accent);
}

.parse-error {
  font-size: 12px;
  color: var(--danger);
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.preview-section {
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.preview-header {
  margin-bottom: 8px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.preview-table-wrapper {
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.preview-table th {
  text-align: left;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
}

.preview-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
}

.preview-table code {
  font-family: 'JetBrains Mono', monospace;
}

.preview-more {
  font-size: 11px;
  color: var(--text-secondary);
  padding: 8px;
  text-align: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
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

.btn-primary {
  background: var(--accent);
  color: #fff;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
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

.modal-enter-active, .modal-leave-active {
  transition: opacity 0.15s;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>
