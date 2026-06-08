import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { categoryApi } from '../api'
import type { Category } from '../types'

const emptyForm = { name: '', description: '' }

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCategories = useCallback(async () => {
    try {
      setError(null)
      const data = await categoryApi.list()
      setCategories(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
      }

      if (editingId) {
        await categoryApi.update(editingId, payload)
      } else {
        await categoryApi.add(payload)
      }

      resetForm()
      await loadCategories()
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (category: Category) => {
    setEditingId(category.id)
    setForm({
      name: category.name,
      description: category.description ?? '',
    })
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个分类吗？分类下有物品时无法删除。')) return

    setError(null)
    try {
      await categoryApi.delete(id)
      if (editingId === id) resetForm()
      await loadCategories()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}

      <section className="form-section">
        <h2>{editingId ? '编辑分类' : '新增分类'}</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="field">
            <label htmlFor="category-name">分类名称 *</label>
            <input
              id="category-name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="例如：书籍、电子产品"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="category-description">描述</label>
            <textarea
              id="category-description"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="分类说明（可选）"
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
        <h2>分类列表</h2>
        {loading ? (
          <p className="hint">加载中...</p>
        ) : categories.length === 0 ? (
          <p className="hint">暂无分类，请先创建分类，再到物品页关联</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>名称</th>
                  <th>描述</th>
                  <th>物品数</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr
                    key={category.id}
                    className={editingId === category.id ? 'active' : ''}
                  >
                    <td>{category.id}</td>
                    <td>{category.name}</td>
                    <td>{category.description || '—'}</td>
                    <td>{category.item_count}</td>
                    <td>
                      {new Date(category.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td className="row-actions">
                      <button type="button" onClick={() => handleEdit(category)}>
                        编辑
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => handleDelete(category.id)}
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
