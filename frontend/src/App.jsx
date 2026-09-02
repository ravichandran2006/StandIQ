import { useEffect, useState } from 'react'
import { recommendationDemo } from './demoData'
import { DocumentAnalysis, Explanation, ComplianceCard, HistoryPage, MappingCard, MissingInformation, RecommendationHeader, RelatedStandards, RequirementCard, SearchPage, Sidebar, SimplePage, StandardsTable, SummaryMetrics, TenderOutput, TopNavigation, Traceability, UploadPage, VersionCard } from './components'
import './styles.css'

const HISTORY_KEY = 'standiq-search-history'

export default function App() {
  const [active, setActive] = useState('Dashboard')
  const [toast, setToast] = useState('')
  const [dialog, setDialog] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] }
  })
  const data = recommendationDemo

  useEffect(() => { window.localStorage.setItem(HISTORY_KEY, JSON.stringify(history)) }, [history])

  const notify = (message) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2600)
  }
  const action = (message) => () => notify(message)
  const navigate = (page) => setActive(page)
  const downloadReport = () => {
    const lines = ['StandIQ - Recommendation Report', '', `Requirement: ${data.requirement.text}`, `Language: ${data.requirement.language}`, '', 'Recommended Standards:', ...data.standards.map((item) => `${item.rank}. ${item.number} - ${item.title} (${item.score}%)`), '', 'Disclaimer: Demo UI data. Verify against current official BIS documents and notifications.']
    const stream = lines.map((line) => `BT /F1 10 Tf 50 ${760 - lines.indexOf(line) * 18} Td (${line.replace(/[()]/g, '')}) Tj`).join(' ')
    const pdf = `%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n5 0 obj<</Length ${stream.length + 1}>>stream\n${stream}\nendstream endobj\ntrailer<</Root 1 0 R>>\n%%EOF`
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([pdf], { type: 'application/pdf' }))
    link.download = 'standiq-recommendation-report.pdf'
    link.click()
    URL.revokeObjectURL(link.href)
    notify('Recommendation report downloaded')
  }
  const startSearch = (query) => {
    const text = query.trim()
    if (!text) return
    setHistory((items) => [{ id: Date.now(), text, source: 'Text input', createdAt: new Date().toLocaleString() }, ...items].slice(0, 20))
    setActive('Dashboard')
    notify('Demo recommendation prepared')
  }
  const handleFile = (file) => {
    if (file && file.size > 20 * 1024 * 1024) { notify('File exceeds the 20 MB limit'); return }
    setSelectedFile(file)
  }
  const analyzeFile = () => {
    if (!selectedFile) return
    setHistory((items) => [{ id: Date.now(), text: selectedFile.name, source: 'Uploaded document', createdAt: new Date().toLocaleString() }, ...items].slice(0, 20))
    setActive('Dashboard')
    notify('Demo document analysis prepared')
  }

  const renderPage = () => {
    if (active === 'Search Standards') return <SearchPage onSearch={startSearch} />
    if (active === 'Upload Document') return <UploadPage selectedFile={selectedFile} onFile={handleFile} onAnalyze={analyzeFile} />
    if (active === 'History') return <HistoryPage history={history} onOpen={() => { setActive('Dashboard'); notify('Previous result reopened') }} />
    if (active === 'Saved Results') return <SimplePage title="Saved Results" description="Your bookmarked recommendation results will appear here." />
    if (active === 'Alerts') return <SimplePage title="Alerts" description="Monitor changes to standards and compliance evidence." />
    if (active === 'Settings') return <SimplePage title="Settings" description="Manage your workspace preferences and notification settings." />
    if (active === 'Help & Guide') return <SimplePage title="Help & Guide" description="Learn how StandIQ organizes standards evidence for procurement." />
    if (active === 'Logout') return <SimplePage title="Signed out" description="Your demo session is ready to close." actionLabel="Return to Dashboard" onAction={() => setActive('Dashboard')} />
    return <Dashboard data={data} onDownload={downloadReport} onGenerate={action('Tender specification draft queued')} onNewSearch={() => setActive('Search Standards')} onUpload={() => setActive('Upload Document')} onDialog={setDialog} action={action} />
  }

  return <div className="app-frame">
    <TopNavigation onNavigate={navigate} onProfile={() => setActive('Profile')} />
    <div className="workspace">
      <Sidebar active={active} onSelect={navigate} />
      <main className="main-content">{active === 'Profile' ? <SimplePage title="Profile" description="Signed in as AR · Procurement Intelligence Team" /> : renderPage()}</main>
    </div>
    {toast && <div className="toast" role="status">✓ {toast}</div>}
    {dialog && <div className="modal-backdrop" onClick={() => setDialog(null)}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setDialog(null)} aria-label="Close">×</button><h2 id="dialog-title">{dialog.title}</h2><p>{dialog.body}</p><button className="button primary" onClick={() => setDialog(null)}>Close</button></div></div>}
  </div>
}

function Dashboard({ data, onDownload, onGenerate, onNewSearch, onUpload, onDialog, action }) {
  return <><RecommendationHeader onNewSearch={onNewSearch} onDownload={onDownload} onGenerate={onGenerate} /><RequirementCard requirement={data.requirement} /><SummaryMetrics metrics={data.metrics} /><StandardsTable standards={data.standards} onEvidence={(standard) => onDialog({ title: `Evidence for ${standard.number}`, body: `Demo evidence panel for “${standard.title}”. Authoritative evidence will be connected in a later phase.` })} onViewAll={action('Showing all recommended standards')} /><div className="two-column"><Explanation factors={data.matchFactors} onDetails={action('Explanation details opened')} /><RelatedStandards related={data.related} onViewAll={action('Showing all related standards')} /></div><div className="three-column"><VersionCard version={data.version} onHistory={action('Version history opened')} /><ComplianceCard compliance={data.compliance} onDetails={action('Compliance details opened')} /><MappingCard mapping={data.mapping} onViewAll={action('Full mapping opened')} /></div><div className="three-column bottom-grid"><MissingInformation missing={data.missing} onRefine={action('Requirement refinement opened')} /><TenderOutput onGenerate={onGenerate} onDownload={onDownload} /><Traceability traceability={data.traceability} onSources={action('Source documents opened')} onEvidence={action('Evidence register opened')} /></div><DocumentAnalysis document={data.document} onUpload={onUpload} /><footer><span>◆</span> StandIQ provides AI-powered recommendations. Verify official compliance with the latest BIS documents and notifications before final procurement decisions.</footer></>
}
