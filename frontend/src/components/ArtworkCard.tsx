import type { CatalogArtwork } from '../services/catalogApi'
import { ArtworkImage } from './ArtworkImage'
interface ArtworkCardProps { artwork: CatalogArtwork; index: number; onSelect(publicId: string): void }
export function ArtworkCard({ artwork, index, onSelect }: ArtworkCardProps) {
  const creatorLine = [artwork.creator_display, artwork.date_text].filter(Boolean).join(' · ')
  return <article className={`evidence-card evidence-card-${index % 7}`}><button className="evidence-card-link" type="button" onClick={() => onSelect(artwork.public_id)} aria-label={`Explore ${artwork.title}`}><span className="card-visual"><ArtworkImage className="evidence-card-image" src={artwork.image_url} alt={artwork.title} /><span className="card-index" aria-hidden="true">{(index + 1).toString().padStart(2, '0')}</span><span className="card-action" aria-hidden="true">Open trail ↗</span></span><span className="evidence-card-copy"><span className="card-proof"><i aria-hidden="true" />CC0 verified · {artwork.provider_name}</span><strong>{artwork.title}</strong>{creatorLine && <span className="card-facts">{creatorLine}</span>}</span></button></article>
}
