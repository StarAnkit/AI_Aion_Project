import type { CatalogLicense } from './catalogApi'
export interface MuseumFact { label: string; value: string }
export interface GeneratedExplanation { summary: string; visual_observations: string[]; inferences: string[]; uncertainty: string; insufficient_context: boolean }
export interface ArtworkExplanation { status: 'ready' | 'insufficient_context' | 'not_configured'; ai_generated: boolean; content_notice: string; rights_notice: string; verified_museum_facts: MuseumFact[]; generated: GeneratedExplanation | null; provenance: { provider_name: string; source_url: string; license: CatalogLicense }; message: string | null }
export interface ExplanationApi { explainArtwork(publicId: string): Promise<ArtworkExplanation> }
const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
export function createHttpExplanationApi(baseUrl = defaultApiBaseUrl): ExplanationApi { return { async explainArtwork(publicId) { const response = await fetch(`${baseUrl}/catalog/artworks/${encodeURIComponent(publicId)}/explanation`, { method: 'POST', headers: { Accept: 'application/json' } }); if (!response.ok) throw new Error(`Explanation request failed with status ${response.status}`); return (await response.json()) as ArtworkExplanation } } }
