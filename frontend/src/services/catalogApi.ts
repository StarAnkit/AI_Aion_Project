export interface CatalogLicense {
  status: 'CC0'
  license_uri: string
  evidence_url: string
}

export interface CatalogArtwork {
  public_id: string
  title: string
  creator_display: string | null
  date_text: string | null
  medium: string | null
  culture: string | null
  department: string | null
  image_url: string
  source_url: string
  provider_code: string
  provider_name: string
  license: CatalogLicense
}

export interface CatalogPage {
  items: CatalogArtwork[]
  limit: number
  offset: number
  total: number
}

export interface CatalogApi {
  listArtworks(options?: { limit?: number; offset?: number }): Promise<CatalogPage>
  getArtwork(publicId: string): Promise<CatalogArtwork>
}

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export function createHttpCatalogApi(baseUrl = defaultApiBaseUrl): CatalogApi {
  return {
    async listArtworks({ limit = 20, offset = 0 } = {}) {
      const parameters = new URLSearchParams({ limit: String(limit), offset: String(offset) })
      return requestCatalog<CatalogPage>(`${baseUrl}/catalog/artworks?${parameters}`)
    },
    async getArtwork(publicId) {
      return requestCatalog<CatalogArtwork>(
        `${baseUrl}/catalog/artworks/${encodeURIComponent(publicId)}`,
      )
    },
  }
}

async function requestCatalog<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    throw new Error(`Catalog request failed with status ${response.status}`)
  }
  return (await response.json()) as T
}
