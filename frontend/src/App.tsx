import { useEffect, useState } from 'react'
import type { Stats } from './api/client'
import { api } from './api/client'
import Header from './components/Header'
import JobTable from './components/JobTable'
import LiveScraping from './components/LiveScraping'
import MetricsRow from './components/MetricsRow'
import RunControls from './components/RunControls'
import { RecommendationBars, ScoreChart } from './components/Charts'
import { useJobs } from './hooks/useJobs'

type View = 'dashboard' | 'live'

function initialView(): View {
  const v = new URLSearchParams(window.location.search).get('view')
  return v === 'live' ? 'live' : 'dashboard'
}

export default function App() {
  const { jobs, loading, error, filters, setFilters, updateStatus, clearAll, pipeline, reload } = useJobs()
  const [stats, setStats] = useState<Stats | null>(null)
  const [view, setView] = useState<View>(initialView)

  useEffect(() => {
    api.getStats().then(setStats).catch(() => setStats(null))
  }, [jobs])

  const running = pipeline.status.state === 'running'

  const goLive = (newTab: boolean) => {
    const url = `${window.location.pathname}?view=live`
    if (newTab) window.open(url, '_blank', 'noopener')
    else {
      window.history.pushState(null, '', url)
      setView('live')
    }
  }

  const goDashboard = () => {
    window.history.pushState(null, '', window.location.pathname)
    setView('dashboard')
  }

  const handleRun = async () => {
    try {
      await pipeline.run()
      // full new page for live scraping (LinkedIn phase, then Naukri phase)
      goLive(true)
      setView('live')
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to start pipeline')
    }
  }

  const handleClear = async () => {
    if (!window.confirm('Clear all jobs from the Google Sheet?')) return
    try {
      await clearAll()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to clear data')
    }
  }

  if (view === 'live') {
    return (
      <LiveScraping
        status={pipeline.status}
        connected={pipeline.connected}
        onBack={goDashboard}
      />
    )
  }

  return (
    <div className="flex min-h-screen">
      <RunControls
        onRun={handleRun}
        onClear={handleClear}
        running={running}
        state={pipeline.status.state}
        message={pipeline.status.message}
        step={pipeline.status.step}
        totalSteps={pipeline.status.total_steps}
        connected={pipeline.connected}
        error={pipeline.status.error}
      />

      <main className="flex-1 space-y-6 overflow-y-auto p-8">
        <Header />
        {running && (
          <button
            onClick={() => goLive(true)}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover"
          >
            ⚡ Watch live scraping in a new tab
          </button>
        )}
        <MetricsRow stats={stats} />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <ScoreChart stats={stats} />
          <RecommendationBars stats={stats} />
        </div>
        <JobTable
          jobs={jobs}
          loading={loading}
          error={error}
          filters={filters}
          onFiltersChange={setFilters}
          onStatusUpdate={updateStatus}
        />
        <footer className="pb-4 text-center text-xs text-muted">
          Job Application Agent · FastAPI + React ·{' '}
          <button onClick={reload} className="text-accent hover:underline">Refresh data</button>
        </footer>
      </main>
    </div>
  )
}
