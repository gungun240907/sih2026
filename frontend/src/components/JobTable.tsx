import { useMemo, useState } from 'react'
import type { Job, JobFilters, JobStatus, Recommendation } from '../api/client'

const STATUS_OPTIONS: { value: JobStatus; label: string }[] = [
  { value: 'new', label: '🆕 New' },
  { value: 'applied', label: '📨 Applied' },
  { value: 'interview', label: '🎤 Interview' },
  { value: 'offer', label: '🎉 Offer' },
  { value: 'rejected', label: '❌ Rejected' },
]

const REC_STYLE: Record<string, string> = {
  apply: 'bg-green/15 text-green border-green/40',
  maybe: 'bg-amber/15 text-amber border-amber/40',
  skip: 'bg-red/15 text-red border-red/40',
}

interface Props {
  jobs: Job[]
  loading: boolean
  error: string | null
  filters: JobFilters
  onFiltersChange: (f: JobFilters) => void
  onStatusUpdate: (jobId: string, status: JobStatus) => Promise<void>
}

const REC_VALUES: Recommendation[] = ['apply', 'maybe', 'skip']

export default function JobTable({ jobs, loading, error, filters, onFiltersChange, onStatusUpdate }: Props) {
  const [sortDesc, setSortDesc] = useState(true)
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const availableStatuses = useMemo(
    () => Array.from(new Set<JobStatus>(jobs.map((j) => j.status))),
    [jobs],
  )

  const filtered = useMemo(() => {
    const rows = jobs.filter(
      (j) =>
        filters.recommendation.includes(j.recommendation) &&
        filters.status.includes(j.status) &&
        j.match_score * 100 >= filters.min_score,
    )
    rows.sort((a, b) => (sortDesc ? b.match_score - a.match_score : a.match_score - b.match_score))
    return rows
  }, [jobs, filters, sortDesc])

  const toggle = <T,>(list: T[], value: T) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value]

  const handleStatusChange = async (jobId: string, status: JobStatus) => {
    setUpdatingId(jobId)
    try {
      await onStatusUpdate(jobId, status)
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return <div className="rounded-2xl border border-border bg-card p-10 text-center text-muted">Loading jobs…</div>
  }
  if (error) {
    return <div className="rounded-2xl border border-red bg-card p-6 text-red">Could not load data: {error}</div>
  }
  if (jobs.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-card p-10 text-center text-muted">
        No jobs logged yet. Click <strong className="text-accent">▶ Run Agent Now</strong> in the sidebar.
      </div>
    )
  }

  return (
    <section className="rounded-2xl border border-border bg-card p-6">
      <h2 className="mb-4 border-b border-border pb-2 text-lg font-bold">💼 Job Pipeline</h2>

      <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted">Recommendation</p>
          <div className="flex flex-wrap gap-1.5">
            {REC_VALUES.map((r) => (
              <button
                key={r}
                onClick={() => onFiltersChange({ ...filters, recommendation: toggle(filters.recommendation, r) })}
                className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize transition ${
                  filters.recommendation.includes(r) ? REC_STYLE[r] : 'border-border text-muted'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted">Status</p>
          <div className="flex flex-wrap gap-1.5">
            {availableStatuses.map((s) => (
              <button
                key={s}
                onClick={() => onFiltersChange({ ...filters, status: toggle(filters.status, s) })}
                className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize transition ${
                  filters.status.includes(s)
                    ? 'border-accent/40 bg-accent/15 text-accent'
                    : 'border-border text-muted'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted">Min score: {filters.min_score}%</p>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={filters.min_score}
            onChange={(e) => onFiltersChange({ ...filters, min_score: Number(e.target.value) })}
            className="w-full accent-[#7c83ff]"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-card2 text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Location</th>
              <th
                className="cursor-pointer px-4 py-3 select-none hover:text-text"
                onClick={() => setSortDesc((v) => !v)}
              >
                Score {sortDesc ? '↓' : '↑'}
              </th>
              <th className="px-4 py-3">Rec</th>
              <th className="px-4 py-3">✅ Matched</th>
              <th className="px-4 py-3">❌ Missing</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">URL</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((job) => (
              <tr key={job.id} className="border-t border-border hover:bg-card2/50">
                <td className="max-w-56 truncate px-4 py-3 font-medium" title={job.title}>{job.title}</td>
                <td className="px-4 py-3">{job.company}</td>
                <td className="px-4 py-3 text-muted">{job.location}</td>
                <td className="px-4 py-3 font-bold text-accent">{Math.round(job.match_score * 100)}%</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${REC_STYLE[job.recommendation] ?? 'border-border text-muted'}`}>
                    {job.recommendation || '—'}
                  </span>
                </td>
                <td className="max-w-40 truncate px-4 py-3 text-xs text-green" title={job.matched_skills.join(', ')}>
                  {job.matched_skills.join(', ') || '—'}
                </td>
                <td className="max-w-40 truncate px-4 py-3 text-xs text-red" title={job.missing_skills.join(', ')}>
                  {job.missing_skills.join(', ') || '—'}
                </td>
                <td className="px-4 py-3">
                  <select
                    value={job.status}
                    disabled={updatingId === job.id}
                    onChange={(e) => handleStatusChange(job.id, e.target.value as JobStatus)}
                    className="rounded-lg border border-border bg-card px-2 py-1 text-xs text-text outline-none focus:border-accent disabled:opacity-50"
                  >
                    {STATUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  {job.url && (
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-md bg-accent px-3 py-1 text-xs font-semibold text-white hover:bg-accent-hover"
                    >
                      View
                    </a>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted">
                  No jobs match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">
        Showing {filtered.length} of {jobs.length} jobs · sorted by score {sortDesc ? '(high → low)' : '(low → high)'}
      </p>
    </section>
  )
}
