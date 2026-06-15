export interface Category {
  id: number
  name: string
  description: string | null
  item_count: number
  created_at: string
  updated_at: string
}

export interface CategoryCreate {
  name: string
  description?: string | null
}

export interface CategoryUpdate {
  name?: string
  description?: string | null
}

export interface Item {
  id: number
  title: string
  description: string | null
  category_id: number | null
  category_name: string | null
  created_at: string
  updated_at: string
}

export interface ItemCreate {
  title: string
  description?: string | null
  category_id?: number | null
}

export interface ItemUpdate {
  title?: string
  description?: string | null
  category_id?: number | null
}

export interface GeneratedImage {
  id: number
  prompt: string
  visual_brief: string | null
  image_url: string
  model: string | null
  size: string | null
  created_at: string
  updated_at: string
}

export interface ImageModelOption {
  value: string
  label: string
  provider: string
}

export interface LlmModelOption {
  value: string
  label: string
  provider: string
}

export interface ImageGenerate {
  prompt: string
  size?: string | null
  model?: string | null
  llm_model?: string | null
  use_visual_brief?: boolean
}

export type ImageGenerateMode = 'direct' | 'visual_brief'
