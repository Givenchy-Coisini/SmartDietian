<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChefHat, Languages } from 'lucide-vue-next'
import { LOCALE_STORAGE_KEY, type AppLocale } from '@/locales'

const { t, locale } = useI18n()

defineEmits<{
  newSession: []
}>()

const isZh = computed(() => locale.value === 'zh-CN')
const toggleTitle = computed(() =>
  isZh.value ? t('header.switchToEnglish') : t('header.switchToChinese')
)
const toggleLabel = computed(() => (isZh.value ? 'EN' : '中'))

function toggleLocale() {
  const next: AppLocale = isZh.value ? 'en' : 'zh-CN'
  locale.value = next
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, next)
  } catch {
    // localStorage 不可用时忽略
  }
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-primary-100/50 shadow-sm">
    <div class="max-w-full mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center shadow-md shadow-primary-200/50">
          <ChefHat class="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 class="text-base font-bold text-gray-900 tracking-tight">{{ t('app.title') }}</h1>
          <p class="text-[11px] text-gray-400 leading-tight">{{ t('app.subtitle') }}</p>
        </div>
      </div>

      <button
        type="button"
        :title="toggleTitle"
        :aria-label="toggleTitle"
        class="inline-flex items-center gap-1.5 px-3 h-9 rounded-lg border border-primary-100 bg-white/80 hover:bg-primary-50 text-gray-700 hover:text-primary-600 text-sm font-medium transition-colors shadow-sm"
        @click="toggleLocale"
      >
        <Languages class="w-4 h-4" />
        <span>{{ toggleLabel }}</span>
      </button>
    </div>
  </header>
</template>
