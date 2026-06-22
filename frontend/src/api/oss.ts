interface PresignResponse {
  uploadUrl: string
  accessUrl: string
}

const API_BASE = '/api/v1'

export async function getPresignUrl(filename: string): Promise<PresignResponse> {
  const res = await fetch(`${API_BASE}/oss/presign?filename=${encodeURIComponent(filename)}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function uploadToOss(uploadUrl: string, file: File): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': file.type },
  })
  if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`)
}
