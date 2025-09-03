const DOCUMENT_DOMAINS = [
  { id: 'finance', label: 'Finance' },
  { id: 'health', label: 'Healthcare' },
  { id: 'legal', label: 'Legal' },
  { id: 'insurance', label: 'Insurance' },
  { id: 'education', label: 'Education' },
  { id: 'hr', label: 'HR & Recruitment' },
  { id: 'technical', label: 'Technical' },
  { id: 'research', label: 'Research' },
  { id: 'government', label: 'Government' },
  { id: 'marketing', label: 'Marketing' },
  { id: 'general', label: 'General' },
]

function DomainSelector({ selectedDomain, setSelectedDomain }) {
  return (
    <div className="flex overflow-x-auto pb-2 no-scrollbar">
      <div className="flex space-x-3">
        {DOCUMENT_DOMAINS.map(domain => (
          <button
            key={domain.id}
            className={`px-5 py-2 rounded-full font-medium text-sm transition-all duration-300 whitespace-nowrap ${
              selectedDomain === domain.id 
                ? 'bg-gradient-to-r from-purple-600 to-blue-500 text-white shadow-lg scale-105' 
                : 'bg-white/15 backdrop-blur-sm text-white border border-white/20 hover:bg-white/25 hover:border-white/30 shadow-md'
            }`}
            onClick={() => setSelectedDomain(domain.id)}
          >
            {domain.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default DomainSelector
