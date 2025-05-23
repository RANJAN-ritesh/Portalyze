import { useEffect, useState } from 'react';

interface GradingProgressProps {
  onComplete: () => void;
}

const steps = [
  'Analyzing repository structure',
  'Checking portfolio sections',
  'Evaluating code quality',
  'Assessing responsiveness',
  'Generating feedback',
];

export function GradingProgress({ onComplete }: GradingProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= steps.length - 1) {
          clearInterval(interval);
          onComplete();
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 space-y-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-4">
            Grading in Progress
          </h2>
        </div>

        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={step}
              className={`flex items-center space-x-3 ${
                index < currentStep
                  ? 'text-green-500'
                  : index === currentStep
                  ? 'text-primary'
                  : 'text-muted-foreground'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  index < currentStep
                    ? 'bg-green-500'
                    : index === currentStep
                    ? 'bg-primary animate-pulse'
                    : 'bg-muted'
                }`}
              >
                {index < currentStep ? (
                  '✓'
                ) : index === currentStep ? (
                  <div className="w-3 h-3 bg-primary-foreground rounded-full" />
                ) : null}
              </div>
              <span>{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 