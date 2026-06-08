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
