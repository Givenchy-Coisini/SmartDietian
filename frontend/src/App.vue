<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppChat from '@/components/AppChat.vue'
import ChatSidebar from '@/components/ChatSidebar.vue'
import { useChat } from '@/composables/useChat'

const {
  messages,
  threads,
  threadId,
  isLoading,
  initThread,
  loadHistory,
  loadThreads,
  switchThread,
  newSession,
  deleteThread
} = useChat()

const chatRef = ref<InstanceType<typeof AppChat> | null>(null)

function handleSendMessage() {
  loadThreads()
}

function handleSetLoading(loading: boolean) {
  isLoading.value = loading
}

async function handleNewSession() {
  await newSession()
  chatRef.value?.scrollToBottomForce()
}

async function handleSelectThread(id: string) {
  await switchThread(id)
  chatRef.value?.scrollToBottomForce()
}

async function handleDeleteThread(id: string) {
  await deleteThread(id)
  chatRef.value?.scrollToBottomForce()
}

onMounted(async () => {
  initThread()
  await loadHistory()
  await loadThreads()
})
</script>

<template>
  <div class="relative h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 font-sans overflow-hidden">
    <div class="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob" />
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000" />
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-primary-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000" />
    </div>

    <AppHeader @new-session="handleNewSession" />

    <div class="flex h-screen pt-16">
      <ChatSidebar
        :threads="threads"
        :active-thread-id="threadId"
        @select-thread="handleSelectThread"
        @new-session="handleNewSession"
        @delete-thread="handleDeleteThread"
      />

      <main class="flex-1 min-w-0">
        <AppChat
          ref="chatRef"
          :messages="messages"
          :thread-id="threadId"
          :is-loading="isLoading"
          @send-message="handleSendMessage"
          @set-loading="handleSetLoading"
        />
      </main>
    </div>
  </div>
</template>
