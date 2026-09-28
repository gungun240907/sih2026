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
}

const STEP_LABELS = ['Scrape portals', 'Score with LLM', 'Log to Sheets', 'Notify']

export default function RunControls({
  onRun, onClear, running, state, message, step, totalSteps, connected, error,
}: Props) {
  return (
    <aside className="w-72 shrink-0 border-r border-border bg-panel p-5 flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-bold text-text">🤖 Job Agent</h1>
        <div className="mt-1 flex items-center gap-2 text-xs text-muted">
          <span
            className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green' : 'bg-red'}`}
          />
          {connected ? 'Live connected' : 'Reconnecting…'}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">Controls</h2>
        <button
          onClick={onRun}
          disabled={running}
          className="w-full rounded-lg bg-accent px-4 py-2.5 font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? '⏳ Running…' : '▶ Run Agent Now'}
        </button>
        <button
          onClick={onClear}
          disabled={running}
          className="w-full rounded-lg border border-red bg-transparent px-4 py-2.5 font-semibold text-red transition hover:bg-red hover:text-white disabled:opacity-50"
        >
          🗑️ Clear All Data
        </button>
      </div>

      {state === 'running' && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="mb-2 flex items-center justify-between text-xs text-muted">
            <span>Progress</span>
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
        <div className="rounded-xl border border-green bg-card p-4 text-xs text-green">
          ✅ Pipeline complete. {message}
        </div>
      )}
      {state === 'failed' && (
        <div className="rounded-xl border border-red bg-card p-4 text-xs text-red break-words">
          ❌ {error ?? message ?? 'Pipeline failed'}
        </div>
      )}

      <div className="mt-auto flex flex-col gap-4 text-xs text-muted">
        <div>
          <h2 className="mb-1 font-semibold uppercase tracking-wider">Search Settings</h2>
          <p>Keywords: AI Engineer, ML Engineer</p>
          <p>Location: Bengaluru</p>
          <p>Min Score: 65% · Auto-apply: 85%+</p>
        </div>
        <div>
          <h2 className="mb-1 font-semibold uppercase tracking-wider">Pipeline</h2>
          <p>1. 🌐 Scrape LinkedIn</p>
          <p>2. 🧠 Score with LLM</p>
          <p>3. 📋 Log to Sheets</p>
        </div>
      </div>
    </aside>
  )
}
