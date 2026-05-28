<script setup lang="ts">
import { useAppStore } from '../stores/app'

const store = useAppStore()
</script>

<template>
  <n-date-picker
    :value="store.currentDate ? new Date(
      parseInt(store.currentDate.slice(0, 4)),
      parseInt(store.currentDate.slice(4, 6)) - 1,
      parseInt(store.currentDate.slice(6, 8)),
    ).getTime() : null"
    @update:value="(v: number | null) => {
      if (v) {
        const d = new Date(v)
        const y = d.getFullYear()
        const m = String(d.getMonth() + 1).padStart(2, '0')
        const day = String(d.getDate()).padStart(2, '0')
        store.setDate(`${y}${m}${day}`)
      }
    }"
    type="date"
    :is-date-disabled="(ts: number) => {
      const d = new Date(ts)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return !store.availableDates.includes(`${y}${m}${day}`)
    }"
    clearable
    class="w-40"
  />
</template>
