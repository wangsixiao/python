import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  GeneratedImage,
  ImageGenerate,
  ImageModelOption,
  LlmModelOption,
  Item,
  ItemCreate,
  ItemUpdate,
} from './types'

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

export const categoryApi = {
  list: () => request<Category[]>(`${API_BASE}/category/list`),

  detail: (id: number) =>
    request<Category>(`${API_BASE}/category/detail?id=${id}`),

  add: (data: CategoryCreate) =>
    request<Category>(`${API_BASE}/category/add`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: CategoryUpdate) =>
    request<Category>(`${API_BASE}/category/update`, {
      method: 'POST',
      body: JSON.stringify({ id, ...data }),
    }),

  delete: (id: number) =>
    request<{ success: boolean }>(`${API_BASE}/category/delete`, {
      method: 'POST',
      body: JSON.stringify({ id }),
    }),
}

export const itemApi = {
  list: (categoryId?: number | null) => {
    const query =
      categoryId != null ? `?category_id=${categoryId}` : ''
    return request<Item[]>(`${API_BASE}/list${query}`)
  },

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

export const imageApi = {
  models: () => request<ImageModelOption[]>(`${API_BASE}/image/models`),

  llmModels: () => request<LlmModelOption[]>(`${API_BASE}/image/llm-models`),

  list: (keyword?: string) => {
    const query = keyword?.trim()
      ? `?q=${encodeURIComponent(keyword.trim())}`
      : ''
    return request<GeneratedImage[]>(`${API_BASE}/image/list${query}`)
  },

  detail: (id: number) =>
    request<GeneratedImage>(`${API_BASE}/image/detail?id=${id}`),

  generate: (data: ImageGenerate) =>
    request<GeneratedImage>(`${API_BASE}/image/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<{ success: boolean }>(`${API_BASE}/image/delete`, {
      method: 'POST',
      body: JSON.stringify({ id }),
    }),
}
