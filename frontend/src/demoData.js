export const recommendationDemo = {
  requirement: {
    text: 'Stainless steel cable tray with perforated type for electrical wiring in industrial applications',
    language: 'English',
    source: 'Text input',
    searchedAt: '28 May 2025, 10:30 AM',
  },
  metrics: [
    { label: 'Best Match Score', value: '00%', note: 'High relevance', tone: 'green', featured: true },
    { label: 'Standards Found', value: '12', note: 'Relevant Standards', tone: 'blue' },
    { label: 'Related Standards', value: '8', note: 'Normative / Allied', tone: 'green' },
    { label: 'Latest Version', value: 'Up to date', note: 'Includes Amendments', tone: 'orange' },
    { label: 'Compliance Checks', value: '4 / 4', note: 'Applicable Identified', tone: 'purple' },
    { label: 'Requirements Extracted', value: '19', note: 'From Input', tone: 'blue' },
    { label: 'Document Pages', value: '0', note: 'Text Input', tone: 'orange' },
  ],
  standards: [
    { rank: 1, number: 'IS 9537', title: 'Stainless Steel Wire and Wire Products', score: 95, status: 'Latest', type: 'Primary' },
    { rank: 2, number: 'IS 14821:2021', title: 'Stainless Steel Sheets, Plates and Strips', score: 88, status: 'Latest', type: 'Related' },
    { rank: 3, number: 'IS 4759:2016', title: 'Perforated Cable Trays and Cable Ladders', score: 82, status: 'Latest', type: 'Primary' },
    { rank: 4, number: 'IS 2062:2011', title: 'Hot Rolled Medium and High Tensile Structural Steel', score: 75, status: 'Latest', type: 'Related' },
    { rank: 5, number: 'IS 277:2003', title: 'Mild Steel and Medium Tensile Steel Bars and Sections', score: 68, status: 'Latest', type: 'Related' },
  ],
  matchFactors: ['Product Type Match', 'Material Match', 'Application / Intended Use Match', 'Technical Requirements Match', 'Scope Match'],
  related: {
    normative: ['IS 8028:2021 - Reclosable Coatings of Zinc on Iron & Steel', 'IS 2619:1984 - Recommended Practice for Hot Dip Galvanizing', 'IS 14820:2019 - General Requirements for Cable Management Systems'],
    allied: ['IS 15969:2008 - Cable Trays, Cable Ladders and Accessories', 'IS 1200:2020 - Safety of Machinery', 'IS 732:2019 - Code of Practice for Electrical Wiring Installations'],
  },
  version: { current: 'Yes', superseded: 'No', amendments: '2', latest: 'Amendment No. 1 (2022)', date: '10 Jan 2024' },
  compliance: [
    { label: 'BIS Product Certification', status: 'Applicable', tone: 'green' },
    { label: 'QCO (Quality Control Order)', status: 'Applicable', tone: 'green' },
    { label: 'CRS (Compulsory Registration Scheme)', status: 'Not Applicable', tone: 'slate' },
    { label: 'Hallmarking', status: 'Not Applicable', tone: 'slate' },
  ],
  mapping: [
    ['Product Type', 'Scope / Title', 'Matched'],
    ['Material', 'Material Specification', 'Matched'],
    ['Application / Use', 'Scope Clause', 'Matched'],
    ['Perforated Type', 'Technical Requirement', 'Matched'],
    ['Load / Strength', 'Clause 7: Load Bearing', 'Matched'],
    ['Finishing / Coating', 'Related Standard', 'Matched'],
    ['Testing', 'Test Method', 'Matched'],
    ['Installation', 'Allied Standard', 'Matched'],
  ],
  missing: ['Load capacity', 'Dimensions', 'Environmental conditions', 'Coating type and thickness'],
  traceability: { source: 'Bureau of Indian Standards (BIS)', dataStatus: 'Verified & Updated', indexed: '27 May 2025', retrieved: '28 May 2025, 10:30 AM', method: 'Hybrid Search (Metadata + Keyword + Semantic)' },
  document: { name: 'No document uploaded', pages: '0', language: 'English', extracted: '19', relevant: '8' },
}

export const navigation = ['Dashboard', 'Search Standards', 'Upload Document', 'History', 'Saved Results', 'Alerts', 'Settings', 'Help & Guide', 'Logout']
