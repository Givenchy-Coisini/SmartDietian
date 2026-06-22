<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ChatEmpty from './ChatEmpty.vue'
import ChatInput from './ChatInput.vue'
import { streamChat } from '@/api/chat'
import { useImageUpload } from '@/composables/useImageUpload'
import type { ChatMessage as ChatMessageType } from '@/api/chat'

const props = defineProps<{
  messages: ChatMessageType[]
  threadId: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  sendMessage: []
  setLoading: [loading: boolean]
}>()

const {
  previewUrl,
  createPreview,
  upload,
  clear: clearImage,
} = useImageUpload()

const chatContainer = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(
  () => props.messages[props.messages.length - 1]?.content,
  scrollToBottom
)

function handleFileSelected(file: File) {
  createPreview(file)
}

async function handleSend(text: string, file: File | null) {
  if (props.isLoading) return

  let imageUrl: string | null = null
  if (file) {
    imageUrl = await upload(file)
  }

  const userMsg: ChatMessageType = { role: 'user', content: text }
  if (imageUrl) userMsg.image_url = imageUrl
  props.messages.push(userMsg)

  const aiMsg: ChatMessageType = { role: 'assistant', content: '' }
  props.messages.push(aiMsg)

  emit('setLoading', true)
  try {
    await streamChat(
      {
        message: text,
        image_url: imageUrl,
        thread_id: props.threadId,
      },
      (chunk) => {
        aiMsg.content += chunk
      }
    )
    emit('sendMessage')
  } catch {
    aiMsg.content += `\n\n⚠️ 流式响应中断`
  } finally {
    emit('setLoading', false)
  }
}

function scrollToBottomForce() {
  scrollToBottom()
}

defineExpose({ scrollToBottomForce })
</script>

<template>
  <div class="flex flex-col h-full">
    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto pt-4 pb-24 scroll-smooth"
    >
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
        <ChatEmpty />
      </div>
      <div v-else class="max-w-3xl mx-auto px-6 space-y-5">
        <ChatMessage
          v-for="(msg, i) in messages"
          :key="i"
          :message="msg"
          :loading="isLoading && i === messages.length - 1 && msg.role === 'assistant'"
        />
      </div>
    </div>

    <ChatInput
      :disabled="isLoading"
      :image-preview="previewUrl"
      @send="handleSend"
      @file-selected="handleFileSelected"
      @clear-image="clearImage"
    />
  </div>
</template>
