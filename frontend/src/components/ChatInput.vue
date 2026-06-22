<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Image, Send, X } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps<{
  disabled?: boolean
  imagePreview?: string | null
}>()

const emit = defineEmits<{
  send: [text: string, file: File | null]
  fileSelected: [file: File]
  clearImage: []
}>()

const text = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

const canSend = computed(() => {
  return (text.value.trim() || selectedFile.value) && !props.disabled
})

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) {
    selectedFile.value = input.files[0]
    emit('fileSelected', input.files[0])
  }
}

function handleClearImage() {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  emit('clearImage')
}

function handleSend() {
  if (!canSend.value) return
  emit('send', text.value.trim(), selectedFile.value)
  text.value = ''
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  emit('clearImage')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="fixed bottom-0 right-0 left-72 z-50">
    <div class="max-w-3xl mx-auto px-6 pb-5">
      <div class="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/60 shadow-lg shadow-gray-200/40 p-3">
        <div v-if="imagePreview" class="mb-2 relative inline-block">
          <img
            :src="imagePreview"
            class="h-20 rounded-xl object-cover border border-primary-200 shadow-sm"
            alt="preview"
          />
          <button
            class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center shadow-md hover:bg-red-600 transition-colors"
            @click="handleClearImage"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <div class="flex items-end gap-2">
          <button
            class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-gray-400 hover:text-primary-500 hover:bg-primary-50 transition-all"
            @click="fileInputRef?.click()"
          >
            <Image class="w-5 h-5" />
          </button>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFileChange"
          />

          <textarea
            v-model="text"
            :placeholder="t('chat.placeholder')"
            :disabled="disabled"
            rows="1"
            class="flex-1 resize-none rounded-xl border-0 bg-transparent px-2 py-2.5 text-sm focus:outline-none disabled:opacity-50 max-h-32 placeholder:text-gray-400"
            @keydown="handleKeydown"
          />

          <button
            :disabled="!canSend"
            class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-white transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
            :class="canSend
              ? 'bg-gradient-to-r from-primary-500 to-accent-500 shadow-md shadow-primary-200/50 hover:shadow-lg'
              : 'bg-gray-200'"
            @click="handleSend"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
