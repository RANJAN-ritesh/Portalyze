import { useEffect, useState } from 'react';
import { Loader2, Clock, CheckCircle2, Circle } from 'lucide-react';

interface GradingProgressProps {
  onComplete: () => void;
  portfolioUrl?: string;
}

const steps = [
  { text: 'Loading portfolio website', duration: 3 },
  { text: 'Analyzing page structure', duration: 2 },
  { text: 'Checking About section', duration: 2 },
  { text: 'Evaluating projects', duration: 3 },
  { text: 'Reviewing skills & contact', duration: 2 },
  { text: 'Testing responsiveness', duration: 3 },
  { text: 'AI analysis & feedback', duration: 8 },
];

export function GradingProgress({ onComplete, portfolioUrl }: GradingProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const expectedDuration = steps.reduce((sum, step) => sum + step.duration, 0);

  // Elapsed time counter
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 0.1);
    }, 100);

    return () => clearInterval(timer);
  }, []);

  // Step progression
  useEffect(() => {
    if (currentStep >= steps.length) return;

    const stepDuration = steps[currentStep].duration * 1000;
    const timeout = setTimeout(() => {
      setCurrentStep((prev) => prev + 1);
    }, stepDuration);

    return () => clearTimeout(timeout);
  }, [currentStep]);

  useEffect(() => {
    if (currentStep >= steps.length) {
      onComplete();
    }
  }, [currentStep, onComplete]);

  const progress = Math.min((elapsedTime / expectedDuration) * 100, 95);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600/20 rounded-full mb-4">
            <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">
            Analyzing Portfolio
          </h2>
          {portfolioUrl && (
            <p className="text-gray-400 text-sm truncate max-w-md mx-auto">
              {portfolioUrl}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-8 bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-3 text-sm">
            <div className="flex items-center gap-2 text-gray-400">
              <Clock className="w-4 h-4" />
              <span>Elapsed: <span className="text-white font-medium">{elapsedTime.toFixed(1)}s</span></span>
            </div>
            <span className="text-gray-400">
              Expected: <span className="text-white font-medium">{expectedDuration}s</span>
            </span>
          </div>

          {/* Progress Bar */}
          <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-purple-600 transition-all duration-300 ease-out rounded-full"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>

          <div className="mt-2 text-right text-xs text-gray-500">
            {Math.round(progress)}% complete
          </div>
        </div>

        {/* Steps */}
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 space-y-3">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            return (
              <div
                key={index}
                className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                  isCurrent ? 'bg-gray-800' : ''
                }`}
              >
                <div className="flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-700" />
                  )}
                </div>
                <span
                  className={`flex-1 ${
                    isCompleted
                      ? 'text-gray-400 line-through'
                      : isCurrent
                      ? 'text-white font-medium'
                      : 'text-gray-600'
                  }`}
                >
                  {step.text}
                </span>
                {isCurrent && (
                  <span className="text-xs text-gray-500">
                    ~{step.duration}s
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer tip */}
        <div className="mt-6 text-center text-sm text-gray-500">
          This usually takes 15-30 seconds. Please wait...
        </div>
      </div>
    </div>
  );
}
