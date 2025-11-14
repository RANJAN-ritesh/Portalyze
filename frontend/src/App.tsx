import { useState } from 'react'
import { Landing } from './components/Landing'
import { GradingProgress } from './components/GradingProgress'
import Result from './components/Result'
import { api, APIError } from './services/api'
import type { GradingResult } from './services/api'

type AppState = 'landing' | 'grading' | 'result' | 'error'

export default function App() {
  const [state, setState] = useState<AppState>('landing')
  const [result, setResult] = useState<GradingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentPortfolioUrl, setCurrentPortfolioUrl] = useState<string>('')

  const handleStartGrading = async (portfolioUrl: string, geminiApiKey: string, forceRefresh: boolean = false) => {
    setCurrentPortfolioUrl(portfolioUrl)
    setState('grading')
    setError(null)
    try {
      const gradingResult = await api.gradePortfolio(portfolioUrl, geminiApiKey, forceRefresh)
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

  const handleRestart = () => {
    setState('landing')
    setResult(null)
    setError(null)
    setCurrentPortfolioUrl('')
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Content */}
      {state === 'landing' && <Landing onStartGrading={handleStartGrading} />}

      {state === 'grading' && <GradingProgress onComplete={() => {}} portfolioUrl={currentPortfolioUrl} />}

      {state === 'result' && result && (
        <Result result={result} onRestart={handleRestart} />
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
