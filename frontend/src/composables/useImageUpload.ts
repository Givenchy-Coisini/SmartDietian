import { ref } from 'vue'
import { getPresignUrl, uploadToOss } from '@/api/oss'

export function useImageUpload() {
  const isUploading = ref(false)
  const previewUrl = ref<string | null>(null)
  const uploadedUrl = ref<string | null>(null)

  function createPreview(file: File) {
    clear()
    previewUrl.value = URL.createObjectURL(file)
  }

  async function upload(file: File): Promise<string | null> {
    isUploading.value = true

    try {
      const { uploadUrl, accessUrl } = await getPresignUrl(file.name)
      await uploadToOss(uploadUrl, file)
      uploadedUrl.value = accessUrl
      return accessUrl
    } catch {
      uploadedUrl.value = null
      return null
    } finally {
      isUploading.value = false
    }
  }

  function clear() {
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
    uploadedUrl.value = null
  }

  return { isUploading, previewUrl, uploadedUrl, createPreview, upload, clear }
}
