import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { categoryApi, itemApi } from '../api'
import type { Category, Item } from '../types'

const emptyForm = { title: '', description: '', category_id: '' }

export default function ItemsPage() {
  const [items, setItems] = useState<Item[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [form, setForm] = useState(emptyForm)
  const [filterCategoryId, setFilterCategoryId] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCategories = useCallback(async () => {
    const data = await categoryApi.list()
    setCategories(data)
  }, [])

  const loadItems = useCallback(async () => {
    try {
      setError(null)
      const categoryId =
        filterCategoryId === '' ? undefined : Number(filterCategoryId)
      const data = await itemApi.list(categoryId)
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [filterCategoryId])

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  useEffect(() => {
    setLoading(true)
    loadItems()
  }, [loadItems])

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        category_id: form.category_id ? Number(form.category_id) : null,
      }

      if (editingId) {
        await itemApi.update(editingId, payload)
      } else {
        await itemApi.add(payload)
      }

      resetForm()
      await loadItems()
      await loadCategories()
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (item: Item) => {
    setEditingId(item.id)
    setForm({
      title: item.title,
      description: item.description ?? '',
      category_id: item.category_id ? String(item.category_id) : '',
    })
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条记录吗？')) return

    setError(null)
    try {
      await itemApi.delete(id)
      if (editingId === id) resetForm()
      await loadItems()
      await loadCategories()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}

      <section className="form-section">
        <h2>{editingId ? '编辑物品' : '新增物品'}</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="field">
            <label htmlFor="title">标题 *</label>
            <input
              id="title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="输入标题"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="category">分类</label>
            <select
              id="category"
              value={form.category_id}
              onChange={(e) =>
                setForm({ ...form, category_id: e.target.value })
              }
            >
              <option value="">未分类</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="description">描述</label>
            <textarea
              id="description"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="输入描述（可选）"
              rows={3}
            />
          </div>
          <div className="actions">
            <button type="submit" disabled={submitting}>
              {submitting ? '提交中...' : editingId ? '保存' : '创建'}
            </button>
            {editingId && (
              <button type="button" className="secondary" onClick={resetForm}>
                取消
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="list-section">
        <div className="list-header">
          <h2>物品列表</h2>
          <div className="field filter-field">
            <label htmlFor="filter-category">按分类筛选</label>
            <select
              id="filter-category"
              value={filterCategoryId}
              onChange={(e) => setFilterCategoryId(e.target.value)}
            >
              <option value="">全部分类</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {loading ? (
          <p className="hint">加载中...</p>
        ) : items.length === 0 ? (
          <p className="hint">暂无数据，请添加物品或调整筛选条件</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>标题</th>
                  <th>分类</th>
                  <th>描述</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.id}
                    className={editingId === item.id ? 'active' : ''}
                  >
                    <td>{item.id}</td>
                    <td>{item.title}</td>
                    <td>{item.category_name || '未分类'}</td>
                    <td>{item.description || '—'}</td>
                    <td>
                      {new Date(item.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td className="row-actions">
                      <button type="button" onClick={() => handleEdit(item)}>
                        编辑
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => handleDelete(item.id)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
