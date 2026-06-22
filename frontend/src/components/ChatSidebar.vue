<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { MessageSquarePlus, Trash2, MessageCircle } from 'lucide-vue-next'
import type { Thread } from '@/api/chat'

const { t } = useI18n()

defineProps<{
  threads: Thread[]
  activeThreadId: string
}>()

const emit = defineEmits<{
  selectThread: [id: string]
  newSession: []
  deleteThread: [id: string]
}>()

function handleDelete(e: Event, id: string) {
  e.stopPropagation()
  emit('deleteThread', id)
}
</script>

<template>
  <aside class="hidden md:flex flex-col w-72 h-full bg-white/60 backdrop-blur-xl border-r border-primary-100/50">
    <div class="p-4 border-b border-primary-100/50">
      <button
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-br from-primary-400 to-accent-500 text-white text-sm font-medium shadow-md shadow-primary-200/50 hover:shadow-lg hover:scale-[1.02] transition"
        @click="emit('newSession')"
      >
        <MessageSquarePlus class="w-4 h-4" />
        {{ t('header.newSession') }}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-3 py-3 space-y-1">
      <p class="px-2 pb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
        {{ t('sidebar.title') }}
      </p>

      <div v-if="threads.length === 0" class="px-2 py-8 text-center text-sm text-gray-400">
        {{ t('sidebar.empty') }}
      </div>

      <button
        v-for="t in threads"
        :key="t.thread_id"
        class="group w-full text-left flex items-start gap-2 px-3 py-2.5 rounded-lg transition relative"
        :class="t.thread_id === activeThreadId
          ? 'bg-primary-100/70 text-primary-700'
          : 'text-gray-600 hover:bg-primary-50/70'"
        @click="emit('selectThread', t.thread_id)"
      >
        <MessageCircle class="w-4 h-4 mt-0.5 shrink-0 opacity-70" />
        <span class="flex-1 text-sm truncate">{{ t.preview }}</span>
        <span
          class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition"
          @click="handleDelete($event, t.thread_id)"
        >
          <Trash2 class="w-4 h-4" />
        </span>
      </button>
    </div>
  </aside>
</template>
