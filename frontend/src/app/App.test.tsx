import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from './App'

describe('App', () => {
  it('renders health from an injected API', async () => {
    render(<App healthApi={{ getHealth: async () => ({ status: 'ok', service: 'ai-aion-api' }) }} />)
    expect(screen.getByRole('heading', { name: /clean foundation/i })).toBeInTheDocument()
    expect(await screen.findByText('Backend status: ok')).toBeInTheDocument()
  })
})
