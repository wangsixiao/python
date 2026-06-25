import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { agentApi, imageApi } from '../api'
import type { AgentChatMessage, AgentToolCallLog, LlmModelOption } from '../types'

interface ChatEntry {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: AgentToolCallLog[]
}

const SUGGESTIONS = [
  '列出所有分类及物品数量',
  '创建一个「机器学习」分类',
  '列出没有分类的物品',
  '帮我新建 3 本编程书籍的物品',
]

function formatToolName(name: string): string {
  const labels: Record<string, string> = {
    list_categories: '查询分类',
    create_category: '创建分类',
    update_category: '更新分类',
    delete_category: '删除分类',
    list_items: '查询物品',
    create_item: '创建物品',
    update_item: '更新物品',
    delete_item: '删除物品',
  }
  return labels[name] ?? name
}

export default function AgentPage() {
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [input, setInput] = useState('')
  const [llmModel, setLlmModel] = useState('qwen-plus')
  const [llmModelOptions, setLlmModelOptions] = useState<LlmModelOption[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const loadModels = useCallback(async () => {
    const models = await imageApi.llmModels()
    setLlmModelOptions(models)
    if (models.length > 0) {
      setLlmModel((current) =>
        models.some((option) => option.value === current)
          ? current
          : models[0].value
      )
    }
  }, [])

  useEffect(() => {
    loadModels().catch((err) => {
      setError(err instanceof Error ? err.message : '加载模型列表失败')
    })
  }, [loadModels])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries, loading])

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userEntry: ChatEntry = { role: 'user', content: trimmed }
    const nextEntries = [...entries, userEntry]
    setEntries(nextEntries)
    setInput('')
    setLoading(true)
    setError(null)

    const apiMessages: AgentChatMessage[] = nextEntries.map((entry) => ({
      role: entry.role,
      content: entry.content,
    }))

    try {
      const response = await agentApi.chat(apiMessages, llmModel)
      setEntries((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.message,
          toolCalls: response.tool_calls.length > 0 ? response.tool_calls : undefined,
        },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : '对话失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const dashscopeModels = llmModelOptions.filter((m) => m.provider === 'dashscope')
  const openaiModels = llmModelOptions.filter((m) => m.provider === 'openai')

  return (
    <>
      {error && <div className="error">{error}</div>}

      <section className="form-section agent-section">
        <div className="agent-header">
          <div>
            <h2>物品管家 Agent</h2>
            <p className="hint">
              用自然语言管理分类和物品，Agent 会自动调用工具完成操作
            </p>
          </div>
          <div className="field agent-model-field">
            <label htmlFor="agent-llm-model">对话模型</label>
            <select
              id="agent-llm-model"
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              disabled={loading}
            >
              {dashscopeModels.length > 0 && (
                <optgroup label="阿里云 DashScope">
                  {dashscopeModels.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              )}
              {openaiModels.length > 0 && (
                <optgroup label="OpenAI">
                  {openaiModels.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        </div>

        <div className="agent-chat">
          {entries.length === 0 && (
            <div className="agent-empty">
              <p>试试这些指令：</p>
              <div className="agent-suggestions">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    className="secondary"
                    onClick={() => sendMessage(suggestion)}
                    disabled={loading}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {entries.map((entry, index) => (
            <div
              key={index}
              className={`agent-message agent-message-${entry.role}`}
            >
              <div className="agent-message-role">
                {entry.role === 'user' ? '你' : 'Agent'}
              </div>
              <div className="agent-message-content">{entry.content}</div>
              {entry.toolCalls && entry.toolCalls.length > 0 && (
                <div className="agent-tool-calls">
                  {entry.toolCalls.map((tool) => (
                    <details key={tool.id} className="agent-tool-call">
                      <summary>
                        <span
                          className={`agent-tool-status ${
                            tool.result.ok ? 'ok' : 'error'
                          }`}
                        >
                          {tool.result.ok ? '✓' : '✗'}
                        </span>
                        {formatToolName(tool.name)}
                      </summary>
                      <pre>{JSON.stringify(tool.result, null, 2)}</pre>
                    </details>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="agent-message agent-message-assistant">
              <div className="agent-message-role">Agent</div>
              <div className="agent-message-content agent-typing">
                思考中，正在调用工具...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="agent-input-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="例如：列出所有分类，然后把「Python 入门」移到编程类"
            rows={3}
            disabled={loading}
          />
          <div className="actions">
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? '处理中...' : '发送'}
            </button>
            {entries.length > 0 && (
              <button
                type="button"
                className="secondary"
                disabled={loading}
                onClick={() => {
                  setEntries([])
                  setError(null)
                }}
              >
                清空对话
              </button>
            )}
          </div>
        </form>
      </section>
    </>
  )
}
