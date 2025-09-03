import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

function FileUploader({ file, setFile }) {
  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [setFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    maxFiles: 1,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'message/rfc822': ['.eml'],
      'application/vnd.ms-outlook': ['.msg']
    }
  })

  return (
    <>
      <div 
        {...getRootProps({ 
          className: 'border border-white/30 rounded-xl p-5 flex items-center justify-between cursor-pointer transition-all duration-300 bg-white/10 backdrop-blur-xl hover:bg-white/20 hover:border-white/40 shadow-lg hover:shadow-purple-500/10'
        })}
      >
        <input {...getInputProps()} />
        <div className="flex items-center">
          <div className="mr-5">
            {file ? (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-lg filter">
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#9333ea" />
                    <stop offset="100%" stopColor="#3b82f6" />
                  </linearGradient>
                </defs>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            ) : (
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#uploadGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-lg animate-float">
                <defs>
                  <linearGradient id="uploadGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#9333ea" />
                    <stop offset="100%" stopColor="#3b82f6" />
                  </linearGradient>
                </defs>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            )}
          </div>
          <div className="text-left">
            <p className="text-white font-medium drop-shadow-sm">
              {isDragActive 
                ? 'Drop your document here' 
                : file 
                  ? file.name 
                  : 'Ask your doc'
              }
            </p>
            <p className="text-white/80 text-sm">
              {file 
                ? `${(file.size / 1024 / 1024).toFixed(2)} MB` 
                : 'Upload a document to begin'
              }
            </p>
          </div>
        </div>
        
        <div className="ml-auto bg-gradient-to-r from-purple-600 to-blue-500 text-white py-2.5 px-6 rounded-full text-sm font-medium hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300 hover:scale-105 shadow-md">
          {file ? 'Change file' : 'Select file'}
        </div>
      </div>
    </>
  )
}

export default FileUploader
