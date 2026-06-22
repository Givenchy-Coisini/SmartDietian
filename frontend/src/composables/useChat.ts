import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { streamChat, getMessages, deleteMessages, getThreads } from '@/api/chat'
import type { ChatMessage, Thread } from '@/api/chat'

export function useChat() {
  const messages = ref<ChatMessage[]>([])
  const threadId = ref('')
  const threads = ref<Thread[]>([])
  const isLoading = ref(false)
  let abortController: AbortController | null = null

  function initThread() {
    const stored = localStorage.getItem('thread_id')
    threadId.value = stored || uuidv4()
    if (!stored) localStorage.setItem('thread_id', threadId.value)
  }

  async function loadHistory() {
    try {
      const history = await getMessages(threadId.value)
      messages.value = history
    } catch {
      // ignore on first load
    }
  }

  async function loadThreads() {
    try {
      threads.value = await getThreads()
    } catch {
      // ignore
    }
  }

  async function switchThread(id: string) {
    stopStreaming()
    threadId.value = id
    localStorage.setItem('thread_id', id)
    await loadHistory()
  }

  async function sendMessage(text: string, imageUrl?: string | null) {
    if (isLoading.value) return

    const userMsg: ChatMessage = { role: 'user', content: text }
    if (imageUrl) userMsg.image_url = imageUrl
    messages.value.push(userMsg)

    const aiMsg: ChatMessage = { role: 'assistant', content: '' }
    messages.value.push(aiMsg)

    isLoading.value = true
    abortController = new AbortController()

    try {
      await streamChat(
        {
          message: text,
          image_url: imageUrl || null,
          thread_id: threadId.value,
        },
        (chunk) => {
          aiMsg.content += chunk
        },
        abortController.signal
      )
      loadThreads()
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        aiMsg.content += `\n\n⚠️ 流式响应中断`
      }
    } finally {
      isLoading.value = false
      abortController = null
    }
  }

  function stopStreaming() {
    abortController?.abort()
  }

  async function newSession() {
    stopStreaming()
    threadId.value = uuidv4()
    localStorage.setItem('thread_id', threadId.value)
    messages.value = []
    loadThreads()
  }

  async function deleteThread(id: string) {
    try {
      await deleteMessages(id)
    } catch {
      // ignore
    }
    if (id === threadId.value) {
      threadId.value = uuidv4()
      localStorage.setItem('thread_id', threadId.value)
      messages.value = []
    }
    loadThreads()
  }

  return {
    messages,
    threadId,
    threads,
    isLoading,
    initThread,
    loadHistory,
    loadThreads,
    switchThread,
    sendMessage,
    stopStreaming,
    newSession,
    deleteThread,
  }
}
