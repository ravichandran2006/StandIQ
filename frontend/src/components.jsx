import { useState } from 'react'

export function Icon({ children }) { return <span className="icon" aria-hidden="true">{children}</span> }

export function TopNavigation() {
  return <header className="top-nav"><div className="brand"><span className="brand-mark">◆</span><span><strong>StandIQ</strong><small>Right Standards. Right Tenders.</small></span></div><nav className="top-links"><button><Icon>⌂</Icon>Home</button><button><Icon>⌕</Icon>Search</button><button><Icon>⇧</Icon>Upload Document</button><button><Icon>◷</Icon>History</button><button><Icon>▱</Icon>Saved</button></nav><button className="profile" aria-label="Open profile">AR</button></header>
}

export function Sidebar({ active, onSelect }) {
  const icons = ['▦', '⌕', '⇧', '◷', '▤', '♢', '⚙', '?', '↪']
  return <aside className="sidebar"><div className="side-spacer" />{navigation.map((item, index) => <button key={item} className={active === item ? 'side-item active' : 'side-item'} onClick={() => onSelect(item)}><Icon>{icons[index]}</Icon><span>{item}</span></button>)}<div className="side-foot"><span className="brand-mark">◆</span><strong>StandIQ v1.0</strong><small>AI powered standards intelligence</small></div></aside>
}

export const navigation = ['Dashboard', 'Search Standards', 'Upload Document', 'History', 'Saved Results', 'Alerts', 'Settings', 'Help & Guide', 'Logout']

export function SectionHeader({ number, title, action, onAction }) { return <div className="section-header"><h2>{number && <span className="section-number">{number}</span>}{title}</h2>{action && <button className="text-action" onClick={onAction}>{action} →</button>}</div> }

export function RecommendationHeader({ onNewSearch, onDownload, onGenerate }) {
  return <section className="recommendation-header"><div className="completion"><span className="checkmark">✓</span><div><h1>Recommendation Completed</h1><p>Standards identified based on your procurement requirement.</p></div></div><div className="header-actions"><button className="button secondary" onClick={onDownload}>⇩ Download Report (PDF)</button><button className="button secondary" onClick={onGenerate}>↗ Generate Tender Specification</button><button className="button primary" onClick={onNewSearch}>⌕ New Search</button></div></section>
}

export function RequirementCard({ requirement }) {
  return <section className="panel requirement-card"><div className="requirement-icon">▤</div><div className="requirement-content"><span className="eyebrow">Your requirement</span><h2>{requirement.text}</h2><div className="meta-row"><span>◉ Language: <strong>{requirement.language}</strong></span><span>◌ Source: <strong>{requirement.source}</strong></span><span>◷ Searched on <strong>{requirement.searchedAt}</strong></span></div></div></section>
}

export function SummaryMetrics({ metrics }) {
  return <section className="metrics-grid">{metrics.map((metric) => <article className={`metric-card tone-${metric.tone} ${metric.featured ? 'featured' : ''}`} key={metric.label}><div className="metric-label">{metric.label}</div><strong>{metric.value}</strong><span>{metric.note}</span>{metric.featured && <div className="score-ring"><span>{metric.value}</span></div>}</article>)}</section>
}

export function StandardsTable({ standards, onEvidence, onViewAll }) {
  return <section className="panel table-panel"><SectionHeader number="1" title="Recommended Indian Standards" action="View All (12)" onAction={onViewAll} /><div className="table-wrap"><table><thead><tr><th>Rank</th><th>IS Number</th><th>Title</th><th>Applicability Score</th><th>Status</th><th>Type</th><th>Evidence</th></tr></thead><tbody>{standards.map((standard) => <tr key={standard.number}><td><span className="rank">{standard.rank}</span></td><td><a href={`#${standard.number}`}>{standard.number}</a></td><td className="title-cell">{standard.title}</td><td><div className="score-cell"><span>{standard.score}%</span><i><b style={{ width: `${standard.score}%` }} /></i></div></td><td><span className="status-pill success">{standard.status}</span></td><td><span className={`type-label ${standard.type.toLowerCase()}`}>{standard.type}</span></td><td><button className="evidence-button" onClick={() => onEvidence(standard)}>◉ View Evidence</button></td></tr>)}</tbody></table></div><button className="table-footer-action" onClick={onViewAll}>View all 12 recommended standards →</button></section>
}

export function Explanation({ factors, onDetails }) {
  return <section className="panel explanation-panel"><SectionHeader number="2" title="Why These Standards Are Recommended" /><div className="explanation-grid"><div className="factor-list">{factors.map((factor) => <div className="factor" key={factor}><span>✓</span>{factor}<b>✓</b></div>)}</div><div className="ai-note"><div className="ai-title"><span>✦</span> AI Explanation</div><p>These standards are recommended because the requirement matches the product type, material, application, and key technical attributes defined in the standards.</p><button className="button tiny" onClick={onDetails}>View Explanation Details</button></div></div></section>
}

export function RelatedStandards({ related, onViewAll }) {
  return <section className="panel related-panel"><SectionHeader number="3" title="Related / Normative Standards" /><div className="related-grid"><div><h3>Normative (Directly Referred)</h3>{related.normative.map((item) => <p key={item}><span className="bullet blue" />{item}</p>)}</div><div><h3>Allied Standards (For Information)</h3>{related.allied.map((item) => <p key={item}><span className="bullet green" />{item}</p>)}</div></div><button className="table-footer-action" onClick={onViewAll}>View all related standards →</button></section>
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
  return <section className="panel document-panel"><SectionHeader title="Document Analysis" action="Upload Document" onAction={onUpload} /><div className="document-grid"><p><span>Document Name</span><strong>{document.name}</strong></p><p><span>Pages Processed</span><strong>{document.pages}</strong></p><p><span>Language Detected</span><strong>{document.language}</strong></p><p><span>Requirements Extracted</span><strong>{document.extracted}</strong></p><p><span>Requirements Relevant to Standards</span><strong>{document.relevant}</strong></p></div></section>
}
