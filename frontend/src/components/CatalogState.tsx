interface CatalogStateProps {
  kind: 'loading' | 'empty' | 'error' | 'not-found'
  onBack?(): void
}

const copy = {
  loading: ['Opening the collection…', 'Checking approved records and their provenance.'],
  empty: ['The collection is ready for its first work.', 'No approved CC0 artworks are available yet.'],
  error: ['The collection could not be reached.', 'Start the FastAPI backend, then refresh this page.'],
  'not-found': ['This artwork is not available.', 'It may not be published or may no longer meet the CC0 policy.'],
} as const

export function CatalogState({ kind, onBack }: CatalogStateProps) {
  return <main className="state-shell" role={kind === 'error' ? 'alert' : 'status'}>
    <span className="brand-mark">AI Aion</span>
    <div className="state-card">
      <p className="eyebrow">Open heritage catalog</p>
      <h1>{copy[kind][0]}</h1>
      <p>{copy[kind][1]}</p>
      {onBack && <button className="text-button" type="button" onClick={onBack}>← Back to gallery</button>}
    </div>
  </main>
}
