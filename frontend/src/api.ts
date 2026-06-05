import type { Item, ItemCreate, ItemUpdate } from './types'

const API_BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const itemApi = {
  list: () => request<Item[]>(`${API_BASE}/list`),

  detail: (id: number) => request<Item>(`${API_BASE}/detail?id=${id}`),

  add: (data: ItemCreate) =>
    request<Item>(`${API_BASE}/add`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ItemUpdate) =>
    request<Item>(`${API_BASE}/update`, {
      method: 'POST',
      body: JSON.stringify({ id, ...data }),
    }),

  delete: (id: number) =>
    request<{ success: boolean }>(`${API_BASE}/delete`, {
      method: 'POST',
      body: JSON.stringify({ id }),
    }),
}
