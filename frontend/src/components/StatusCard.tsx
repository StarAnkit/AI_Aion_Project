import type { HealthStatus } from '../services/healthApi'

export interface StatusCardProps { health: HealthStatus | null; error: string | null }
export function StatusCard({ health, error }: StatusCardProps) {
  const label = error ?? (health ? `Backend status: ${health.status}` : 'Checking the backend…')
  const state = error ? 'offline' : health ? 'online' : 'pending'
  return <div className="status-card" data-state={state} role="status" aria-live="polite"><span className="status-dot" aria-hidden="true" /><span>{label}</span></div>
}
