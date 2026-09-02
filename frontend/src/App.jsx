import { useEffect, useState } from 'react'
import { getHealth } from './api'
import './styles.css'

export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch((requestError) => setError(requestError.message))
  }, [])

  return (
    <main className="app-shell">
      <section className="status-panel" aria-labelledby="page-title">
        <p className="eyebrow">StandIQ / foundation</p>
        <h1 id="page-title">Right standards.<br />Right tenders.</h1>
        <p className="lede">The intelligence workspace is taking shape.</p>
        <div className={`status ${health ? 'status-ready' : error ? 'status-error' : 'status-loading'}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {health ? `API ${health.status}` : error ? 'API unavailable' : 'Connecting to API'}
        </div>
        {health && <p className="detail">{health.service} · {health.version}</p>}
        {error && <p className="detail">{error}</p>}
      </section>
    </main>
  )
}
