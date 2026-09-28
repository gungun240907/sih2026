import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type RunStatus } from '../api/client'

const IDLE: RunStatus = {
  run_id: null,
  state: 'idle',
  step: 0,
  total_steps: 4,
  event: null,
  message: null,
  started_at: null,
  finished_at: null,
  counters: {},
}

export function usePipelineStream() {
  const [status, setStatus] = useState<RunStatus>(IDLE)
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  const connect = useCallback(() => {
    esRef.current?.close()
    const es = new EventSource('/api/pipeline/stream')
    es.onopen = () => setConnected(true)
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as RunStatus
        setStatus(data)
        if (data.state === 'completed' || data.state === 'failed') {
          es.close()
          setConnected(false)
          // re-arm to idle after showing final state
          setTimeout(() => setStatus((s) => (s.state === data.state ? IDLE : s)), 6000)
          connect()
        }
      } catch { /* ignore malformed frames */ }
    }
    es.onerror = () => {
      setConnected(false)
      es.close()
      // retry after a delay unless component unmounted
      setTimeout(() => connect(), 5000)
    }
    esRef.current = es
  }, [])

  useEffect(() => {
    // On mount, reconcile with any run that may already be in progress
    api.getRunStatus().then((s) => {
      setStatus(s)
      connect()
    }).catch(() => connect())
    return () => esRef.current?.close()
  }, [connect])

  const run = useCallback(async (params?: Record<string, unknown>) => {
    await api.runPipeline(params)
    connect()
  }, [connect])

  return { status, connected, run }
}
