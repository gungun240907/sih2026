import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Job, type JobFilters, type JobStatus } from '../api/client'
import { usePipelineStream } from './usePipelineStream'

const ALL_RECS = ['apply', 'maybe', 'skip'] as const
const ALL_STATUSES: JobStatus[] = ['new', 'applied', 'interview', 'offer', 'rejected']

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<JobFilters>({
    recommendation: [...ALL_RECS],
    status: [...ALL_STATUSES],
    min_score: 65,
  })
  const pipeline = usePipelineStream()

  const load = useCallback(async () => {
    try {
      setError(null)
      const data = await api.getJobs(filters)
      setJobs(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  // Refresh data when a pipeline run completes
  const prevState = useRef(pipeline.status.state)
  useEffect(() => {
    if (
      (prevState.current === 'running' && pipeline.status.state !== 'running') ||
      pipeline.status.state === 'completed'
    ) {
      load()
    }
    prevState.current = pipeline.status.state
  }, [pipeline.status.state, load])

  const updateStatus = useCallback(async (jobId: string, status: JobStatus) => {
    // optimistic update
    setJobs((prev) => prev.map((j) => (j.id === jobId ? { ...j, status } : j)))
    try {
      await api.updateStatus(jobId, status)
    } catch (e) {
      load() // revert on failure
      throw e
    }
  }, [load])

  const clearAll = useCallback(async () => {
    await api.clearJobs()
    setJobs([])
    load()
  }, [load])

  return { jobs, loading, error, filters, setFilters, updateStatus, clearAll, pipeline, reload: load }
}
