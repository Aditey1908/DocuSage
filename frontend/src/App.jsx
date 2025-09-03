import { useState } from 'react'
import docusageLogo from './assets/docusage-logo.png'
import DomainSelector from './components/DomainSelector'
import FileUploader from './components/FileUploader'
import { BackgroundGradientAnimation } from './components/ui/background-gradient-animation'

function App() {
  const [file, setFile] = useState(null)
  const [selectedDomain, setSelectedDomain] = useState('finance') // Default selected domain
  const [isLoading, setIsLoading] = useState(false)

  const handleProcessDocument = () => {
    if (!file) return
    
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      console.log('Processing document:', { file, domain: selectedDomain })
      setIsLoading(false)
      // Handle the response here
    }, 2000)
  }

  return (
    <BackgroundGradientAnimation>
      <div className="max-w-4xl w-[90%] mx-auto py-12 relative min-h-screen flex flex-col items-center justify-center">
        <header className="text-center mb-12">
          <div className="animate-[fadeIn_1s_ease]">
            <img src={docusageLogo} alt="DocuSage Logo" className="max-w-[280px] h-auto mx-auto block drop-shadow-2xl" />
            <p className="text-xl max-w-lg mx-auto mt-5 font-medium text-center">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-300 via-white to-cyan-200 drop-shadow-lg">
                Unlock the wisdom in your documents
              </span>
            </p>
          </div>
        </header>
        
        <main className="w-full">
          <section className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 md:p-8 shadow-2xl border border-white/20 transition-all duration-500 hover:shadow-purple-500/20 hover:border-white/30">
            <FileUploader file={file} setFile={setFile} />
            
            {/* File preview is now integrated into the uploader component */}
            
            <div className="mt-6">
              <h3 className="font-medium text-white drop-shadow-md mb-3">Document domain:</h3>
              <DomainSelector 
                selectedDomain={selectedDomain} 
                setSelectedDomain={setSelectedDomain} 
              />
            </div>
            
            <button 
              className={`mt-8 w-full max-w-[300px] mx-auto block py-3.5 px-8 bg-gradient-to-r from-purple-600 via-blue-500 to-cyan-400 text-white rounded-full font-medium text-base transition-all duration-300 
              shadow-lg hover:shadow-xl hover:shadow-purple-500/30 
              ${!file && 'opacity-70 cursor-not-allowed filter grayscale'} 
              ${isLoading ? 'animate-pulse' : 'hover:scale-105'}`}
              onClick={handleProcessDocument}
              disabled={!file || isLoading}
            >
              {isLoading ? 'Processing...' : file ? 'Start Learning about your doc' : 'Upload a document to begin'}
            </button>
          </section>
        </main>
      </div>
    </BackgroundGradientAnimation>
  )
}

export default App
