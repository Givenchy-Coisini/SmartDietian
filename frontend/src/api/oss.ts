import axios from 'axios'

import { request } from '@/utils/request'

interface PresignResponse {
  uploadUrl: string
  accessUrl: string
  contentType?: string
}

export async function getPresignUrl(filename: string): Promise<PresignResponse> {
  return await request<PresignResponse>({
    url: '/oss/presign',
    method: 'GET',
    params: { filename },
  })
}

export async function uploadToOss(uploadUrl: string, file: File): Promise<void> {
  await axios.put(uploadUrl, file, {
    headers: { 'Content-Type': file.type },
    transformRequest: [(data) => data],
  })
}
