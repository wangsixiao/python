import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { imageApi } from '../api'
import type {
  GeneratedImage,
  ImageGenerateMode,
  ImageModelOption,
  LlmModelOption,
} from '../types'

const DASHSCOPE_SIZE_OPTIONS = [
  { value: '512*512', label: '512 × 512' },
  { value: '1024*1024', label: '1024 × 1024' },
  { value: '1024*1536', label: '1024 × 1536' },
  { value: '1536*1024', label: '1536 × 1024' },
]

const DALLE3_SIZE_OPTIONS = [
  { value: '1024*1024', label: '1024 × 1024' },
  { value: '1024*1536', label: '1024 × 1792' },
  { value: '1536*1024', label: '1792 × 1024' },
]

const DALLE2_SIZE_OPTIONS = [
  { value: '512*512', label: '512 × 512' },
  { value: '1024*1024', label: '1024 × 1024' },
]

const GPT_IMAGE_SIZE_OPTIONS = [
  { value: '1024*1024', label: '1024 × 1024' },
  { value: '1024*1536', label: '1024 × 1536' },
  { value: '1536*1024', label: '1536 × 1024' },
]

function getSizeOptions(model: string) {
  if (model === 'dall-e-3') return DALLE3_SIZE_OPTIONS
  if (model === 'dall-e-2') return DALLE2_SIZE_OPTIONS
  if (model.startsWith('gpt-image-')) return GPT_IMAGE_SIZE_OPTIONS
  return DASHSCOPE_SIZE_OPTIONS
}

const MODE_OPTIONS: { value: ImageGenerateMode; label: string; hint: string }[] = [
  {
    value: 'direct',
    label: '直接生图',
    hint: '将提示词直接发送给所选文生图模型',
  },
  {
    value: 'visual_brief',
    label: '先分析再生图',
    hint: 'LLM 生成 Visual Brief 后再出图',
  },
]

