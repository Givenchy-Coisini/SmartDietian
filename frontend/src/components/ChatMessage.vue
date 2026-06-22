<script setup lang="ts">
import { computed } from 'vue'
import { User, LoaderCircle } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'
import type { ChatMessage } from '@/api/chat'

const props = defineProps<{
  message: ChatMessage
  loading?: boolean
}>()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  return md.render(props.message.content)
})

const isUser = computed(() => props.message.role === 'user')
</script>

<template>
  <div
    class="flex gap-3"
    :class="isUser ? 'flex-row-reverse' : 'flex-row'"
  >
    <div
      class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm"
      :class="isUser
        ? 'bg-gradient-to-br from-primary-400 to-primary-600 shadow-primary-200/50'
        : 'bg-gradient-to-br from-accent-400 to-primary-500 shadow-accent-200/50'"
    >
      <User v-if="isUser" class="w-4 h-4 text-white" />
      <span v-else class="text-white text-xs font-bold">AI</span>
    </div>

    <div
      class="max-w-[80%] rounded-2xl px-4 py-3 shadow-sm"
      :class="isUser
        ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-primary-200/40'
        : 'bg-white/90 backdrop-blur-sm border border-gray-100 shadow-gray-100/50'"
    >
      <p v-if="isUser" class="whitespace-pre-wrap text-sm leading-relaxed">
        {{ message.content }}
      </p>

      <div v-else>
        <div v-if="loading && !message.content" class="flex items-center gap-2 text-gray-400">
          <LoaderCircle class="w-4 h-4 animate-spin" />
          <span class="text-sm">{{ $t('chat.sending') }}</span>
        </div>
        <div
          v-else
          class="markdown-body text-sm text-gray-700"
          v-html="renderedContent"
        />
      </div>

      <img
        v-if="message.image_url"
        :src="message.image_url"
        class="mt-2 max-w-full rounded-lg max-h-60 object-cover"
        alt="uploaded food"
      />
    </div>
  </div>
</template>
