<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { UtensilsCrossed } from 'lucide-vue-next'

const { t } = useI18n()
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full text-center px-4">
    <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-100 to-primary-200/60 flex items-center justify-center mb-6 shadow-lg shadow-primary-100/50">
      <UtensilsCrossed class="w-12 h-12 text-primary-400" />
    </div>
    <h2 class="text-xl font-semibold text-gray-700 mb-2">
      {{ t('chat.emptyTitle') }}
    </h2>
    <p class="text-gray-400 text-sm max-w-xs">
      {{ t('chat.emptySubtitle') }}
    </p>
  </div>
</template>
