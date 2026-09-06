import { useState } from 'react'

export function Icon({ children }) { return <span className="icon" aria-hidden="true">{children}</span> }

export function TopNavigation({ onNavigate, onProfile, theme, onToggleTheme }) {
  return <header className="top-nav"><button className="brand brand-button" onClick={() => onNavigate('Dashboard')}><span className="brand-mark">◆</span><span><strong>StandIQ</strong><small>Right Standards. Right Tenders.</small></span></button><nav className="top-links"><button onClick={() => onNavigate('Dashboard')}><Icon>⌂</Icon>Home</button><button onClick={() => onNavigate('Search Standards')}><Icon>⌕</Icon>Search</button><button onClick={() => onNavigate('Upload Document')}><Icon>⇧</Icon>Upload Document</button><button onClick={() => onNavigate('History')}><Icon>◷</Icon>History</button><button onClick={() => onNavigate('Saved Results')}><Icon>▱</Icon>Saved</button></nav><button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle dark mode" title="Toggle dark / light mode">{theme === 'dark' ? '☀' : '☾'}</button><button className="profile" aria-label="Open profile" onClick={onProfile}>AR</button></header>
}

export function Sidebar({ active, onSelect }) {
  const icons = ['▦', '⌕', '⇧', '◷', '▤', '♢', '⚙', '?', '↪']
  return <aside className="sidebar"><div className="side-spacer" />{navigation.map((item, index) => <button key={item} className={active === item ? 'side-item active' : 'side-item'} onClick={() => onSelect(item)}><Icon>{icons[index]}</Icon><span>{item}</span></button>)}<div className="side-foot"><span className="brand-mark">◆</span><strong>StandIQ v1.0</strong><small>AI powered standards intelligence</small></div></aside>
}

export const navigation = ['Dashboard', 'Search Standards', 'Upload Document', 'History', 'Saved Results', 'Alerts', 'Settings', 'Help & Guide', 'Logout']

export function SectionHeader({ number, title, action, onAction }) { return <div className="section-header"><h2>{number && <span className="section-number">{number}</span>}{title}</h2>{action && <button className="text-action" onClick={onAction}>{action} →</button>}</div> }

export function RecommendationHeader({ onNewSearch, onDownload, onGenerate, onSave, isSaved }) {
  return <section className="recommendation-header"><div className="completion"><span className="checkmark">✓</span><div><h1>Recommendation Completed</h1><p>Standards identified based on your procurement requirement.</p></div></div><div className="header-actions"><button className="button secondary" onClick={onDownload}>⇩ Download Report (PDF)</button><button className="button secondary" onClick={onGenerate}>↗ Generate Tender Specification</button><button className="button secondary bookmark-button" onClick={onSave}>{isSaved ? '✓ Bookmarked' : '◆ Save Result'}</button><button className="button primary" onClick={onNewSearch}>⌕ New Search</button></div></section>
}

export function RequirementCard({ requirement }) {
  return <section className="panel requirement-card"><div className="requirement-icon">▤</div><div className="requirement-content"><span className="eyebrow">Your requirement</span><h2>{requirement.text}</h2><div className="meta-row"><span>◉ Language: <strong>{requirement.language}</strong></span><span>◌ Source: <strong>{requirement.source}</strong></span><span>◷ Searched on <strong>{requirement.searchedAt}</strong></span></div></div></section>
}

export function SummaryMetrics({ metrics }) {
  return <section className="metrics-grid">{metrics.map((metric) => <article className={`metric-card tone-${metric.tone} ${metric.featured ? 'featured' : ''}`} key={metric.label}><div className="metric-label">{metric.label}</div><strong>{metric.value}</strong><span>{metric.note}</span>{metric.featured && <div className="score-ring"><span>{metric.value}</span></div>}</article>)}</section>
}

