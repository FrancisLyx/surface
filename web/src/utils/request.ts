import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

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

service.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message =
      error.response?.data?.message ||
      error.message ||
      '网络异常，请稍后重试'

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
