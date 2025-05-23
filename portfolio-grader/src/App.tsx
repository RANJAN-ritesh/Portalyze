import { useState } from 'react'
import { Landing } from './components/Landing'
import { GradingProgress } from './components/GradingProgress'
import Result from './components/Result'
import { api } from './services/api'
import type { GradingResult } from './services/api'
import { APIError } from './services/api'

type AppState = 'landing' | 'grading' | 'result' | 'error'

export default function App() {
  const [state, setState] = useState<AppState>('landing')
  const [result, setResult] = useState<GradingResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleStartGrading = async (repoUrl: string) => {
    setState('grading')
    setError(null)
    try {
      const gradingResult = await api.gradePortfolio(repoUrl)
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
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {state === 'landing' && <Landing onStartGrading={handleStartGrading} />}
      {state === 'grading' && <GradingProgress onComplete={() => {}} />}
      {state === 'result' && result && (
        <Result result={result} onRestart={handleRestart} />
      )}
      {state === 'error' && (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="w-full max-w-md p-8 space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-destructive mb-4">
                Error
              </h2>
              <p className="text-muted-foreground mb-6">
                {error}
              </p>
              <button
                onClick={handleRestart}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
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
