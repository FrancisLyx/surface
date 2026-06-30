import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { clearToken, getToken } from './auth'

export type ApiResponse<T> = {
  code: number
  message: string
  data: T
  request_id: string
}

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

service.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message =
      error.response?.data?.message ||
      error.message ||
      '网络异常，请稍后重试'

    if (error.response?.status === 401) {
      clearToken()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(new Error(message))
  },
)

export async function request<T>(config: AxiosRequestConfig) {
  const response = await service.request<ApiResponse<T>>(config)
  const payload = response.data

  if (payload.code !== 200) {
    throw new Error(payload.message || '请求失败')
  }

  return payload.data
}

export function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig) {
  return request<T>({
    ...config,
    url,
    method: 'POST',
    data,
  })
}

export function get<T>(url: string, config?: AxiosRequestConfig) {
  return request<T>({
    ...config,
    url,
    method: 'GET',
  })
}
