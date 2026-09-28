export type JobStatus = 'new' | 'applied' | 'interview' | 'offer' | 'rejected'
export type Recommendation = 'apply' | 'maybe' | 'skip' | ''

export interface Job {
  id: string
  title: string
  company: string
  location: string
  url: string
  source: string
  match_score: number
  recommendation: Recommendation
  matched_skills: string[]
  missing_skills: string[]
  status: JobStatus
  scraped_at: string
}

export interface Stats {
  total: number
  apply_count: number
  maybe_count: number
  skip_count: number
  avg_score: number
  top_score: number
  score_bins: Record<string, number>
  recommendations: Record<string, number>
}

export type RunState = 'idle' | 'running' | 'completed' | 'failed'

export interface ScrapedJobRef {
  source: string
  title: string
  company: string
  url: string
  message: string
}

export interface RunStatus {
  run_id: string | null
  state: RunState
  step: number
  total_steps: number
  event: string | null
  message: string | null
  started_at: string | null
  finished_at: string | null
  counters: Record<string, number>
  recent_jobs?: ScrapedJobRef[]
  summary?: Record<string, unknown> | null
  error?: string | null
}

export interface JobFilters {
  recommendation: Recommendation[]
  status: JobStatus[]
  min_score: number
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getJobs: (filters?: Partial<JobFilters> & { sort?: string }) => {
    const params = new URLSearchParams()
    filters?.recommendation?.forEach((r) => params.append('recommendation', r))
    filters?.status?.forEach((s) => params.append('status', s))
    if (filters?.min_score != null) params.set('min_score', String(filters.min_score / 100))
    if (filters?.sort) params.set('sort', filters.sort)
    const qs = params.toString()
    return request<Job[]>(`/api/jobs${qs ? `?${qs}` : ''}`)
  },
  updateStatus: (jobId: string, status: JobStatus) =>
    request<Job>(`/api/jobs/${jobId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  clearJobs: () => request<{ ok: boolean }>('/api/jobs', { method: 'DELETE' }),
  getStats: () => request<Stats>('/api/stats'),
  runPipeline: (params?: Record<string, unknown>) =>
    request<{ run_id: string; state: string }>('/api/pipeline/run', {
      method: 'POST',
      body: JSON.stringify(params ?? {}),
    }),
  getRunStatus: () => request<RunStatus>('/api/pipeline/status'),
}
