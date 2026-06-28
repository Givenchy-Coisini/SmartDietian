import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse
} from 'axios'

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api/v1',
  timeout: 30_000
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const message =
        (data && (data.detail || data.message)) || `请求失败 (HTTP ${status})`
      console.error(`[request] ${status}:`, message)
      return Promise.reject(new Error(message))
    }
    if (error.code === 'ECONNABORTED') {
      console.error('[request] 请求超时')
      return Promise.reject(new Error('请求超时，请稍后再试'))
    }
    console.error('[request] 网络异常:', error.message)
    return Promise.reject(new Error(error.message || '网络异常'))
  }
)

export function request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  return service.request<unknown, T>(config)
}

export default service
