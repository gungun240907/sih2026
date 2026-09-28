import { useCallback, useEffect, useRef, useState } from 'react'
import { FileText, Pencil, RefreshCw, Save, Sparkles, Upload, X } from 'lucide-react'
import { api, type ResumeAnalysis } from '../api/client'

interface Props {
  activeResumeId: string | null
  onActiveChange: (id: string | null) => void
  onSuggestLocation: (city: string) => void
}

export default function ResumePanel({ activeResumeId, onActiveChange, onSuggestLocation }: Props) {
  const [text, setText] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [warning, setWarning] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [resume, active] = await Promise.all([api.getResume(), api.getActiveResume().catch(() => null)])
      setText(resume.text)
      setDraft(resume.text)
      setSource(active?.resume_id ? `upload:${active.resume_id}` : resume.source)
      if (active) onActiveChange(active.resume_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load resume')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSave = async () => {
    if (!draft.trim()) {
      setError('Resume text must not be empty')
      return
    }
    try {
      setSaving(true)
      setError(null)
      const data = await api.updateResume(draft.trim())
      setText(data.text)
      setDraft(data.text)
      setSource(data.source)
      setEditing(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save resume')
    } finally {
      setSaving(false)
    }
  }

  const handleFile = async (file: File) => {
    try {
      setUploading(true)
      setError(null)
      setWarning(null)
      const up = await api.uploadResume(file)
      setWarning(up.warning)
      onActiveChange(up.resume_id)
      // the upload also replaced the default resume — reload it as the preview
      const updated = await api.getResume()
      setText(updated.text)
      setDraft(updated.text)
      setSource(`${updated.source} (from ${up.filename})`)
      const a = await api.analyzeResume({ resume_id: up.resume_id })
      setAnalysis(a)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true)
      setError(null)
      const a = await api.analyzeResume(
        activeResumeId ? { resume_id: activeResumeId } : { text: editing ? draft : (text ?? '') },
      )
      setAnalysis(a)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const useForRun = () => {
    if (analysis?.suggested_location) onSuggestLocation(analysis.suggested_location)
  }

  const exportHref = (fmt: 'md' | 'txt' | 'pdf') => api.exportResumeUrl(fmt, activeResumeId ?? undefined)

  return (
    <section className="rounded-[10px] border border-border bg-card p-4 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="label-caps flex items-center gap-1.5">
          <FileText size={13} strokeWidth={1.5} className="text-accent" aria-hidden />
          Current Resume{source ? ` · ${source}` : ''}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.md,.pdf,.png,.jpg,.jpeg,.webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) handleFile(f)
              e.target.value = ''
            }}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-semibold text-muted hover:border-accent hover:text-text disabled:opacity-50"
          >
            <Upload size={12} strokeWidth={1.5} aria-hidden />
            {uploading ? 'Uploading…' : 'Upload txt/pdf/image'}
          </button>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || loading}
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-semibold text-muted hover:border-accent hover:text-text disabled:opacity-50"
          >
            <Sparkles size={12} strokeWidth={1.5} aria-hidden />
            {analyzing ? 'Analyzing…' : 'Analyze'}
          </button>
          {!editing ? (
            <>
              <button
                onClick={load}
                disabled={loading}
                title="Reload resume"
                className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-semibold text-muted hover:border-accent hover:text-text disabled:opacity-50"
              >
                <RefreshCw size={12} strokeWidth={1.5} aria-hidden />
                Reload
              </button>
              <button
                onClick={() => setEditing(true)}
                disabled={loading || text == null}
                className="inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-1 text-xs font-semibold text-[#FBF9F4] hover:bg-accent-hover disabled:opacity-50"
              >
                <Pencil size={12} strokeWidth={1.5} aria-hidden />
                Edit
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => {
                  setDraft(text ?? '')
                  setEditing(false)
                  setError(null)
                }}
                disabled={saving}
                className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-semibold text-muted hover:border-accent hover:text-text disabled:opacity-50"
              >
                <X size={12} strokeWidth={1.5} aria-hidden />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-1 text-xs font-semibold text-[#FBF9F4] hover:bg-accent-hover disabled:opacity-50"
              >
                <Save size={12} strokeWidth={1.5} aria-hidden />
                {saving ? 'Saving…' : 'Save'}
              </button>
            </>
          )}
        </div>
      </div>

      {loading && <p className="text-xs text-muted">Loading resume…</p>}
      {error && <p className="mb-2 text-xs font-medium text-brick-text">{error}</p>}
      {warning && <p className="mb-2 text-xs font-medium text-amber">{warning}</p>}
      {activeResumeId && (
        <p className="mb-2 text-xs text-muted">
          Uploads replace the default resume — <span className="font-mono">{activeResumeId}</span> is active for scoring &amp; runs.
          {' '}<a className="font-semibold text-accent hover:underline" href={exportHref('md')}>md</a>
          {' · '}<a className="font-semibold text-accent hover:underline" href={exportHref('txt')}>txt</a>
          {' · '}<a className="font-semibold text-accent hover:underline" href={exportHref('pdf')}>pdf</a>
        </p>
      )}

      {analysis && (
        <div className="mb-3 rounded-lg bg-card2 p-3 text-xs leading-relaxed text-text">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-semibold">ATS score: {analysis.ats_score}/100</span>
            <button onClick={useForRun} className="font-semibold text-accent hover:text-accent-hover hover:underline">
              Use suggested location ({analysis.suggested_location})
            </button>
          </div>
          <p className="text-muted">{analysis.summary}</p>
          {analysis.skills.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {analysis.skills.map((s) => (
                <span key={s} className="rounded-full border border-border px-2 py-0.5 text-xs">{s}</span>
              ))}
            </div>
          )}
          {analysis.suggested_keywords.length > 0 && (
            <p className="mt-2 text-muted">Search for: <span className="font-semibold text-text">{analysis.suggested_keywords.join(', ')}</span></p>
          )}
          {analysis.gaps.length > 0 && (
            <ul className="mt-2 list-disc pl-4 text-muted">
              {analysis.gaps.map((g) => <li key={g}>{g}</li>)}
            </ul>
          )}
        </div>
      )}

      {!loading && text != null && !editing && (
        <>
          <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg bg-card2 p-3 text-xs leading-relaxed text-text">
            {text}
          </pre>
          <p className="mt-2 text-xs text-muted">{text.length.toLocaleString()} characters · used for LLM scoring</p>
        </>
      )}

      {editing && (
        <>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={14}
            className="w-full rounded-lg border border-border bg-card2 p-3 font-mono text-xs leading-relaxed text-text outline-none focus:border-accent"
          />
          <p className="mt-2 text-xs text-muted">{draft.length.toLocaleString()} characters</p>
        </>
      )}
    </section>
  )
}
