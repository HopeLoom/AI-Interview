import { InterviewStep } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

interface ProgressTrackerProps {
  steps: InterviewStep[];
  currentStep: number;
}

export function ProgressTracker({ steps, currentStep }: ProgressTrackerProps) {
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl p-4">
      <h3 className="text-lg font-semibold text-slate-100 mb-4">Interview Progress</h3>
      <div className="flex justify-between relative">
        {steps.map((step) => (
          <div
            key={step.id}
            className={cn(
              'progress-bar-step relative z-10 w-10 h-10 flex items-center justify-center rounded-full border-2 text-sm font-medium',
              step.status === 'completed' && 'completed bg-green-500 border-green-500 text-white',
              step.status === 'active' && 'active border-blue-500 bg-blue-500 text-white',
              step.status === 'upcoming' && 'border-slate-500 bg-slate-600 text-slate-300'
            )}
          >
            {step.status === 'completed' ? <Check className="w-5 h-5" /> : step.id}
          </div>
        ))}
      </div>
      <div className="flex justify-between mt-3 text-xs text-slate-400 px-1">
        {steps.map((step) => (
          <div
            key={step.id}
            className={cn(
              'text-center w-10 truncate',
              step.status === 'active' && 'font-medium text-blue-400'
            )}
          >
            {step.name}
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="w-full bg-slate-600 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(currentStep / steps.length) * 100}%` }}
          ></div>
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-400">
          <span>Step {currentStep}</span>
          <span>of {steps.length}</span>
        </div>
      </div>
    </div>
  );
}
