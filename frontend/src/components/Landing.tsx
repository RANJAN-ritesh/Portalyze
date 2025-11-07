import { useState } from 'react';
import { Globe, Sparkles, CheckCircle2, Zap, List, RefreshCw } from 'lucide-react';

interface LandingProps {
  onStartGrading: (portfolioUrl: string, forceRefresh: boolean) => void;
}

export function Landing({ onStartGrading }: LandingProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Basic URL validation
    if (!url.trim()) {
      setError('Please enter your portfolio URL');
      return;
    }

    // Check if it's a valid URL
    try {
      const urlObj = new URL(url);

      // Check for localhost
      if (urlObj.hostname === 'localhost' || urlObj.hostname === '127.0.0.1') {
        setError('Please deploy your portfolio first. Localhost URLs are not supported.');
        return;
      }

      // Check for HTTPS
      if (urlObj.protocol !== 'https:' && urlObj.protocol !== 'http:') {
        setError('Please enter a valid HTTP or HTTPS URL');
        return;
      }

      onStartGrading(url, forceRefresh);
    } catch {
      setError('Please enter a valid URL (e.g., https://yourportfolio.com)');
    }
  };

  const exampleUrls = [
    'https://portfolio.example.com',
    'https://username.github.io',
    'https://mysite.vercel.app'
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Globe className="w-12 h-12 text-purple-500" />
            <h1 className="text-5xl font-bold text-white">
              Portalyze
            </h1>
          </div>
          <p className="text-xl text-gray-300 mb-2">
            AI-Powered Portfolio Grading
          </p>
          <p className="text-sm text-gray-400 flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4" />
            Instant feedback on your deployed portfolio
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-900 rounded-2xl shadow-2xl p-8 space-y-6 border border-gray-800">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-white">
              Get Your Portfolio Graded
            </h2>
            <p className="text-gray-400">
              Enter your deployed portfolio URL for comprehensive AI-powered analysis
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="portfolio-url" className="block text-sm font-medium text-gray-300 mb-2">
                Portfolio URL <span className="text-red-500">*</span>
              </label>
              <input
                id="portfolio-url"
                type="text"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setError('');
                }}
                placeholder="https://yourportfolio.com"
                className={`w-full px-4 py-3 border-2 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors ${
                  error
                    ? 'border-red-600 bg-red-950/20'
                    : 'border-gray-700 bg-gray-800'
                } text-white placeholder-gray-500`}
                autoFocus
              />
              {error && (
                <p className="mt-2 text-sm text-red-400">
                  {error}
                </p>
              )}
            </div>

            {/* Force Refresh Checkbox */}
            <div className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                id="force-refresh"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                className="w-4 h-4 text-purple-600 bg-gray-800 border-gray-700 rounded focus:ring-purple-500 focus:ring-2"
              />
              <label htmlFor="force-refresh" className="text-gray-300 flex items-center gap-2 cursor-pointer">
                <RefreshCw className="w-4 h-4" />
                <span>Force fresh analysis (bypass cache)</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={!url.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-all disabled:cursor-not-allowed shadow-lg"
            >
              Analyze Portfolio →
            </button>
          </form>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-800">
            <div className="text-center">
              <div className="w-10 h-10 mx-auto mb-2 bg-purple-600/20 rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-xs font-semibold text-gray-300">Fast</div>
              <div className="text-xs text-gray-500">15-30s analysis</div>
            </div>
            <div className="text-center">
              <div className="w-10 h-10 mx-auto mb-2 bg-purple-600/20 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-xs font-semibold text-gray-300">Accurate</div>
              <div className="text-xs text-gray-500">27 parameters</div>
            </div>
            <div className="text-center">
              <div className="w-10 h-10 mx-auto mb-2 bg-purple-600/20 rounded-full flex items-center justify-center">
                <Zap className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-xs font-semibold text-gray-300">Free</div>
              <div className="text-xs text-gray-500">Always free</div>
            </div>
          </div>

          {/* Examples */}
          <div className="pt-4 border-t border-gray-800">
            <p className="text-xs text-gray-500 mb-2">Example URLs:</p>
            <div className="flex flex-wrap gap-2">
              {exampleUrls.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setUrl(example)}
                  className="text-xs px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-full text-gray-300 transition-colors border border-gray-700"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <List className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-purple-300 mb-1">What we check:</p>
                <p className="text-sm text-purple-400">
                  About section, Projects (min 3), Skills, Contact info, Responsiveness, Design quality, and 20+ other parameters
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          Powered by AI • Gemini + Groq • MediaPipe Face Detection
        </p>
      </div>
    </div>
  );
}
