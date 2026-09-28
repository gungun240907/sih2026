import { Award, ClipboardList, CircleHelp, Gauge, ThumbsUp } from 'lucide-react'
import type { Stats } from '../api/client'

function Metric({
  label,
  value,
  accent,
  icon,
}: {
  label: string
  value: string | number
  accent: string
  icon: React.ReactNode
}) {
  return (
    <div
      className="rounded-[10px] border border-border bg-card p-5 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)]"
      style={{ borderTop: `3px solid ${accent}` }}
    >
      <p className="flex items-center gap-1.5 text-xs text-muted">
        {icon}
        {label}
      </p>
      <p className="mt-1 font-serif text-3xl font-semibold text-text">{value}</p>
    </div>
  )
}

export default function MetricsRow({ stats }: { stats: Stats | null }) {
  if (!stats) return null
  const iconProps = { size: 13, strokeWidth: 1.5 } as const
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-5">
      <Metric label="Total Tracked" value={stats.total} accent="#2F5D50" icon={<ClipboardList {...iconProps} aria-hidden />} />
      <Metric label="Apply" value={stats.apply_count} accent="#2E7D52" icon={<ThumbsUp {...iconProps} aria-hidden />} />
      <Metric label="Maybe" value={stats.maybe_count} accent="#8A5A00" icon={<CircleHelp {...iconProps} aria-hidden />} />
      <Metric label="Avg Score" value={`${Math.round(stats.avg_score * 100)}%`} accent="#C2603D" icon={<Gauge {...iconProps} aria-hidden />} />
      <Metric label="Top Score" value={`${Math.round(stats.top_score * 100)}%`} accent="#1F2A24" icon={<Award {...iconProps} aria-hidden />} />
    </div>
  )
}
