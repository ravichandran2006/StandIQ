import { useEffect, useState } from 'react'
import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import { recommendationDemo } from './demoData'
import {
  analyzeRequirement,
  fetchAllEvidence,
  fetchComplianceDetails,
  fetchExplanation,
  fetchRelatedStandards,
  fetchRequirementMapping,
  fetchSourceDocuments,
  fetchTenderSpecification,
  fetchVersionHistory,
  languageLabel,
  refineRequirement,
  uploadDocument,
} from './api'
import {
  ActionModal,
  ComplianceCard,
  DocumentAnalysis,
  Explanation,
  HistoryPage,
  MappingCard,
  MissingInformation,
  RecommendationHeader,
  RelatedStandards,
  RequirementCard,
  SavedResultsPage,
  SearchPage,
  Sidebar,
  SimplePage,
  StandardsTable,
  SummaryMetrics,
  TenderOutput,
  TopNavigation,
  Traceability,
  UploadPage,
  VersionCard,
} from './components'
import './styles.css'
import './theme.css'

const HISTORY_KEY = 'standiq-search-history'
const SAVED_KEY = 'standiq-saved-results'
const THEME_KEY = 'standiq-theme'

export default function App() {
  const [active, setActive] = useState('Dashboard')
  const [toast, setToast] = useState('')
  const [dialog, setDialog] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [rawResult, setRawResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] }
  })
  const [savedResults, setSavedResults] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem(SAVED_KEY) || '[]') } catch { return [] }
  })
  const [theme, setTheme] = useState(() => {
    const stored = window.localStorage.getItem(THEME_KEY)
    if (stored === 'dark' || stored === 'light') return stored
    return window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ? 'dark' : 'light'
  })
  const data = recommendation || (import.meta.env.VITE_DEMO_MODE === 'true' ? recommendationDemo : null)

  useEffect(() => { window.localStorage.setItem(HISTORY_KEY, JSON.stringify(history)) }, [history])
  useEffect(() => { window.localStorage.setItem(SAVED_KEY, JSON.stringify(savedResults)) }, [savedResults])
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  const toggleTheme = () => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  const currentSavedId = rawResult?.requirement?.original_text
  const isSaved = Boolean(currentSavedId) && savedResults.some((item) => item.id === currentSavedId)

  const notify = (message) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2600)
  }
  const navigate = (page) => setActive(page)

  const applyRecommendation = (result) => {
    setRawResult(result)
    setRecommendation(toDashboardData(result))
  }

  const primaryStandard = () => rawResult?.standards?.[0] || null

  const openDialog = (dialogState) => setDialog(dialogState)
  const closeDialog = () => setDialog(null)

  const runAction = async (title, task) => {
    setActionLoading(true)
    openDialog({ title, loading: true, body: 'Loading…' })
    try {
      const result = await task()
      openDialog({ title, loading: false, ...result })
    } catch (error) {
      openDialog({ title, loading: false, error: error.message })
    } finally {
      setActionLoading(false)
    }
  }

  const downloadReport = () => {
    if (!rawResult?.requirement) {
      notify('Run an analysis before downloading a report')
      return
    }
    generateReportPdf(rawResult).save('standiq-recommendation-report.pdf')
    notify('Recommendation report downloaded as PDF')
  }

  const startSearch = async (query) => {
    const text = query.trim()
    if (!text) return
    setLoading(true)
    try {
      applyRecommendation(await analyzeRequirement(text))
    } catch (error) {
      notify(error.message)
      return
    } finally {
      setLoading(false)
    }
    setHistory((items) => [{ id: Date.now(), text, source: 'Text input', createdAt: new Date().toLocaleString() }, ...items].slice(0, 20))
    setActive('Dashboard')
    notify('Recommendation analysis completed')
  }

  const handleRefine = async (refinement) => {
    if (!rawResult?.requirement?.original_text || !refinement.trim()) {
      notify('Enter additional requirement details to refine')
      return
    }
    setLoading(true)
    closeDialog()
    try {
      applyRecommendation(await refineRequirement(rawResult.requirement.original_text, refinement.trim()))
      notify('Recommendation updated with refined requirement')
    } catch (error) {
      notify(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExplanation = () => {
    const standard = primaryStandard()
    if (!standard || !rawResult) {
      notify('Run an analysis before opening AI explanation')
      return
    }
    runAction('AI Explanation', async () => {
      const response = await fetchExplanation(rawResult.requirement.original_text, standard.standard_id)
      return {
        status: response.status,
        body: response.explanation,
        note: response.message,
      }
    })
  }

  const handleRelated = () => {
    const standard = primaryStandard()
    if (!standard) {
      notify('No standard selected for related standards')
      return
    }
    runAction('Related / Normative Standards', async () => {
      const response = await fetchRelatedStandards(standard.standard_id)
      return { status: response.status, table: response.items, note: response.message }
    })
  }

  const handleVersionHistory = () => {
    const standard = primaryStandard()
    if (!standard) return notify('No standard available for version history')
    runAction('Version History', async () => {
      const response = await fetchVersionHistory(standard.standard_id)
      return { status: response.status, table: response.items, note: response.message }
    })
  }

  const handleCompliance = () => {
    const standard = primaryStandard()
    if (!standard) return notify('No standard available for compliance details')
    runAction('Certification & Compliance', async () => {
      const response = await fetchComplianceDetails(standard.standard_id)
      return { status: response.status, compliance: response.items, note: response.message }
    })
  }

  const handleMapping = () => {
    const standard = primaryStandard()
    if (!standard || !rawResult) return notify('No mapping available')
    runAction('Requirement → Standard Mapping', async () => {
      const response = await fetchRequirementMapping(standard.standard_id, rawResult.requirement.original_text)
      return { status: response.status, mapping: response.items, note: response.message }
    })
  }

  const handleTender = () => {
    if (!rawResult) return notify('Run an analysis before generating tender specification')
    runAction('Tender Specification', async () => {
      const response = await fetchTenderSpecification(rawResult.requirement.original_text)
      return { status: response.status, body: response.specification, note: response.disclaimer }
    })
  }

  const handleSources = () => {
    const standard = primaryStandard()
    if (!standard) return notify('No source documents available')
    runAction('Source Documents', async () => {
      const response = await fetchSourceDocuments(standard.standard_id)
      return { status: response.status, table: response.items, note: response.message }
    })
  }

  const handleEvidence = () => {
    const standard = primaryStandard()
    if (!standard || !rawResult) return notify('No evidence available')
    runAction('All Evidence', async () => {
      const response = await fetchAllEvidence(standard.standard_id, rawResult.requirement.original_text)
      return { status: response.status, table: response.items, note: response.message }
    })
  }

  const handleFile = (file) => {
    if (file && file.size > 20 * 1024 * 1024) { notify('File exceeds the 20 MB limit'); return }
    setSelectedFile(file)
  }
  const analyzeFile = async () => {
    if (!selectedFile) return
    setLoading(true)
    try {
      const result = await uploadDocument(selectedFile)
      applyRecommendation(result)
      setHistory((items) => [
        {
          id: Date.now(),
          text: selectedFile.name,
          source: 'Uploaded document',
          createdAt: new Date().toLocaleString(),
        },
        ...items,
      ].slice(0, 20))
      setActive('Dashboard')
      notify('Document upload analysis completed')
    } catch (error) {
      notify(error.message)
    } finally {
      setLoading(false)
    }
  }
  const deleteHistory = (id) => {
    setHistory((items) => items.filter((item) => item.id !== id))
    notify('History item deleted')
  }

  const handleSave = () => {
    if (!rawResult) {
      notify('Run an analysis before saving a result')
      return
    }
    const id = rawResult.requirement.original_text
    if (savedResults.some((item) => item.id === id)) {
      setSavedResults((items) => items.filter((item) => item.id !== id))
      notify('Result removed from Saved Results')
    } else {
      setSavedResults((items) => [
        {
          id,
          text: rawResult.requirement.original_text,
          source: 'Bookmarked result',
          createdAt: new Date().toLocaleString(),
          data: recommendation,
          raw: rawResult,
        },
        ...items,
      ].slice(0, 50))
      notify('Result saved to Saved Results')
    }
  }

  const openSaved = (item) => {
    setRawResult(item.raw)
    setRecommendation(item.data)
    setActive('Dashboard')
    notify('Saved result opened')
  }

  const removeSaved = (id) => {
    setSavedResults((items) => items.filter((item) => item.id !== id))
    notify('Saved result removed')
  }

  const renderPage = () => {
    if (active === 'Search Standards') return <SearchPage onSearch={startSearch} loading={loading} />
    if (active === 'Upload Document') return <UploadPage selectedFile={selectedFile} onFile={handleFile} onAnalyze={analyzeFile} loading={loading} />
    if (active === 'History') return <HistoryPage history={history} onOpen={(item) => startSearch(item.text)} onDelete={deleteHistory} />
    if (active === 'Saved Results') return <SavedResultsPage saved={savedResults} onOpen={openSaved} onRemove={removeSaved} />
    if (active === 'Alerts') return <SimplePage title="Alerts" description="Monitor changes to standards and compliance evidence." />
    if (active === 'Settings') return <SimplePage title="Settings" description="Manage your workspace preferences and notification settings." />
    if (active === 'Help & Guide') return <SimplePage title="Help & Guide" description="Learn how StandIQ organizes standards evidence for procurement." />
    if (active === 'Logout') return <SimplePage title="Signed out" description="Your demo session is ready to close." actionLabel="Return to Dashboard" onAction={() => setActive('Dashboard')} />
    if (!data) return <SimplePage title={loading ? 'Analyzing requirement' : 'Start a standards analysis'} description={loading ? 'The backend is evaluating stored standards evidence.' : 'Search by procurement requirement to load an evidence-aware recommendation.'} actionLabel={loading ? undefined : 'New Search'} onAction={() => setActive('Search Standards')} />
    return (
      <Dashboard
        data={data}
        onDownload={downloadReport}
        onGenerate={handleTender}
        onNewSearch={() => setActive('Search Standards')}
        onUpload={() => setActive('Upload Document')}
        onSave={handleSave}
        isSaved={isSaved}
        onExplanation={handleExplanation}
        onRelated={handleRelated}
        onVersionHistory={handleVersionHistory}
        onCompliance={handleCompliance}
        onMapping={handleMapping}
        onRefine={() => openDialog({ title: 'Refine Requirement', refine: true, originalText: rawResult?.requirement?.original_text || data.requirement.text })}
        onSources={handleSources}
        onEvidence={handleEvidence}
        onStandardEvidence={(standard) => {
          const match = rawResult?.standards?.find((item) => item.is_number === standard.number)
          if (!match) {
            openDialog({ title: `Evidence for ${standard.number}`, body: 'Evidence is available after a live backend recommendation.' })
            return
          }
          runAction(`Evidence for ${standard.number}`, async () => {
            const response = await fetchAllEvidence(match.standard_id, rawResult.requirement.original_text)
            return { status: response.status, table: response.items, note: response.message }
          })
        }}
      />
    )
  }

  return <div className="app-frame">
    <TopNavigation onNavigate={navigate} onProfile={() => setActive('Profile')} theme={theme} onToggleTheme={toggleTheme} />
    <div className="workspace">
      <Sidebar active={active} onSelect={navigate} />
      <main className="main-content">{active === 'Profile' ? <SimplePage title="Profile" description="Signed in as AR · Procurement Intelligence Team" /> : renderPage()}</main>
    </div>
    {toast && <div className="toast" role="status">✓ {toast}</div>}
    {dialog && <ActionModal dialog={dialog} loading={actionLoading} onClose={closeDialog} onRefine={handleRefine} />}
  </div>
}

function toDashboardData(result) {
  const standards = result.standards || []
  const first = standards[0]
  const related = standards.reduce((groups, standard) => {
    ;(standard.relationships || []).forEach((item) => {
      const row = {
        standard: item.is_number,
        title: item.title,
        relationship: item.relationship_type,
        whyRelevant: item.evidence_note || 'Recorded in authoritative metadata',
        status: item.status || 'unknown',
      }
      if (['NORMATIVE', 'REFERRED', 'TEST_METHOD'].includes(item.relationship_type)) groups.normative.push(row)
      else groups.allied.push(row)
    })
    return groups
  }, { normative: [], allied: [] })
  const mapping = (first?.mapping || []).map((row) => [row.requirement_element, row.supporting_evidence, row.match === 'matched' ? 'Matched' : row.match === 'partially matched' ? 'Partial' : row.match === 'ambiguous' ? 'Ambiguous' : 'Missing'])
  const complianceItems = first?.compliance || []
  const compliance = [
    { label: 'BIS Product Certification', status: complianceItems.some((item) => item.type === 'QCO') ? 'Recorded' : 'Unavailable', tone: complianceItems.some((item) => item.type === 'QCO') ? 'green' : 'slate' },
    { label: 'QCO (Quality Control Order)', status: complianceItems.some((item) => item.type === 'QCO') ? 'Recorded' : 'Not recorded', tone: complianceItems.some((item) => item.type === 'QCO') ? 'green' : 'slate' },
    { label: 'CRS (Compulsory Registration Scheme)', status: complianceItems.some((item) => item.type === 'CRS') ? 'Recorded' : 'Not recorded', tone: complianceItems.some((item) => item.type === 'CRS') ? 'green' : 'slate' },
    { label: 'Hallmarking', status: 'Verify in details', tone: 'warning' },
  ]
  const doc = result.document
  const documentName = doc?.filename || 'Text requirement'
  const extractedLen = doc?.extracted_text_length || result.requirement.original_text.length
  return {
    requirement: {
      text: result.requirement.original_text,
      language: result.requirement.detected_language_label || languageLabel(result.requirement.detected_language),
      source: doc ? `Uploaded document: ${doc.filename}` : 'Backend analysis',
      searchedAt: new Date().toLocaleString(),
    },
    standards: standards.map((item, index) => ({ rank: index + 1, number: item.is_number, title: item.title, score: Math.round(item.relevance_score * 100), status: item.evidence_state === 'supported' ? 'Supported' : 'Verify', type: item.standard_type || 'Standard' })),
    metrics: [
      { label: 'Standards Found', value: standards.length, note: 'Stored candidates', tone: 'blue' },
      { label: 'Strong Matches', value: standards.filter((item) => item.applicability_status === 'RELEVANT').length, note: 'Deterministic relevance', tone: 'green' },
      { label: 'Confidence', value: first ? `${Math.round(first.confidence * 100)}%` : '0%', note: first?.evidence_state === 'supported' ? 'Evidence supported' : 'Requires verification', tone: 'orange', featured: true },
    ],
    matchFactors: first?.reasons?.length ? first.reasons : ['No stored evidence matched this requirement.'],
    related,
    version: first?.version ? { current: first.version.status === 'current' ? 'Verified' : 'Unverified', superseded: 'See version history', amendments: first.version.amendments?.length || 0, latest: first.version.amendments?.[0]?.label || first.version.edition_label || 'Unavailable', date: first.version.amendments?.[0]?.publication_date || 'Unavailable' } : { current: 'Unavailable', superseded: 'Unavailable', amendments: 0, latest: 'Unavailable', date: 'Unavailable' },
    compliance,
    mapping,
    missing: result.missing_information,
    traceability: { source: first?.provenance?.source_type || 'No source record', dataStatus: first?.evidence_state === 'supported' ? 'Supported' : 'Requires verification', indexed: 'Unavailable', retrieved: first?.provenance?.retrieved_at || 'Unavailable', method: result.summary?.retrieval_method || 'Deterministic keyword retrieval' },
    document: {
      name: documentName,
      pages: doc?.page_count || 1,
      language: doc?.language_label || result.requirement.detected_language_label || languageLabel(result.requirement.detected_language),
      extracted: doc ? `${extractedLen} characters` : 1,
      extractedLength: extractedLen,
      relevant: standards.length,
    },
    explanationPreview: first?.reasons?.[0] || null,
  }
}

function generateReportPdf(result) {
  const req = result?.requirement || {}
  const standards = result?.standards || []
  const missing = result?.missing_information || []
  const summary = result?.summary || {}
  const first = standards[0] || {}
  const version = first.version || {}
  const compliance = first.compliance || []
  const provenance = first.provenance || {}

  // jsPDF standard fonts only support Latin-1; strip anything else so no garbled glyphs appear.
  const pdfSafe = (value) => String(value ?? '')
    .replace(/[—–]/g, '-')
    .replace(/[•·]/g, '-')
    .replace(/[✓✗⚠→←↑↓◆]/g, '')
    .replace(/[^\u0020-\u00FF\n]/g, '')
    .replace(/\s+/g, ' ')
    .trim()

  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 48
  const contentWidth = pageWidth - margin * 2

  // Branded header band
  doc.setFillColor(23, 101, 211)
  doc.rect(0, 0, pageWidth, 84, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(19)
  doc.text('STANDIQ', margin, 36)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.text('Standards Recommendation Report', margin, 54)
  doc.setFontSize(8)
  doc.text(`Generated: ${pdfSafe(new Date().toLocaleString())}`, pageWidth - margin, 30, { align: 'right' })
  doc.text('Right Standards. Right Tenders.', pageWidth - margin, 46, { align: 'right' })

  let y = 112

  const ensure = (needed) => {
    if (y + needed > pageHeight - 60) {
      doc.addPage()
      y = 48
    }
  }

  const sectionTitle = (title) => {
    ensure(36)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(23, 101, 211)
    doc.text(title.toUpperCase(), margin, y)
    doc.setDrawColor(23, 101, 211)
    doc.setLineWidth(1.2)
    doc.line(margin, y + 5, margin + 78, y + 5)
    y += 22
  }

  const labelValue = (label, value) => {
    ensure(24)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(9)
    doc.setTextColor(86, 103, 122)
    doc.text(label.toUpperCase(), margin, y)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(37, 50, 70)
    const wrapped = doc.splitTextToSize(pdfSafe(value) || '—', contentWidth - 150)
    doc.text(wrapped, margin + 150, y)
    y += Math.max(14, wrapped.length * 11.5 + 3)
  }

  const bulletList = (items) => {
    items.forEach((item) => {
      const wrapped = doc.splitTextToSize('-  ' + pdfSafe(item), contentWidth)
      ensure(wrapped.length * 12 + 6)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      doc.setTextColor(37, 50, 70)
      doc.text(wrapped, margin, y)
      y += wrapped.length * 12 + 4
    })
    y += 6
  }

  // 1. Requirement
  sectionTitle('Procurement Requirement')
  ensure(20)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.setTextColor(86, 103, 122)
  doc.text('REQUIREMENT', margin, y)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10.5)
  doc.setTextColor(30, 42, 60)
  const reqLines = doc.splitTextToSize(pdfSafe(req.original_text) || '—', contentWidth)
  ensure(reqLines.length * 13 + 8)
  doc.text(reqLines, margin, y + 12)
  y += reqLines.length * 13 + 22
  labelValue('Detected Language', req.detected_language_label || req.detected_language)
  labelValue('Technical Keywords', (req.technical_keywords || []).join(', '))
  labelValue('Normalized Text', req.normalized_text)
  if (result.document?.filename) labelValue('Source Document', `${result.document.filename} (${result.document.page_count || '—'} pages)`)
  y += 8

  // 2. Recommended standards table
  if (standards.length) {
    sectionTitle('Recommended Standards')
    autoTable(doc, {
      startY: y,
      margin: { left: margin, right: margin },
      head: [['#', 'IS Number', 'Standard Title', 'Score', 'Applicability', 'Type']],
      body: standards.map((standard, index) => [
        String(index + 1),
        pdfSafe(standard.is_number),
        pdfSafe(standard.title),
        `${Math.round((standard.relevance_score || 0) * 100)}%`,
        pdfSafe(standard.applicability_status || standard.evidence_state || '—'),
        pdfSafe(standard.standard_type || 'Standard'),
      ]),
      styles: { font: 'helvetica', fontSize: 8, cellPadding: 6, textColor: [37, 50, 70], lineColor: [219, 226, 236], lineWidth: 0.6 },
      headStyles: { fillColor: [23, 101, 211], textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [240, 245, 252] },
      columnStyles: {
        0: { cellWidth: 26, halign: 'center' },
        1: { cellWidth: 62 },
        3: { cellWidth: 52, halign: 'center' },
        4: { cellWidth: 88 },
      },
    })
    y = doc.lastAutoTable.finalY + 18
  }

  // 3. Why recommended (top standard)
  const reasons = first.reasons || []
  if (reasons.length) {
    sectionTitle(`Why ${pdfSafe(first.is_number) || 'This Standard'} Was Recommended`)
    bulletList(reasons)
  }

  // 4. Version & amendments
  if (version.edition_label || version.edition_year || version.status) {
    sectionTitle('Version & Amendment Status')
    labelValue('Current Edition', version.edition_label ? `${version.edition_label} (${version.edition_year || '—'})` : '—')
    labelValue('Status', version.status)
    const amendments = (version.amendments || []).map((am) => `${am.label}: ${am.title}`).join(' | ')
    labelValue('Amendments', amendments || 'None recorded')
    y += 6
  }

  // 5. Compliance snapshot (top standard)
  if (compliance.length) {
    sectionTitle('Certification & Compliance')
    bulletList(compliance.map((item) => `${item.type}: ${item.title || item.identifier || '—'} (${item.status || '—'}${item.applicability_note ? ' — ' + item.applicability_note : ''})`))
  }

  // 6. Missing information
  if (missing.length) {
    sectionTitle('Missing / Ambiguous Information')
    bulletList(missing)
  }

  // 7. Source & traceability (top standard)
  if (provenance.source_type || provenance.source_url) {
    sectionTitle('Source & Traceability')
    labelValue('Primary Source', provenance.source_type)
    labelValue('Source URL', provenance.source_url)
    labelValue('Retrieved At', provenance.retrieved_at)
    labelValue('Retrieval Method', summary.retrieval_method)
  }

  // Disclaimer box
  ensure(84)
  doc.setFillColor(240, 245, 252)
  doc.roundedRect(margin, y, contentWidth, 58, 4, 4, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(120, 135, 153)
  doc.text('DISCLAIMER', margin + 12, y + 16)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  const disclaimer = doc.splitTextToSize('This report is generated by StandIQ for guidance only. Verify all standards against current official BIS documents, amendments, and applicable government notifications before final procurement decisions.', contentWidth - 24)
  doc.text(disclaimer, margin + 12, y + 29)

  // Footer on every page
  const pageCount = doc.getNumberOfPages()
  for (let page = 1; page <= pageCount; page++) {
    doc.setPage(page)
    doc.setDrawColor(219, 226, 236)
    doc.setLineWidth(0.8)
    doc.line(margin, pageHeight - 44, pageWidth - margin, pageHeight - 44)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7)
    doc.setTextColor(120, 135, 153)
    doc.text('StandIQ - Right Standards. Right Tenders.', margin, pageHeight - 26)
    doc.text(`Page ${page} of ${pageCount}`, pageWidth - margin, pageHeight - 26, { align: 'right' })
  }

  return doc
}

function Dashboard({ data, onDownload, onGenerate, onNewSearch, onUpload, onExplanation, onRelated, onVersionHistory, onCompliance, onMapping, onRefine, onSources, onEvidence, onStandardEvidence, onSave, isSaved }) {
  return <>
    <RecommendationHeader onNewSearch={onNewSearch} onDownload={onDownload} onGenerate={onGenerate} onSave={onSave} isSaved={isSaved} />
    <RequirementCard requirement={data.requirement} />
    <SummaryMetrics metrics={data.metrics} />
    <StandardsTable standards={data.standards} onEvidence={onStandardEvidence} />
    <div className="two-column">
      <Explanation factors={data.matchFactors} preview={data.explanationPreview} onDetails={onExplanation} />
      <RelatedStandards related={data.related} onViewAll={onRelated} />
    </div>
    <div className="three-column">
      <VersionCard version={data.version} onHistory={onVersionHistory} />
      <ComplianceCard compliance={data.compliance} onDetails={onCompliance} />
      <MappingCard mapping={data.mapping} onViewAll={onMapping} />
    </div>
    <div className="three-column bottom-grid">
      <MissingInformation missing={data.missing} onRefine={onRefine} />
      <TenderOutput onGenerate={onGenerate} onDownload={onDownload} />
      <Traceability traceability={data.traceability} onSources={onSources} onEvidence={onEvidence} />
    </div>
    <DocumentAnalysis document={data.document} onUpload={onUpload} />
    <footer><span>◆</span> StandIQ provides AI-powered recommendations. Verify official compliance with the latest BIS documents and notifications before final procurement decisions.</footer>
  </>
}
