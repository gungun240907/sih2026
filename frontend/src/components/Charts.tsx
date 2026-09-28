import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Stats } from '../api/client'

const REC_COLORS: Record<string, string> = {
  apply: '#4caf82',
  maybe: '#f0a500',
  skip: '#e05c5c',
}

export function ScoreChart({ stats }: { stats: Stats | null }) {
  if (!stats) return null
  const data = Object.entries(stats.score_bins).map(([range, count]) => ({ range: `${range}%`, count }))
  return (
    <section className="rounded-2xl border border-border bg-card p-6 md:col-span-2">
      <h2 className="mb-4 border-b border-border pb-2 text-lg font-bold">📊 Score Distribution</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3d4060" />
            <XAxis dataKey="range" stroke="#9098b1" tickLine={false} />
            <YAxis allowDecimals={false} stroke="#9098b1" tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#1e2130', border: '1px solid #3d4060', borderRadius: 8 }}
              labelStyle={{ color: '#e0e0e0' }}
              cursor={{ fill: '#25284055' }}
            />
            <Bar dataKey="count" fill="#7c83ff" radius={[6, 6, 0, 0]} />
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
    <section className="rounded-2xl border border-border bg-card p-6">
      <h2 className="mb-4 border-b border-border pb-2 text-lg font-bold">🎯 Recommendations</h2>
      <div className="flex flex-col gap-4">
        {Object.entries(stats.recommendations).map(([rec, count]) => {
          const pct = (count / total) * 100
          const color = REC_COLORS[rec] ?? '#9098b1'
          return (
            <div key={rec}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="font-semibold uppercase" style={{ color }}>{rec}</span>
                <span className="text-muted">{count} jobs ({Math.round(pct)}%)</span>
              </div>
              <div className="h-2 rounded bg-card2">
                <div className="h-2 rounded" style={{ background: color, width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
