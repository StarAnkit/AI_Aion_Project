import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { CatalogApi, CatalogArtwork } from '../services/catalogApi'
import { App } from './App'

const artwork: CatalogArtwork = {
  public_id: 'cleveland:12345',
  title: 'Synthetic Open Work',
  creator_display: 'Example Artist',
  date_text: '1900',
  medium: 'Oil on canvas',
  culture: null,
  department: 'Paintings',
  image_url: 'https://images.example.test/12345.jpg',
  source_url: 'https://museum.example.test/artworks/12345',
  provider_code: 'cleveland',
  provider_name: 'Cleveland Museum of Art',
  license: {
    status: 'CC0',
    license_uri: 'https://creativecommons.org/publicdomain/zero/1.0/',
    evidence_url: 'https://museum.example.test/open-access',
  },
}

const secondArtwork: CatalogArtwork = {
  ...artwork,
  public_id: 'cleveland:67890',
  title: 'Open Landscape Study',
  creator_display: 'Another Maker',
  culture: 'American',
  department: 'Drawings',
  image_url: 'https://images.example.test/67890.jpg',
  source_url: 'https://museum.example.test/artworks/67890',
}

function catalogApi(items: CatalogArtwork[] = [artwork]): CatalogApi {
  return {
    listArtworks: async () => ({ items, limit: 20, offset: 0, total: items.length }),
    getArtwork: async () => artwork,
  }
}

describe('App', () => {
  it('renders a compliant artwork and its factual detail', async () => {
    render(<App catalogApi={catalogApi()} initialPublicId={null} />)
    expect(await screen.findByText('Synthetic Open Work')).toBeInTheDocument()
    expect(screen.getByText(/CC0 verified/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Explore Synthetic Open Work' }))

    expect(await screen.findByRole('heading', { name: 'A reusable image with a traceable source.' })).toBeInTheDocument()
    expect(screen.getByText('Oil on canvas')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /official object record/i })).toHaveAttribute('href', artwork.source_url)
    expect(screen.getByRole('link', { name: /provider rights evidence/i })).toHaveAttribute('href', artwork.license.evidence_url)
    expect(screen.getByRole('link', { name: /CC0 legal terms/i })).toHaveAttribute('href', artwork.license.license_uri)
  })

  it('searches and filters only approved factual results, then resets', async () => {
    render(<App catalogApi={catalogApi([artwork, secondArtwork])} initialPublicId={null} />)
    await screen.findByText('Synthetic Open Work')

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search title or creator' }), { target: { value: 'Another Maker' } })
    expect(screen.queryByText('Synthetic Open Work')).not.toBeInTheDocument()
    expect(screen.getByText('Open Landscape Study')).toBeInTheDocument()

    fireEvent.change(screen.getByRole('combobox', { name: 'Department' }), { target: { value: 'Paintings' } })
    expect(screen.getByRole('heading', { name: 'No matching trail yet.' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Clear all filters' }))
    expect(screen.getByText('Synthetic Open Work')).toBeInTheDocument()
    expect(screen.getByText('Open Landscape Study')).toBeInTheDocument()
  })

  it('renders the empty collection state', async () => {
    render(<App catalogApi={catalogApi([])} initialPublicId={null} />)
    expect(await screen.findByRole('heading', { name: /ready for its first work/i })).toBeInTheDocument()
  })

  it('renders a helpful API error state', async () => {
    const failingApi: CatalogApi = {
      listArtworks: async () => { throw new Error('Catalog request failed with status 503') },
      getArtwork: async () => { throw new Error('Catalog request failed with status 503') },
    }
    render(<App catalogApi={failingApi} initialPublicId={null} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('The collection could not be reached.')
  })
})