export function StandardsTable({ standards, onEvidence, onViewAll }) {
  return <section className="panel table-panel"><SectionHeader number="1" title="Recommended Indian Standards" action={standards.length ? `View All (${standards.length})` : undefined} onAction={onViewAll} /><div className="table-wrap"><table><thead><tr><th>Rank</th><th>IS Number</th><th>Title</th><th>Applicability Score</th><th>Status</th><th>Type</th><th>Evidence</th></tr></thead><tbody>{standards.map((standard) => <tr key={standard.number}><td><span className="rank">{standard.rank}</span></td><td><a href={`#${standard.number}`}>{standard.number}</a></td><td className="title-cell">{standard.title}</td><td><div className="score-cell"><span>{standard.score}%</span><i><b style={{ width: `${standard.score}%` }} /></i></div></td><td><span className="status-pill success">{standard.status}</span></td><td><span className={`type-label ${standard.type.toLowerCase()}`}>{standard.type}</span></td><td><button className="evidence-button" onClick={() => onEvidence(standard)}>◉ View Evidence</button></td></tr>)}</tbody></table></div>{standards.length > 0 && <button className="table-footer-action" onClick={onViewAll}>View all {standards.length} recommended standards →</button>}</section>
}

export function Explanation({ factors, preview, onDetails }) {
  return <section className="panel explanation-panel"><SectionHeader number="2" title="Why These Standards Are Recommended" /><div className="explanation-grid"><div className="factor-list">{factors.map((factor) => <div className="factor" key={factor}><span>✓</span>{factor}<b>✓</b></div>)}</div><div className="ai-note"><div className="ai-title"><span>✦</span> AI Explanation</div><p>{preview || 'Open explanation details to view a grounded summary based on verified recommendation evidence.'}</p><button className="button tiny" onClick={onDetails}>View Explanation Details</button></div></div></section>
}

export function RelatedStandards({ related, onViewAll }) {
  const rows = [...related.normative, ...related.allied]
  return <section className="panel related-panel"><SectionHeader number="3" title="Related / Normative Standards" /><div className="table-wrap"><table><thead><tr><th>Standard</th><th>Title</th><th>Relationship</th><th>Why Relevant</th><th>Status</th></tr></thead><tbody>{rows.length ? rows.map((item) => <tr key={`${item.standard}-${item.relationship}`}><td>{item.standard || item}</td><td>{item.title || '—'}</td><td>{item.relationship || '—'}</td><td>{item.whyRelevant || '—'}</td><td>{item.status || '—'}</td></tr>) : <tr><td colSpan="5">No related standards recorded yet. Use View all to fetch authoritative relationships.</td></tr>}</tbody></table></div><button className="table-footer-action" onClick={onViewAll}>View all related standards →</button></section>
}

export function VersionCard({ version, onHistory }) {
  return <section className="panel compact-panel"><SectionHeader number="4" title="Version & Amendment Status" /><div className="detail-list"><p>Current Standard <strong className="value-yes">{version.current}</strong></p><p>Superseded <strong>{version.superseded}</strong></p><p>Total Amendments <strong>{version.amendments}</strong></p><p>Latest Amendment <strong>{version.latest}</strong></p><p>Date of Latest Amendment <strong>{version.date}</strong></p></div><div className="warning">⚠ Tender may refer to an older version.<br />Review recommendation.</div><button className="button tiny" onClick={onHistory}>View Version History</button></section>
}

export function ComplianceCard({ compliance, onDetails }) {
  return <section className="panel compact-panel"><SectionHeader number="5" title="Certification & Compliance" /><div className="compliance-list">{compliance.map((item) => <p key={item.label}><span>{item.label}</span><strong className={`status-pill ${item.tone}`}>{item.status}</strong></p>)}</div><div className="info-note">ⓘ Compliance status is based on authoritative BIS data and applicable government notifications.</div><button className="button tiny" onClick={onDetails}>View Details</button></section>
}

export function MappingCard({ mapping, onViewAll }) {
  return <section className="panel compact-panel mapping-panel"><SectionHeader number="6" title="Requirement → Standard Mapping" /><div className="mapping-table"><div className="mapping-head"><span>Requirement Element</span><span>Matched Standard Evidence</span><span>Match</span></div>{mapping.map(([element, evidence, status]) => <div className="mapping-row" key={element}><span>{element}</span><span>{evidence}</span><b>{status === 'Matched' ? '✓' : '!'}</b></div>)}</div><button className="button tiny" onClick={onViewAll}>View Full Mapping</button></section>
}

export function MissingInformation({ missing, onRefine }) {
  return <section className="panel compact-panel missing-panel"><SectionHeader number="7" title="Missing / Ambiguous Information" /><p>The following information could improve applicability:</p><ul>{missing.map((item) => <li key={item}>{item} <span>+</span></li>)}</ul><button className="button tiny" onClick={onRefine}>Refine Requirement</button></section>
}

