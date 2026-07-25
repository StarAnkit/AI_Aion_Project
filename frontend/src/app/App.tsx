import { useEffect, useState } from 'react'
import { StatusCard } from '../components/StatusCard'
import { createHttpHealthApi, type HealthApi, type HealthStatus } from '../services/healthApi'

const defaultHealthApi = createHttpHealthApi()
export interface AppProps { healthApi?: HealthApi }

export function App({ healthApi = defaultHealthApi }: AppProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let current = true
    healthApi.getHealth().then((result) => current && setHealth(result)).catch(() => current && setError('The backend is not reachable yet.'))
    return () => { current = false }
  }, [healthApi])

  return <main className="shell"><section className="hero" aria-labelledby="page-title">
    <p className="eyebrow">AI Aion Project</p><h1 id="page-title">A clean foundation for what comes next.</h1>
    <p className="intro">The React interface and FastAPI service are separated, typed, and ready to grow. Data and AI decisions remain intentionally open.</p>
    <StatusCard health={health} error={error} />
  </section></main>
}