export default function ImageGenPage() {
  const [prompt, setPrompt] = useState('')
  const [size, setSize] = useState('1024*1024')
  const [model, setModel] = useState('qwen-image-2.0-pro')
  const [llmModel, setLlmModel] = useState('qwen-plus')
  const [modelOptions, setModelOptions] = useState<ImageModelOption[]>([])
  const [llmModelOptions, setLlmModelOptions] = useState<LlmModelOption[]>([])
  const [mode, setMode] = useState<ImageGenerateMode>('visual_brief')
  const [historySearch, setHistorySearch] = useState('')
  const [images, setImages] = useState<GeneratedImage[]>([])
  const [latestImage, setLatestImage] = useState<GeneratedImage | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadModels = useCallback(async () => {
    const [imageModels, llmModels] = await Promise.all([
      imageApi.models(),
      imageApi.llmModels(),
    ])
    setModelOptions(imageModels)
    setLlmModelOptions(llmModels)
    if (imageModels.length > 0) {
      setModel((current) =>
        imageModels.some((option) => option.value === current)
          ? current
          : imageModels[0].value
      )
    }
    if (llmModels.length > 0) {
      setLlmModel((current) =>
        llmModels.some((option) => option.value === current)
          ? current
          : llmModels[0].value
      )
    }
  }, [])

  const sizeOptions = getSizeOptions(model)
  const dashscopeImageModels = modelOptions.filter(
    (option) => option.provider === 'dashscope'
  )
  const openaiImageModels = modelOptions.filter(
    (option) => option.provider === 'openai'
  )
  const dashscopeLlmModels = llmModelOptions.filter(
    (option) => option.provider === 'dashscope'
  )
  const openaiLlmModels = llmModelOptions.filter(
    (option) => option.provider === 'openai'
  )

  useEffect(() => {
    if (!sizeOptions.some((option) => option.value === size)) {
      setSize(sizeOptions[0]?.value ?? '1024*1024')
    }
  }, [model, size, sizeOptions])

  const loadImages = useCallback(async () => {
    try {
      setError(null)
      setLoading(true)
      const data = await imageApi.list(historySearch)
      setImages(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [historySearch])

  useEffect(() => {
    loadModels().catch((err) => {
      setError(err instanceof Error ? err.message : '加载模型列表失败')
    })
  }, [loadModels])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadImages()
    }, 300)
    return () => window.clearTimeout(timer)
  }, [loadImages])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    setGenerating(true)
    setError(null)

    try {
      const created = await imageApi.generate({
        prompt: prompt.trim(),
        size,
        model,
        llm_model: mode === 'visual_brief' ? llmModel : undefined,
        use_visual_brief: mode === 'visual_brief',
      })
      setLatestImage(created)
      setPrompt('')
      await loadImages()
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条生成记录吗？')) return

    setError(null)
    try {
      await imageApi.delete(id)
      if (latestImage?.id === id) setLatestImage(null)
      await loadImages()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}

      <section className="form-section">
        <h2>文生图</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="field">
            <label htmlFor="model">文生图模型</label>
            <select
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {dashscopeImageModels.length > 0 && (
                <optgroup label="阿里云 DashScope">
                  {dashscopeImageModels.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              )}
              {openaiImageModels.length > 0 && (
                <optgroup label="OpenAI">
                  {openaiImageModels.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
          {mode === 'visual_brief' && (
            <div className="field">
              <label htmlFor="llm-model">分析模型（Visual Brief）</label>
              <select
                id="llm-model"
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
              >
                {dashscopeLlmModels.length > 0 && (
                  <optgroup label="阿里云 DashScope">
                    {dashscopeLlmModels.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </optgroup>
                )}
                {openaiLlmModels.length > 0 && (
                  <optgroup label="OpenAI">
                    {openaiLlmModels.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>
          )}
          <div className="field">
            <label>生成模式</label>
            <div className="mode-options">
              {MODE_OPTIONS.map((option) => (
                <label key={option.value} className="mode-option">
                  <input
                    type="radio"
                    name="generate-mode"
                    value={option.value}
                    checked={mode === option.value}
                    onChange={() => setMode(option.value)}
                  />
                  <span className="mode-option-label">{option.label}</span>
                  <span className="mode-option-hint">{option.hint}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="field">
            <label htmlFor="prompt">提示词 *</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={
                mode === 'visual_brief'
                  ? '描述创作意图，系统将先由 LLM 生成 Visual Brief 再出图'
                  : '描述你想生成的图片，例如：一只橘猫坐在窗台上，阳光洒落，写实风格'
              }
              rows={5}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="size">图片尺寸</label>
            <select
              id="size"
              value={size}
              onChange={(e) => setSize(e.target.value)}
            >
              {sizeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="actions">
            <button type="submit" disabled={generating}>
              {generating
                ? mode === 'visual_brief'
                  ? 'LLM 分析中，正在生成图片...'
                  : '生成中，请稍候...'
                : '生成图片'}
            </button>
          </div>
        </form>
      </section>

      {latestImage && (
        <section className="form-section">
          <h2>本次生成结果</h2>
          <p className="hint">
            <strong>模型：</strong>
            {latestImage.model || '—'}
          </p>
          <p className="hint">
            <strong>原始提示词：</strong>
            {latestImage.prompt}
          </p>
          {latestImage.visual_brief && (
            <div className="visual-brief-box">
              <strong>Visual Brief（LLM 生成）</strong>
              <p>{latestImage.visual_brief}</p>
            </div>
          )}
          <div className="image-preview">
            <img src={latestImage.image_url} alt={latestImage.prompt} />
          </div>
        </section>
      )}

      <section className="list-section">
        <div className="list-header">
          <h2>生成历史</h2>
          <div className="field filter-field history-search-field">
            <label htmlFor="history-search">提示词搜索</label>
            <div className="history-search-row">
              <input
                id="history-search"
                type="search"
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                placeholder="搜索提示词或 Visual Brief"
              />
              {historySearch && (
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setHistorySearch('')}
                >
                  清空
                </button>
              )}
            </div>
          </div>
        </div>
        {loading ? (
          <p className="hint">加载中...</p>
        ) : images.length === 0 ? (
          <p className="hint">
            {historySearch.trim()
              ? `未找到包含「${historySearch.trim()}」的历史记录`
              : '暂无生成记录，输入提示词开始创作'}
          </p>
        ) : (
          <div className="image-grid">
            {images.map((image) => (
              <article key={image.id} className="image-card">
                <div className="image-card-preview">
                  <img src={image.image_url} alt={image.prompt} loading="lazy" />
                </div>
                <div className="image-card-body">
                  <p className="image-card-prompt">
                    <strong>提示词：</strong>
                    {image.prompt}
                  </p>
                  {image.visual_brief && (
                    <p className="image-card-brief">{image.visual_brief}</p>
                  )}
                  <p className="image-card-meta">
                    {image.model || '—'} · {image.size || '—'} ·{' '}
                    {new Date(image.created_at).toLocaleString('zh-CN')}
                  </p>
                  <div className="row-actions">
                    <a
                      href={image.image_url}
                      target="_blank"
                      rel="noreferrer"
                      className="link-button"
                    >
                      查看原图
                    </a>
                    <button
                      type="button"
                      className="danger"
                      onClick={() => handleDelete(image.id)}
                    >
                      删除
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  )
}