export function TenderOutput({ onGenerate, onDownload }) {
  return <section className="panel compact-panel tender-panel"><SectionHeader number="8" title="Tender-Ready Output" /><p>Your procurement specification should include:</p><ul><li>Primary Applicable Standard(s)</li><li>Supporting / Related Standards</li><li>Test Methods</li><li>Safety / Installation Standards</li><li>Applicable Compliance Requirements</li></ul><button className="button primary wide" onClick={onGenerate}>↗ Generate Tender Specification</button><button className="button secondary wide" onClick={onDownload}>⇩ Download Report (PDF)</button></section>
}

export function Traceability({ traceability, onSources, onEvidence }) {
  return <section className="panel compact-panel trace-panel"><SectionHeader number="9" title="Source & Traceability" /><div className="detail-list"><p>Primary Source <strong>{traceability.source}</strong></p><p>Data Status <strong className="value-yes">{traceability.dataStatus}</strong></p><p>Indexed On <strong>{traceability.indexed}</strong></p><p>Retrieved On <strong>{traceability.retrieved}</strong></p><p>Retrieval Method <strong>{traceability.method}</strong></p></div><div className="trace-note">✓ All results are traceable to authorized BIS sources and official notifications.</div><button className="button tiny" onClick={onSources}>View Source Documents</button><button className="button tiny" onClick={onEvidence}>View All Evidence</button></section>
}

export function DocumentAnalysis({ document, onUpload }) {
  return <section className="panel document-panel"><SectionHeader title="Document Analysis" action="Upload Document" onAction={onUpload} /><div className="document-grid"><p><span>Document Name</span><strong>{document.name}</strong></p><p><span>Pages Processed</span><strong>{document.pages}</strong></p><p><span>Language Detected</span><strong>{document.language}</strong></p><p><span>Extracted Text Length</span><strong>{document.extractedLength ? `${document.extractedLength} characters` : (typeof document.extracted === 'string' ? document.extracted : `${document.extracted} ${document.extracted === 1 ? 'requirement' : 'requirements'}`)}</strong></p><p><span>Requirements Relevant to Standards</span><strong>{document.relevant}</strong></p></div></section>
}

export function PageHeading({ eyebrow, title, description }) { return <div className="page-heading"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div> }

export function SearchPage({ onSearch, loading }) {
  const [query, setQuery] = useState('')
  return <section className="page-view"><PageHeading eyebrow="Standards intelligence" title="Search Standards" description="Describe a procurement requirement to prepare a standards analysis." /><div className="panel form-panel"><label htmlFor="requirement">Procurement requirement</label><textarea id="requirement" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Example: stainless steel cable tray for industrial electrical wiring" /><div className="form-footer"><span>English · Malayalam · Tamil · Hindi</span><button className="button primary" onClick={() => onSearch(query)} disabled={!query.trim() || loading}>{loading ? 'Analyzing…' : '⌕ Start Analysis'}</button></div></div></section>
}

export function UploadPage({ selectedFile, onFile, onAnalyze, loading }) {
  return <section className="page-view"><PageHeading eyebrow="Document workspace" title="Upload Document" description="Add a tender or technical specification for document analysis." /><div className="panel upload-panel"><label className="drop-zone" htmlFor="document-upload"><span className="upload-icon">⇧</span><strong>{selectedFile ? selectedFile.name : 'Choose a document to analyze'}</strong><span>PDF files · Maximum 20 MB</span><input id="document-upload" type="file" accept=".pdf,application/pdf" onChange={(event) => onFile(event.target.files?.[0] || null)} /></label>{selectedFile && <div className="selected-file"><span>✓ Ready for analysis</span><small>{Math.ceil(selectedFile.size / 1024)} KB · {selectedFile.type || 'PDF Document'}</small></div>}<button className="button primary" disabled={!selectedFile || loading} onClick={onAnalyze}>{loading ? 'Analyzing…' : 'Analyze Document'}</button></div></section>
}

export function HistoryPage({ history, onOpen, onDelete }) {
  return <section className="page-view"><PageHeading eyebrow="Workspace memory" title="Search History" description="Review previous procurement requirements and reopen a result." /><div className="history-list">{history.length ? history.map((item) => <div className="panel history-item" key={item.id}><button className="history-open" onClick={() => onOpen(item)}><span className="history-icon">◷</span><span><strong>{item.text}</strong><small>{item.source} · {item.createdAt}</small></span><span className="history-arrow">→</span></button><button className="history-delete" aria-label="Delete history item" title="Delete" onClick={(e) => { e.stopPropagation(); onDelete(item.id) }}>✕</button></div>) : <div className="panel empty-state">No searches yet. Start with a procurement requirement.</div>}</div></section>
}

