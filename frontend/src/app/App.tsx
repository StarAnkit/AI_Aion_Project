import { useEffect, useState } from 'react'
import { ArtworkDetail } from '../components/ArtworkDetail'
import { CatalogGallery } from '../components/CatalogGallery'
import { CatalogState } from '../components/CatalogState'
import { createHttpCatalogApi, type CatalogApi, type CatalogArtwork, type CatalogPage } from '../services/catalogApi'
import type { ExplanationApi } from '../services/explanationApi'

const defaultCatalogApi = createHttpCatalogApi()

export interface AppProps {
  catalogApi?: CatalogApi
  initialPublicId?: string | null
  explanationApi?: ExplanationApi
}

type ViewState =
  | { kind: 'loading' }
  | { kind: 'error' }
  | { kind: 'not-found' }
  | { kind: 'gallery'; page: CatalogPage }
  | { kind: 'detail'; artwork: CatalogArtwork }

export function App({ catalogApi = defaultCatalogApi, initialPublicId, explanationApi }: AppProps) {
  const [publicId, setPublicId] = useState<string | null>(() =>
    initialPublicId !== undefined ? initialPublicId : readPublicId(),
  )
  const [view, setView] = useState<ViewState>({ kind: 'loading' })

  useEffect(() => {
    if (initialPublicId !== undefined) return
    const onHistoryChange = () => {
      setView({ kind: 'loading' })
      setPublicId(readPublicId())
    }
    window.addEventListener('popstate', onHistoryChange)
    return () => window.removeEventListener('popstate', onHistoryChange)
  }, [initialPublicId])

  useEffect(() => {
    let current = true
    const request = publicId
      ? catalogApi.getArtwork(publicId)
      : catalogApi.listArtworks({ limit: 50 })
    request
      .then((result) => {
        if (!current) return
        if ('items' in result) setView({ kind: 'gallery', page: result })
        else setView({ kind: 'detail', artwork: result })
      })
      .catch((error: unknown) => {
        if (!current) return
        const isNotFound = error instanceof Error && error.message.includes('status 404')
        setView({ kind: isNotFound ? 'not-found' : 'error' })
      })
    return () => { current = false }
  }, [catalogApi, publicId])

  const navigate = (nextPublicId: string | null) => {
    const url = new URL(window.location.href)
    if (nextPublicId) url.searchParams.set('artwork', nextPublicId)
    else url.searchParams.delete('artwork')
    window.history.pushState({}, '', url)
    setView({ kind: 'loading' })
    setPublicId(nextPublicId)
  }

  if (view.kind === 'loading') return <CatalogState kind="loading" />
  if (view.kind === 'error') return <CatalogState kind="error" />
  if (view.kind === 'not-found') return <CatalogState kind="not-found" onBack={() => navigate(null)} />
  if (view.kind === 'detail') return <ArtworkDetail artwork={view.artwork} onBack={() => navigate(null)} explanationApi={explanationApi} />
  if (!view.page.items.length) return <CatalogState kind="empty" />
  return <CatalogGallery artworks={view.page.items} total={view.page.total} onSelect={navigate} />
}

function readPublicId(): string | null {
  return new URLSearchParams(window.location.search).get('artwork')
}
