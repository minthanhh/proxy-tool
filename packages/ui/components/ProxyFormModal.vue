<script setup lang="ts">
export interface ProxyFormData {
  address: string
  port: number | ''
  protocol: 'http' | 'https' | 'socks5'
  username: string
  password: string
  region: string
}

const props = defineProps<{
  open: boolean
  saving: boolean
  proxy: ProxyFormData | null
}>()

const emit = defineEmits<{
  save: [data: ProxyFormData]
  cancel: []
}>()

const form = ref<ProxyFormData>({
  address: '',
  port: '',
  protocol: 'http',
  username: '',
  password: '',
  region: '',
})

const errors = ref<Record<string, string>>({})

watch(() => props.open, (opening) => {
  if (opening) {
    if (props.proxy) {
      form.value = { ...props.proxy }
    } else {
      form.value = { address: '', port: '', protocol: 'http', username: '', password: '', region: '' }
    }
    errors.value = {}
  }
})

const ipv4Re = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/

function validate(): boolean {
  const e: Record<string, string> = {}
  if (!form.value.address.trim()) {
    e.address = 'Address is required'
  } else if (!ipv4Re.test(form.value.address.trim())) {
    e.address = 'Invalid IPv4 address'
  } else {
    const parts = form.value.address.trim().split('.').map(Number)
    if (parts.some(p => p < 0 || p > 255)) {
      e.address = 'Invalid IPv4 address'
    }
  }
  if (form.value.port === '' || form.value.port === 0) {
    e.port = 'Port is required'
  } else if (typeof form.value.port === 'number' && (form.value.port < 1 || form.value.port > 65535)) {
    e.port = 'Port must be 1–65535'
  }
  errors.value = e
  return Object.keys(e).length === 0
}

function handleSave() {
  if (!validate()) return
  emit('save', { ...form.value, address: form.value.address.trim() })
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('cancel')
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSave()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-overlay" @click.self="emit('cancel')">
        <div class="modal-content" role="dialog" aria-label="Proxy form">
          <div class="modal-header">
            <h3>{{ proxy ? 'Edit Proxy' : 'Add Proxy' }}</h3>
            <button class="close-btn" @click="emit('cancel')">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-row">
              <label class="form-label">
                Address <span class="required">*</span>
                <input
                  v-model="form.address"
                  type="text"
                  placeholder="192.168.1.1"
                  class="form-input mono"
                  :class="{ invalid: errors.address }"
                >
                <span v-if="errors.address" class="form-error">{{ errors.address }}</span>
              </label>
              <label class="form-label form-label-narrow">
                Port <span class="required">*</span>
                <input
                  v-model.number="form.port"
                  type="number"
                  min="1"
                  max="65535"
                  placeholder="3128"
                  class="form-input"
                  :class="{ invalid: errors.port }"
                >
                <span v-if="errors.port" class="form-error">{{ errors.port }}</span>
              </label>
            </div>

            <label class="form-label">
              Protocol
              <select v-model="form.protocol" class="form-select">
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
                <option value="socks5">SOCKS5</option>
              </select>
            </label>

            <div class="form-row">
              <label class="form-label">
                Username
                <input v-model="form.username" type="text" placeholder="(optional)" class="form-input">
              </label>
              <label class="form-label">
                Password
                <input v-model="form.password" type="password" placeholder="(optional)" class="form-input">
              </label>
            </div>

            <label class="form-label">
              Region
              <input v-model="form.region" type="text" placeholder="US (ISO 3166-1 alpha-2)" class="form-input" maxlength="2">
            </label>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="emit('cancel')">Cancel</button>
            <button class="btn btn-primary" :disabled="saving" @click="handleSave">
              <span v-if="saving" class="spinner" />
              <span v-else>{{ proxy ? 'Save' : 'Add' }}</span>
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

.modal-content {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 480px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
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

.form-label-narrow {
  max-width: 120px;
}

.required {
  color: var(--danger);
}

.form-input, .form-select {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
}

.form-input.mono {
  font-family: 'JetBrains Mono', monospace;
}

.form-input.invalid, .form-select.invalid {
  border-color: var(--danger);
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-error {
  font-size: 11px;
  color: var(--danger);
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
