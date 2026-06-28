import { request } from '@/utils/request'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  image_url?: string
}

export interface ChatRequest {
  message: string
  image_url?: string | null
  thread_id: string
}

export interface Thread {
  thread_id: string
  preview: string
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export async function streamChat(
  req: ChatRequest,
  onChunk: (text: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal
  })

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value, { stream: true }))
  }
}

export async function getMessages(threadId: string): Promise<ChatMessage[]> {
  const data = await request<{ messages?: ChatMessage[] }>({
    url: '/chat/messages',
    method: 'GET',
    params: { thread_id: threadId }
  })
  return data.messages ?? []
}

export async function deleteMessages(threadId: string): Promise<void> {
  await request<void>({
    url: '/chat/messages',
    method: 'DELETE',
    params: { thread_id: threadId }
  })
}

export async function getThreads(): Promise<Thread[]> {
  const data = await request<{ threads?: Thread[] }>({
    url: '/chat/threads',
    method: 'GET'
  })
  return data.threads ?? []
}
