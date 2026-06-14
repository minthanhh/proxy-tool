<script setup lang="ts">
const props = defineProps<{
  requests: number
  rateLimits: number
  rotations: number
  activeProxies: number
}>()

const emit = defineEmits<{
  navigate: [filter: string]
}>()

const stats = computed(() => [
  { label: 'Requests Today', value: props.requests, color: 'var(--accent)', icon: 'req', filter: 'requests' },
  { label: 'Rate Limits', value: props.rateLimits, color: 'var(--warning)', icon: 'limit', filter: 'rate-limited' },
  { label: 'Rotations', value: props.rotations, color: 'var(--success)', icon: 'rot', filter: 'rotations' },
  { label: 'Active Proxies', value: props.activeProxies, color: 'var(--success)', icon: 'proxy', filter: 'proxies' },
])

function animateValue(el: HTMLElement, from: number, to: number) {
  const duration = 400
  const start = performance.now()
  function frame(now: number) {
    const t = Math.min((now - start) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    el.textContent = Math.round(from + (to - from) * eased).toString()
    if (t < 1) requestAnimationFrame(frame)
  }
  requestAnimationFrame(frame)
}

const cardRefs = ref<(HTMLElement | null)[]>([])

watch(
  () => [props.requests, props.rateLimits, props.rotations, props.activeProxies],
  ([r, rl, rot, ap], [pr, prl, prot, pap]) => {
    const values = [r, rl, rot, ap]
    const prev = [pr ?? 0, prl ?? 0, prot ?? 0, pap ?? 0]
    cardRefs.value.forEach((el, i) => {
      const valEl = el?.querySelector('.stat-value') as HTMLElement
      if (valEl) animateValue(valEl, prev[i], values[i])
    })
  },
)
</script>

<template>
  <div class="stats-grid">
    <button
      v-for="(s, i) in stats"
      :key="s.label"
      ref="cardRefs"
      class="stat-card"
      :title="`View ${s.label}`"
      @click="emit('navigate', s.filter)"
    >
      <span class="stat-value" :style="{ color: s.color }">{{ s.value }}</span>
      <span class="stat-label">{{ s.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.stat-card:hover {
  border-color: var(--accent);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
