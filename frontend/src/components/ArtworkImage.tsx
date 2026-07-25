import { useState } from 'react'

interface ArtworkImageProps {
  src: string
  alt: string
  className?: string
}

export function ArtworkImage({ src, alt, className }: ArtworkImageProps) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return <div className={`image-fallback ${className ?? ''}`} role="img" aria-label={`${alt} image unavailable`}>Image unavailable</div>
  }

  return <img className={className} src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />
}
