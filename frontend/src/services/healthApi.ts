export interface HealthStatus { status: string; service: string }
export interface HealthApi { getHealth(): Promise<HealthStatus> }
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export function createHttpHealthApi(baseUrl = apiBaseUrl): HealthApi {
  return { async getHealth() {
    const response = await fetch(`${baseUrl}/health`)
    if (!response.ok) throw new Error(`Health request failed with status ${response.status}`)
    return (await response.json()) as HealthStatus
  } }
}
