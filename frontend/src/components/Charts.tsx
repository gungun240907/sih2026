import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartColumn, Crosshair } from 'lucide-react'
import type { Stats } from '../api/client'

const REC_COLORS: Record<string, string> = {
  apply: '#2E7D52',
  maybe: '#8A5A00',
  skip: '#A63A2E',
}

export function ScoreChart({ stats }: { stats: Stats | null }) {
  if (!stats) return null
  const data = Object.entries(stats.score_bins).map(([range, count]) => ({ range: `${range}%`, count }))
  return (
    <section className="rounded-[10px] border border-border bg-card p-6 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)] md:col-span-2">
      <h2 className="mb-4 flex items-center gap-2 border-b border-border pb-2 text-lg font-semibold text-text">
        <ChartColumn size={18} strokeWidth={1.5} className="text-accent" aria-hidden />
        Score Distribution
      </h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="#E3DED2" strokeDasharray="2 4" vertical={false} />
            <XAxis dataKey="range" stroke="#6B7268" tickLine={false} axisLine={{ stroke: '#E3DED2' }} tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} stroke="#6B7268" tickLine={false} axisLine={{ stroke: '#E3DED2' }} tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: '#FBF9F4', border: '1px solid #E3DED2', borderRadius: 8, boxShadow: '0 4px 14px rgba(31,42,36,0.08)', color: '#1F2A24', fontSize: 12 }}
              labelStyle={{ color: '#1F2A24', fontWeight: 600 }}
              cursor={{ fill: 'rgba(47,93,80,0.08)' }}
            />
            <Bar dataKey="count" fill="#2F5D50" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

export function RecommendationBars({ stats }: { stats: Stats | null }) {
  if (!stats) return null
  const total = stats.total || 1
  return (
    <section className="rounded-[10px] border border-border bg-card p-6 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_4px_14px_rgba(31,42,36,0.05)]">
      <h2 className="mb-4 flex items-center gap-2 border-b border-border pb-2 text-lg font-semibold text-text">
        <Crosshair size={18} strokeWidth={1.5} className="text-accent" aria-hidden />
        Recommendations
      </h2>
      <div className="flex flex-col gap-4">
        {Object.entries(stats.recommendations).map(([rec, count]) => {
          const pct = (count / total) * 100
          const color = REC_COLORS[rec] ?? '#6B7268'
          return (
            <div key={rec}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="font-semibold uppercase" style={{ color }}>{rec}</span>
                <span className="text-muted">{count} jobs ({Math.round(pct)}%)</span>
              </div>
              <div className="h-2 rounded-full bg-card2">
                <div className="rec-fill h-2 rounded-full" style={{ background: color, width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
