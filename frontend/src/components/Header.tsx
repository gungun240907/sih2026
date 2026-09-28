import { NotebookPen } from 'lucide-react'
import SheetLinks from './SheetLinks'

const BADGES = ['FastAPI', 'React', 'Groq LLM', 'Google Sheets']

export default function Header() {
  return (
    <header className="fade-up rounded-[10px] border border-border bg-card p-6 shadow-[0_1px_2px_rgba(31,42,36,0.05),0_6px_20px_rgba(31,42,36,0.05)] md:p-8">
      <h1 className="flex items-center gap-2.5 text-2xl font-semibold text-text md:text-3xl">
        <NotebookPen size={26} strokeWidth={1.5} className="shrink-0 text-accent" aria-hidden />
        Job Application Agent
      </h1>
      <p className="mt-1 text-sm text-muted">
        Automated scraping · LLM scoring · Smart filtering · Live tracking
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {BADGES.map((b) => (
          <span
            key={b}
            className="rounded-md bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent"
          >
            {b}
          </span>
        ))}
      </div>
      <div className="mt-4">
        <SheetLinks />
      </div>
    </header>
  )
}
