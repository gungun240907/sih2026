import SheetLinks from './SheetLinks'

const BADGES = ['FastAPI', 'React', 'Groq LLM', 'Google Sheets']

export default function Header() {
  return (
    <header className="rounded-2xl border border-border bg-gradient-to-br from-card to-card2 p-8">
      <h1 className="text-3xl font-extrabold text-white">🤖 Job Application Agent</h1>
      <p className="mt-1 text-muted">
        Automated scraping · LLM scoring · Smart filtering · Live tracking
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {BADGES.map((b) => (
          <span
            key={b}
            className="rounded-full border border-accent bg-card2 px-3 py-0.5 text-xs font-semibold text-accent"
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
