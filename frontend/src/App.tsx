import { useState, useEffect } from 'react'
import { Landing } from './components/Landing'
import { GradingProgress } from './components/GradingProgress'
import Result from './components/Result'
import { BatchUpload } from './components/BatchUpload'
import { BatchResults } from './components/BatchResults'
import { api, APIError } from './services/api'
import type { BatchPortfolioItem, BatchGradingResponse, GradingResult } from './services/api'
import { FileText, Link as LinkIcon, Loader2, Clock, Trash2 } from 'lucide-react'

type AppState = 'landing' | 'grading' | 'result' | 'batch-upload' | 'batch-grading' | 'batch-results' | 'error'
type TabMode = 'single' | 'batch'

export default function App() {
  const [state, setState] = useState<AppState>('landing')
  const [mode, setMode] = useState<TabMode>('single')
  const [result, setResult] = useState<GradingResult | null>(null)
  const [batchResults, setBatchResults] = useState<BatchGradingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentPortfolioUrl, setCurrentPortfolioUrl] = useState<string>('')
  const [batchCount, setBatchCount] = useState<number>(0)
  const [batchElapsedTime, setBatchElapsedTime] = useState<number>(0)
  const [clearingCache, setClearingCache] = useState<boolean>(false)

  const handleStartGrading = async (portfolioUrl: string, forceRefresh: boolean = false) => {
    setCurrentPortfolioUrl(portfolioUrl)
    setState('grading')
    setError(null)
    try {
      const gradingResult = await api.gradePortfolio(portfolioUrl, forceRefresh)
      setResult(gradingResult)
      setState('result')
    } catch (error) {
      console.error('Error during grading:', error)
      if (error instanceof APIError) {
        setError(error.message)
      } else {
        setError('An unexpected error occurred')
      }
      setState('error')
    }
  }

  const handleBatchPortfoliosLoaded = async (portfolios: BatchPortfolioItem[]) => {
    setBatchCount(portfolios.length)
    setBatchElapsedTime(0)
    setState('batch-grading')
    setError(null)
    try {
      const batchResult = await api.batchGradePortfolios(portfolios)
      setBatchResults(batchResult)
      setState('batch-results')
    } catch (error) {
      console.error('Error during batch grading:', error)
      if (error instanceof APIError) {
        setError(error.message)
      } else {
        setError('An unexpected error occurred during batch processing')
      }
      setState('error')
    }
  }

  // Elapsed time counter for batch grading
  useEffect(() => {
    if (state !== 'batch-grading') return

    const timer = setInterval(() => {
      setBatchElapsedTime((prev) => prev + 0.1)
    }, 100)

    return () => clearInterval(timer)
  }, [state])

  const handleRestart = () => {
    setState('landing')
    setResult(null)
    setBatchResults(null)
    setError(null)
    setCurrentPortfolioUrl('')
    setBatchCount(0)
  }

  const handleTabChange = (newMode: TabMode) => {
    setMode(newMode)
    setState(newMode === 'single' ? 'landing' : 'batch-upload')
    setResult(null)
    setBatchResults(null)
    setError(null)
  }

  const handleClearAllCache = async () => {
    if (!confirm('Are you sure you want to clear all cached results? This will force fresh analysis for all portfolios.')) {
      return
    }

    setClearingCache(true)
    try {
      const response = await api.clearAllCache()
      alert(`Cache cleared successfully! ${response.deleted_entries} entries removed.`)
    } catch (error) {
      console.error('Error clearing cache:', error)
      if (error instanceof APIError) {
        alert(`Failed to clear cache: ${error.message}`)
      } else {
        alert('Failed to clear cache')
      }
    } finally {
      setClearingCache(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Tab Navigation - Only show on landing/upload screens */}
      {(state === 'landing' || state === 'batch-upload') && (
        <div className="bg-gray-900 border-b border-gray-800">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex gap-2 items-center justify-between">
              <div className="flex gap-2">
                <button
                  onClick={() => handleTabChange('single')}
                  className={`
                    flex items-center gap-2 px-6 py-4 font-semibold transition-all border-b-2
                    ${mode === 'single'
                      ? 'text-purple-400 border-purple-500'
                      : 'text-gray-400 border-transparent hover:text-gray-200'
                    }
                  `}
                >
                  <LinkIcon className="w-5 h-5" />
                  Single Portfolio
                </button>
                <button
                  onClick={() => handleTabChange('batch')}
                  className={`
                    flex items-center gap-2 px-6 py-4 font-semibold transition-all border-b-2
                    ${mode === 'batch'
                      ? 'text-purple-400 border-purple-500'
                      : 'text-gray-400 border-transparent hover:text-gray-200'
                    }
                  `}
                >
                  <FileText className="w-5 h-5" />
                  Batch Upload (CSV)
                </button>
              </div>

              <button
                onClick={handleClearAllCache}
                disabled={clearingCache}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title="Clear all cached analysis results"
              >
                <Trash2 className="w-4 h-4" />
                {clearingCache ? 'Clearing...' : 'Clear Cache'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {state === 'landing' && <Landing onStartGrading={handleStartGrading} />}

      {state === 'batch-upload' && (
        <div className="min-h-[calc(100vh-65px)] flex items-center justify-center bg-gray-950 p-4">
          <div className="w-full max-w-4xl">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">
                Batch Portfolio Grading
              </h1>
              <p className="text-gray-400">
                Upload a CSV file to grade multiple portfolios at once
              </p>
            </div>
            <div className="bg-gray-900 rounded-2xl shadow-2xl p-8 border border-gray-800">
              <BatchUpload onPortfoliosLoaded={handleBatchPortfoliosLoaded} />
            </div>
          </div>
        </div>
      )}

      {state === 'grading' && <GradingProgress onComplete={() => {}} portfolioUrl={currentPortfolioUrl} />}

      {state === 'batch-grading' && (
        <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
          <div className="w-full max-w-2xl">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600/20 rounded-full mb-4">
                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Processing Batch
              </h2>
              <p className="text-gray-400">
                Analyzing {batchCount} portfolio{batchCount !== 1 ? 's' : ''}...
              </p>
            </div>

            {/* Progress Bar with Time */}
            <div className="mb-6 bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="flex items-center justify-between mb-3 text-sm">
                <div className="flex items-center gap-2 text-gray-400">
                  <Clock className="w-4 h-4" />
                  <span>Elapsed: <span className="text-white font-medium">{batchElapsedTime.toFixed(1)}s</span></span>
                </div>
                <span className="text-gray-400">
                  Expected: <span className="text-white font-medium">~{Math.ceil(batchCount * 20 / 60)} min</span>
                </span>
              </div>

              {/* Progress Bar */}
              <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-purple-600 transition-all duration-300 ease-out rounded-full"
                  style={{
                    width: `${Math.min((batchElapsedTime / (batchCount * 20)) * 100, 95)}%`
                  }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </div>
              </div>

              <div className="mt-2 text-right text-xs text-gray-500">
                {Math.min(Math.round((batchElapsedTime / (batchCount * 20)) * 100), 95)}% complete
              </div>
            </div>

            {/* Info Card */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-800 border-t-purple-600"></div>
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium mb-1">Processing portfolios...</p>
                  <p className="text-sm text-gray-400 mb-2">
                    Each portfolio undergoes a comprehensive 27-parameter analysis
                  </p>
                  <ul className="text-xs text-gray-500 space-y-1">
                    <li>• Loading and rendering portfolio websites</li>
                    <li>• Analyzing structure, sections, and content</li>
                    <li>• AI-powered feedback generation</li>
                    <li>• Responsiveness and design checks</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Footer tip */}
            <div className="mt-6 text-center text-sm text-gray-500">
              This may take a few minutes. Please don't close this window...
            </div>
          </div>
        </div>
      )}

      {state === 'result' && result && (
        <Result result={result} onRestart={handleRestart} />
      )}

      {state === 'batch-results' && batchResults && (
        <BatchResults results={batchResults} onRestart={handleRestart} />
      )}

      {state === 'error' && (
        <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
          <div className="w-full max-w-md p-8 space-y-8 bg-gray-900 rounded-2xl shadow-xl border border-gray-800">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl text-red-400">!</span>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Something Went Wrong
              </h2>
              <p className="text-gray-400 mb-6">
                {error}
              </p>
              <button
                onClick={handleRestart}
                className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
