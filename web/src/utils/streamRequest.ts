import { fetchEventSource } from '@microsoft/fetch-event-source'
import { clearToken, getToken } from './auth'

type StreamRequestOptions<T> = {
  data?: T
  signal?: AbortSignal
  onMessage: (message: string) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export async function streamPost<T>(url: string, options: StreamRequestOptions<T>) {
  const token = getToken()
  await fetchEventSource(`${API_BASE_URL}${url}`, {
    method: 'POST',
    signal: options.signal,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(options.data ?? {}),
    openWhenHidden: true,
    async onopen(response) {
      if (response.status === 401) {
        clearToken()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        throw new Error('登录已过期，请重新登录')
      }
      if (!response.ok) {
        throw new Error(`请求失败：${response.status}`)
      }
    },
    onmessage(event) {
      if (event.event === 'done' || event.data === '[DONE]') {
        options.onDone?.()
        return
      }
      if (event.data) {
        options.onMessage(event.data)
      }
    },
    onerror(error) {
      const normalizedError = error instanceof Error ? error : new Error('流式请求失败')
      options.onError?.(normalizedError)
      throw normalizedError
    },
  })
}
