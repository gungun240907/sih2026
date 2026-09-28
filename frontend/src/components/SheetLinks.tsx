import { useEffect, useState } from 'react'
import { ArrowDownToLine, Table2 } from 'lucide-react'

export default function SheetLinks() {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/sheet/url')
      .then((r) => {
        if (!r.ok) throw new Error()
        return r.json()
      })
      .then((d) => setUrl(d.url))
      .catch(() => setError(true))
  }, [])

  const btn =
    'inline-flex items-center gap-1.5 rounded-full border border-border bg-card2 px-3 py-1.5 text-xs font-semibold text-text hover:border-accent hover:text-accent'

  if (error || url === null) {
    return (
      <span className="text-xs text-muted" title="Sheet not reachable">
        {error ? 'Sheet unavailable' : 'Locating sheet…'}
      </span>
    )
  }

  return (
    <div className="flex flex-wrap gap-2">
      <a href={url} target="_blank" rel="noreferrer" className={btn}>
        <Table2 size={13} strokeWidth={1.5} aria-hidden />
        View Google Sheet
      </a>
      <a href="/api/sheet/export?fmt=csv" className={btn}>
        <ArrowDownToLine size={13} strokeWidth={1.5} aria-hidden />
        CSV
      </a>
      <a href="/api/sheet/export?fmt=xlsx" className={btn}>
        <ArrowDownToLine size={13} strokeWidth={1.5} aria-hidden />
        Excel
      </a>
    </div>
  )
}