export function SavedResultsPage({ saved, onOpen, onRemove }) {
  return <section className="page-view"><PageHeading eyebrow="Bookmarked intelligence" title="Saved Results" description="Your bookmarked recommendation results appear here for quick access." /><div className="history-list">{saved.length ? saved.map((item) => <div className="panel history-item" key={item.id}><button className="history-open" onClick={() => onOpen(item)}><span className="history-icon">▤</span><span><strong>{item.text}</strong><small>{item.source} · {item.createdAt}</small></span><span className="history-arrow">→</span></button><button className="history-delete" aria-label="Remove saved result" title="Remove" onClick={(e) => { e.stopPropagation(); onRemove(item.id) }}>✕</button></div>) : <div className="panel empty-state"><span className="empty-icon">◇</span><h2>No saved results</h2><p>Run an analysis and press “Save Result” on the dashboard to bookmark it here.</p></div>}</div></section>
}

export function SimplePage({ title, description, actionLabel, onAction }) {
  return <section className="page-view"><PageHeading eyebrow="StandIQ workspace" title={title} description={description} /><div className="panel empty-state"><span className="empty-icon">◇</span><h2>{title} is ready</h2><p>This workspace is prepared for the next product phase.</p>{actionLabel && <button className="button primary" onClick={onAction}>{actionLabel}</button>}</div></section>
}

function renderTable(columns, rows, emptyMessage) {
  if (!rows?.length) return <p className="modal-empty">{emptyMessage || 'No data available.'}</p>
  return <div className="table-wrap modal-table"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{Object.values(row).map((value, cellIndex) => <td key={cellIndex}>{Array.isArray(value) ? value.map((item) => item.label || item.title || JSON.stringify(item)).join('; ') : (value ?? '—')}</td>)}</tr>)}</tbody></table></div>
}

export function ActionModal({ dialog, loading, onClose, onRefine }) {
  const [refinement, setRefinement] = useState('')
  if (!dialog) return null

  let content = null
  if (dialog.loading) {
    content = <p>Loading…</p>
  } else if (dialog.error) {
    content = <p className="modal-error">{dialog.error}</p>
  } else if (dialog.refine) {
    content = <>
      <p>Add missing or ambiguous details. Your original requirement will be preserved.</p>
      <textarea className="modal-textarea" value={refinement} onChange={(event) => setRefinement(event.target.value)} placeholder="Example: load capacity 500 kg/m, outdoor installation, hot-dip galvanized finish" />
      <button className="button primary" disabled={loading || !refinement.trim()} onClick={() => onRefine(refinement)}>Apply Refinement</button>
    </>
  } else if (dialog.table) {
    const columns = dialog.table[0] ? Object.keys(dialog.table[0]).map((key) => key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())) : []
    content = renderTable(columns, dialog.table, dialog.note)
  } else if (dialog.mapping) {
    content = renderTable(['Requirement Element', 'Extracted Value', 'Recommended Standard', 'Supporting Evidence', 'Match'], dialog.mapping, dialog.note)
  } else if (dialog.compliance) {
    content = <>
      {Object.entries(dialog.compliance).map(([section, items]) => <div key={section} className="modal-section"><h3>{section.replace(/_/g, ' ')}</h3>{items?.length ? items.map((item, index) => <p key={index}><strong>{item.title || item.identifier}</strong>{item.applicability_note ? ` — ${item.applicability_note}` : ''}</p>) : <p>None recorded</p>}</div>)}
      {dialog.note && <p className="modal-note">{dialog.note}</p>}
    </>
  } else {
    content = <>
      {dialog.note && <p className="modal-note">{dialog.note}</p>}
      <pre className="modal-pre">{dialog.body}</pre>
    </>
  }

  return <div className="modal-backdrop" onClick={onClose}><div className="modal modal-wide" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={onClose} aria-label="Close">×</button><h2 id="dialog-title">{dialog.title}</h2>{dialog.status && dialog.status !== 'success' && <p className="modal-status">Status: {dialog.status}</p>}{content}<button className="button primary" onClick={onClose}>Close</button></div></div>
}
