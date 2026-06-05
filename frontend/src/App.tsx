import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { itemApi } from './api'
import type { Item } from './types'
import './App.css'

const emptyForm = { title: '', description: '' }

function App() {
  const [items, setItems] = useState<Item[]>([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadItems = useCallback(async () => {
    try {
      setError(null)
      const data = await itemApi.list()
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
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
      }

      if (editingId) {
        await itemApi.update(editingId, payload)
      } else {
        await itemApi.add(payload)
      }

      resetForm()
      await loadItems()
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
    })
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条记录吗？')) return

    setError(null)
    try {
      await itemApi.delete(id)
      if (editingId === id) resetForm()
      await loadItems()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>物品管理</h1>
        <p>Python + PostgreSQL + React 全栈 CRUD 示例</p>
      </header>

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
        <h2>物品列表</h2>
        {loading ? (
          <p className="hint">加载中...</p>
        ) : items.length === 0 ? (
          <p className="hint">暂无数据，请添加第一条记录</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>标题</th>
                  <th>描述</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className={editingId === item.id ? 'active' : ''}>
                    <td>{item.id}</td>
                    <td>{item.title}</td>
                    <td>{item.description || '—'}</td>
                    <td>{new Date(item.created_at).toLocaleString('zh-CN')}</td>
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
    </div>
  )
}

export default App
