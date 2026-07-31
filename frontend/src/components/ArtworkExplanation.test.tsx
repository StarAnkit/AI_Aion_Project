import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ArtworkExplanation as Result, ExplanationApi } from '../services/explanationApi'
import { ArtworkExplanation } from './ArtworkExplanation'

const result: Result = {
  status: 'ready', ai_generated: true,
  content_notice: 'AI-generated explanation.',
  rights_notice: 'CC0 applies to the image, not this prose.',
  verified_museum_facts: [{ label: 'Title', value: 'Approved work' }],
  generated: { summary: 'A grounded summary.', visual_observations: ['Blue forms are visible.'], inferences: ['The arrangement may feel balanced.'], uncertainty: 'The subject identity is not verified.', insufficient_context: false },
  provenance: { provider_name: 'Cleveland Museum of Art', source_url: 'https://www.clevelandart.org/art/123', license: { status: 'CC0', license_uri: 'https://creativecommons.org/publicdomain/zero/1.0/', evidence_url: 'https://www.clevelandart.org/open-access' } },
  message: null,
}
const api = (value: Result): ExplanationApi => ({ explainArtwork: async () => value })

describe('ArtworkExplanation', () => {
  it('shows loading then separated successful output and evidence links', async () => {
    let resolve!: (value: Result) => void
    const pending: ExplanationApi = { explainArtwork: () => new Promise((done) => { resolve = done }) }
    render(<ArtworkExplanation publicId="cleveland:123" api={pending} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explain this artwork' }))
    expect(screen.getByRole('button', { name: 'Explaining artwork…' })).toBeDisabled()
    resolve(result)
    expect(await screen.findByText('A grounded summary.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Verified museum facts' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Visual observations' })).toBeInTheDocument()
    expect(screen.getByText('AI-generated')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Exact CC0 license/ })).toHaveAttribute('href', result.provenance.license.license_uri)
  })

  it('shows not configured, insufficient context, and backend error states', async () => {
    const { rerender } = render(<ArtworkExplanation publicId="cleveland:123" api={api({ ...result, status: 'not_configured', ai_generated: false, generated: null, message: 'Disabled until configured.' })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explain this artwork' }))
    expect(await screen.findByRole('heading', { name: 'AI explanation is not configured.' })).toBeInTheDocument()
    rerender(<ArtworkExplanation key="insufficient" publicId="cleveland:123" api={api({ ...result, status: 'insufficient_context', generated: { ...result.generated!, insufficient_context: true } })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explain this artwork' }))
    expect(await screen.findByText('Insufficient verified context')).toBeInTheDocument()
    rerender(<ArtworkExplanation key="error" publicId="cleveland:123" api={{ explainArtwork: async () => { throw new Error('safe failure') } }} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explain this artwork' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Explanation unavailable.')
  })
})
