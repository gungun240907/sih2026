import type { RunStatus } from '../api/client'
import { ArrowLeft, Building2, Radio, Search } from 'lucide-react'
import SheetLinks from './SheetLinks'

interface Props {
  status: RunStatus
  connected: boolean
  onBack: () => void
}

function PortalPanel({
  title,
  subtitle,
  active,
  done,
  count,
  jobs,
  icon,
}: {
  title: string
  subtitle: string
  active: boolean
  done: boolean
  count: number | undefined
  jobs: { title: string; company: string; url: string; message: string }[]
  icon: React.ReactNode
}) {
  return (
    <section
      className={`fade-up flex-1 rounded-[10px] border bg-card p-5 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)] ${
        active ? 'border-accent' : 'border-border'
      }`}
    >
      <div className="mb-1 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-base font-semibold text-text">
          {icon}
          {title}
        </h2>
        <span className="text-xs text-muted">
          {done ? '✓ done' : active ? '● live' : '○ waiting'}
        </span>
      </div>
      <p className="mb-3 text-xs text-muted">{subtitle}</p>
      {count != null && (
        <p className="mb-3 font-serif text-lg font-semibold text-text">
          {count} jobs scraped
        </p>
      )}
      {jobs.length === 0 ? (
        <p className="text-xs text-muted">
          {active ? 'Scraping… jobs appear here as they are found.' : 'Waiting for this portal.'}
        </p>
      ) : (
        <ul className="max-h-96 space-y-2 overflow-y-auto">
          {[...jobs].reverse().map((j, i) => (
            <li key={`${j.url}-${i}`} className="rounded-lg bg-card2 p-2.5 text-xs">
              <a
                href={j.url}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-accent hover:text-accent-hover hover:underline"
              >
                {j.title}
              </a>
              <div className="text-muted">{j.company}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default function LiveScraping({ status, connected, onBack }: Props) {
  const feed = status.recent_jobs ?? []
  const liJobs = feed.filter((j) => j.source === 'linkedin')
  const nkJobs = feed.filter((j) => j.source === 'naukri')
  const scraping = status.state === 'running' && status.step <= 1
  // LinkedIn runs first, Naukri second: Naukri panel activates once LinkedIn count lands
  const liDone = status.counters.found_linkedin != null
  const liActive = scraping && !liDone
  const nkActive = scraping && liDone

  return (
    <div className="min-h-screen bg-bg p-4 sm:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold text-text">
              <Radio size={20} strokeWidth={1.5} className="text-accent" aria-hidden />
              Live Scraping
            </h1>
            <p className="mt-1 flex items-center gap-2 text-xs text-muted">
              <span
                className={`inline-block h-2 w-2 rounded-full ${
                  connected ? 'bg-green' : 'bg-amber'
                }`}
              />
              {connected ? 'Live connected' : 'Reconnecting…'}
              {status.message && <span>· {status.message}</span>}
            </p>
          </div>
          <button
            onClick={onBack}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-4 py-2 text-sm font-semibold text-text hover:border-accent hover:text-accent"
          >
            <ArrowLeft size={15} strokeWidth={1.5} aria-hidden />
            Back to Dashboard
          </button>
        </div>

        {status.state === 'completed' && (
          <div className="rounded-[10px] border border-green/30 bg-green/10 p-4 text-sm font-medium text-green">
            {(status.counters.found_linkedin ?? 0) + (status.counters.found_naukri ?? 0) === 0 ? (
              <>{status.message ?? 'No jobs available right now.'}</>
            ) : (
              <>Scraping complete — {status.counters.found_linkedin ?? 0} LinkedIn +{' '}
              {status.counters.found_naukri ?? 0} Naukri jobs. Scoring and Sheets logging continue
              in the background; results appear on the dashboard.</>
            )}
          </div>
        )}
        {status.state === 'failed' && (
          <div className="rounded-[10px] border border-brick-border bg-brick-bg p-4 text-sm">
            <p className="font-mono text-xs text-brick-text">{status.error ?? status.message ?? 'Pipeline failed'}</p>
          </div>
        )}

        <div className="flex flex-col gap-6 md:flex-row">
          <PortalPanel
            title="Phase 1 — LinkedIn"
            subtitle="Left Chrome window on your desktop"
            active={liActive}
            done={liDone}
            count={status.counters.found_linkedin}
            jobs={liJobs}
            icon={<Building2 size={17} strokeWidth={1.5} className="text-accent" aria-hidden />}
          />
          <PortalPanel
            title="Phase 2 — Naukri"
            subtitle="Right Chrome window on your desktop"
            active={nkActive}
            done={status.counters.found_naukri != null}
            count={status.counters.found_naukri}
            jobs={nkJobs}
            icon={<Search size={17} strokeWidth={1.5} className="text-accent" aria-hidden />}
          />
        </div>

        <p className="text-center text-xs text-muted">
          Headed Chrome windows open on your desktop alongside this page — watch either.
        </p>
        <div className="flex justify-center">
          <SheetLinks />
        </div>
      </div>
    </div>
  )
}
