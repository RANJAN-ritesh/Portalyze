import { useState } from 'react';

interface LandingProps {
  onStartGrading: (repoUrl: string) => void;
}

export function Landing({ onStartGrading }: LandingProps) {
  const [repoUrl, setRepoUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (repoUrl.trim()) {
      onStartGrading(repoUrl.trim());
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Portfolio Grader
          </h1>
          <p className="text-muted-foreground">
            Enter your GitHub repository URL to start grading
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
              className="w-full px-4 py-2 rounded-md border border-input bg-background text-foreground"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Start Grading
          </button>
        </form>
      </div>
    </div>
  );
} 