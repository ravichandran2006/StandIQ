import { useState } from 'react'
import { recommendationDemo } from './demoData'
import { DocumentAnalysis, Explanation, ComplianceCard, MappingCard, MissingInformation, RecommendationHeader, RelatedStandards, RequirementCard, Sidebar, StandardsTable, SummaryMetrics, TenderOutput, TopNavigation, Traceability, VersionCard } from './components'
import './styles.css'

export default function App() {
  const [active, setActive] = useState('Dashboard')
  const [toast, setToast] = useState('')
  const [dialog, setDialog] = useState(null)
  const data = recommendationDemo

  const notify = (message) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2600)
  }
  const action = (message) => () => notify(message)

  return <div className="app-frame">
    <TopNavigation />
    <div className="workspace">
      <Sidebar active={active} onSelect={(item) => { setActive(item); notify(`${item} view selected`) }} />
      <main className="main-content">
        <RecommendationHeader onNewSearch={action('New search workspace ready')} onDownload={action('Demo report download queued')} onGenerate={action('Tender specification draft queued')} />
        <RequirementCard requirement={data.requirement} />
        <SummaryMetrics metrics={data.metrics} />
        <StandardsTable standards={data.standards} onEvidence={(standard) => setDialog({ title: `Evidence for ${standard.number}`, body: `Demo evidence panel for “${standard.title}”. Authoritative evidence will be connected in a later phase.` })} onViewAll={action('Showing all recommended standards')} />
        <div className="two-column"><Explanation factors={data.matchFactors} onDetails={action('Explanation details opened')} /><RelatedStandards related={data.related} onViewAll={action('Showing all related standards')} /></div>
        <div className="three-column"><VersionCard version={data.version} onHistory={action('Version history opened')} /><ComplianceCard compliance={data.compliance} onDetails={action('Compliance details opened')} /><MappingCard mapping={data.mapping} onViewAll={action('Full mapping opened')} /></div>
        <div className="three-column bottom-grid"><MissingInformation missing={data.missing} onRefine={action('Requirement refinement opened')} /><TenderOutput onGenerate={action('Tender specification draft queued')} onDownload={action('Demo report download queued')} /><Traceability traceability={data.traceability} onSources={action('Source documents opened')} onEvidence={action('Evidence register opened')} /></div>
        <DocumentAnalysis document={data.document} onUpload={action('Document upload opened')} />
        <footer><span>◆</span> StandIQ provides AI-powered recommendations. Verify official compliance with the latest BIS documents and notifications before final procurement decisions.</footer>
      </main>
    </div>
    {toast && <div className="toast" role="status">✓ {toast}</div>}
    {dialog && <div className="modal-backdrop" onClick={() => setDialog(null)}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setDialog(null)} aria-label="Close">×</button><h2 id="dialog-title">{dialog.title}</h2><p>{dialog.body}</p><button className="button primary" onClick={() => setDialog(null)}>Close</button></div></div>}
  </div>
}
