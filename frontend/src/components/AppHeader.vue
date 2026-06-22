<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ChefHat } from 'lucide-vue-next'

const { t } = useI18n()

defineEmits<{
  newSession: []
}>()
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-primary-100/50 shadow-sm">
    <div class="max-w-full mx-auto px-6 h-16 flex items-center">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center shadow-md shadow-primary-200/50">
          <ChefHat class="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 class="text-base font-bold text-gray-900 tracking-tight">{{ t('app.title') }}</h1>
          <p class="text-[11px] text-gray-400 leading-tight">{{ t('app.subtitle') }}</p>
        </div>
      </div>
    </div>
  </header>
</template>
