import type { Stats } from '../api/client'

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-border bg-gradient-to-br from-card to-card2 p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-accent">{value}</p>
    </div>
  )
}

export default function MetricsRow({ stats }: { stats: Stats | null }) {
  if (!stats) return null
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
      <Metric label="📋 Total Tracked" value={stats.total} />
      <Metric label="✅ Apply" value={stats.apply_count} />
      <Metric label="🤔 Maybe" value={stats.maybe_count} />
      <Metric label="📈 Avg Score" value={`${Math.round(stats.avg_score * 100)}%`} />
      <Metric label="🏆 Top Score" value={`${Math.round(stats.top_score * 100)}%`} />
    </div>
  )
}
