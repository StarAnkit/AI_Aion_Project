import { useMemo, useState } from 'react'
import type { CatalogArtwork } from '../services/catalogApi'
import { ArtworkCard } from './ArtworkCard'

interface CatalogGalleryProps { artworks: CatalogArtwork[]; total: number; onSelect(publicId: string): void }
type SortOption = 'featured' | 'title' | 'creator'

export function CatalogGallery({ artworks, total, onSelect }: CatalogGalleryProps) {
  const [query, setQuery] = useState('')
  const [department, setDepartment] = useState('')
  const [culture, setCulture] = useState('')
  const [sort, setSort] = useState<SortOption>('featured')
  const departments = useMemo(() => uniqueFacts(artworks, 'department'), [artworks])
  const cultures = useMemo(() => uniqueFacts(artworks, 'culture'), [artworks])
  const visibleArtworks = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase()
    const matches = artworks.filter((artwork) => {
      const text = `${artwork.title} ${artwork.creator_display ?? ''}`.toLocaleLowerCase()
      return (!needle || text.includes(needle))
        && (!department || artwork.department === department)
        && (!culture || artwork.culture === culture)
    })
    if (sort === 'title') return [...matches].sort((a, b) => a.title.localeCompare(b.title))
    if (sort === 'creator') return [...matches].sort((a, b) => (a.creator_display ?? 'Unknown').localeCompare(b.creator_display ?? 'Unknown'))
    return matches
  }, [artworks, culture, department, query, sort])
  const hasFilters = Boolean(query || department || culture || sort !== 'featured')
  const reset = () => { setQuery(''); setDepartment(''); setCulture(''); setSort('featured') }

  return <main className="discovery-shell">
    <header className="aion-header">
      <a className="aion-logo" href="/" aria-label="AI Aion home"><span>A</span><strong>AI Aion</strong></a>
      <div className="header-proof"><span className="proof-pulse" aria-hidden="true" />Rights policy active</div>
    </header>
    <section className="discovery-hero" aria-labelledby="catalog-title">
      <div className="hero-orbit" aria-hidden="true"><span>CC0</span><span>50</span><span>01</span></div>
      <div className="hero-copy"><p className="signal-label">Provenance-led art discovery</p><h1 id="catalog-title">Trace what<br /><em>moves you.</em></h1><p>Discover open-access artworks through facts you can follow. Every image arrives with a visible trail back to its source and reuse evidence.</p></div>
      <aside className="proof-ledger" aria-label="Catalog evidence summary">
        <p className="ledger-label">Live collection proof</p><div><strong>{total.toString().padStart(2, '0')}</strong><span>verified works</span></div>
        <dl><div><dt>Rights gate</dt><dd>Explicit CC0</dd></div><div><dt>Image handling</dt><dd>Source-linked</dd></div><div><dt>Provider trail</dt><dd>Visible</dd></div></dl>
      </aside>
    </section>
    <section className="discovery-controls" aria-labelledby="explore-title">
      <div className="controls-heading"><div><p className="signal-label">Explore the evidence map</p><h2 id="explore-title">Find a point of entry</h2></div><p className="result-count" aria-live="polite">Showing <strong>{visibleArtworks.length}</strong> of {total}</p></div>
      <div className="control-grid">
        <label className="search-control"><span>Search title or creator</span><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try Monet or landscape" /></label>
        <label><span>Department</span><select value={department} onChange={(event) => setDepartment(event.target.value)}><option value="">All departments</option>{departments.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label><span>Culture</span><select value={culture} onChange={(event) => setCulture(event.target.value)}><option value="">All cultures</option>{cultures.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label><span>Order</span><select value={sort} onChange={(event) => setSort(event.target.value as SortOption)}><option value="featured">Curated import order</option><option value="title">Title A–Z</option><option value="creator">Creator A–Z</option></select></label>
      </div>
      {hasFilters && <button className="reset-button" type="button" onClick={reset}>Reset discovery view <span aria-hidden="true">×</span></button>}
    </section>
    {visibleArtworks.length ? <section className="evidence-grid" aria-label="Approved CC0 artworks">{visibleArtworks.map((artwork, index) => <ArtworkCard key={artwork.public_id} artwork={artwork} index={index} onSelect={onSelect} />)}</section> : <section className="no-results" role="status"><span aria-hidden="true">∅</span><h2>No matching trail yet.</h2><p>Try a broader title, creator, department, or culture.</p><button className="primary-button" type="button" onClick={reset}>Clear all filters</button></section>}
    <footer className="aion-footer"><span>AI Aion / Open heritage with a visible trail</span><span>{total} records · explicit CC0 only</span></footer>
  </main>
}

function uniqueFacts(artworks: CatalogArtwork[], field: 'department' | 'culture'): string[] {
  return [...new Set(artworks.map((artwork) => artwork[field]).filter((value): value is string => Boolean(value)))].sort()
}
