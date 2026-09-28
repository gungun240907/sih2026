import { Bot, Brain, ClipboardList, Globe, MapPin, Play, Trash2 } from 'lucide-react'
import { INDIAN_CITIES } from '../cities'

interface Props {
  onRun: () => void
  onClear: () => void
  running: boolean
  state: string
  message: string | null
  step: number
  totalSteps: number
  connected: boolean
  error?: string | null
  location: string
  onLocationChange: (city: string) => void
}

const STEP_LABELS = ['Scrape portals', 'Score with LLM', 'Log to Sheets', 'Notify']

export default function RunControls({
  onRun, onClear, running, state, message, step, totalSteps, connected, error,
  location, onLocationChange,
}: Props) {
  return (
    <aside className="fade-up flex w-full shrink-0 flex-col gap-6 border-b border-border bg-panel p-5 md:w-72 md:border-r md:border-b-0">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-text">
          <Bot size={20} strokeWidth={1.5} className="text-accent" aria-hidden />
          Job Agent
        </h1>
        <div className="mt-1 flex items-center gap-2 text-xs text-muted">
          <span
            className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green' : 'bg-amber'}`}
          />
          {connected ? 'Live connected' : 'Reconnecting…'}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="label-caps">Controls</h2>
        <button
          onClick={onRun}
          disabled={running}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-accent px-4 py-2.5 font-semibold text-[#FBF9F4] hover:bg-accent-hover active:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play size={15} strokeWidth={1.5} aria-hidden />
          {running ? 'Running…' : 'Run Agent Now'}
        </button>
        <button
          onClick={onClear}
          disabled={running}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-terra/60 bg-transparent px-4 py-2.5 font-semibold text-terra-deep hover:bg-terra hover:text-[#FBF9F4] active:bg-terra-deep active:text-[#FBF9F4] disabled:opacity-50"
        >
          <Trash2 size={15} strokeWidth={1.5} aria-hidden />
          Clear All Data
        </button>
      </div>

      {state === 'running' && (
        <div className="rounded-[10px] border border-border bg-card p-4 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)]">
          <div className="mb-2 flex items-center justify-between text-xs text-muted">
            <span className="label-caps">Progress</span>
            <span>{step}/{totalSteps}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-card2">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
          {message && <p className="mt-3 text-xs leading-relaxed text-text break-words">{message}</p>}
          <ul className="mt-3 space-y-1">
            {STEP_LABELS.map((label, i) => (
              <li key={label} className="flex items-center gap-2 text-xs">
                <span
                  className={
                    i + 1 < step ? 'text-green'
                    : i + 1 === step ? 'text-accent'
                    : 'text-muted'
                  }
                >
                  {i + 1 < step ? '✓' : i + 1 === step ? '●' : '○'}
                </span>
                <span className={i + 1 <= step ? 'text-text' : 'text-muted'}>{label}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {state === 'completed' && (
        <div className="rounded-[10px] border border-green/30 bg-green/10 p-4 text-xs font-medium text-green">
          Pipeline complete. {message}
        </div>
      )}
      {state === 'failed' && (
        <div className="rounded-[10px] border border-brick-border bg-brick-bg p-4 text-xs break-words">
          <p className="font-semibold text-brick-text">Run failed</p>
          <p className="mt-1 font-mono text-brick-text">{error ?? message ?? 'Pipeline failed'}</p>
        </div>
      )}

      <div className="mt-auto flex flex-col gap-4 text-xs text-muted">
        <div>
          <h2 className="label-caps mb-1">Search Settings</h2>
          <p>Keywords: AI Engineer, ML Engineer</p>
          <label className="mt-2 flex items-center gap-1.5 font-semibold text-text">
            <MapPin size={13} strokeWidth={1.5} className="text-accent" aria-hidden />
            Location
          </label>
          <select
            value={location}
            disabled={running}
            onChange={(e) => onLocationChange(e.target.value)}
            className="mt-1 w-full rounded-lg border border-border bg-card px-2 py-1.5 text-xs text-text outline-none hover:border-accent focus:border-accent disabled:opacity-50"
          >
            {INDIAN_CITIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <p className="mt-2">Min Score: 65% · Auto-apply: 85%+</p>
        </div>
        <div>
          <h2 className="label-caps mb-1">Pipeline</h2>
          <p className="flex items-center gap-1.5"><Globe size={13} strokeWidth={1.5} aria-hidden /> 1. Scrape LinkedIn</p>
          <p className="flex items-center gap-1.5"><Brain size={13} strokeWidth={1.5} aria-hidden /> 2. Score with LLM</p>
          <p className="flex items-center gap-1.5"><ClipboardList size={13} strokeWidth={1.5} aria-hidden /> 3. Log to Sheets</p>
        </div>
      </div>
    </aside>
  )
}
