import React, { useState, useEffect } from 'react';
import { SEARCH_STEPS } from '../constants';

export const ThinkingProcess: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < SEARCH_STEPS.length - 1 ? prev + 1 : prev));
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-2xl mb-8 animate-fade-in">
      <div className="space-y-3">
        {SEARCH_STEPS.map((step, index) => {
          const isComplete = index < currentStep;
          const isCurrent = index === currentStep;
          
          return (
            <div key={step.id} className="flex items-center gap-4 text-sm font-medium transition-all duration-300">
              <div className="w-6 h-6 flex items-center justify-center">
                 {isComplete ? (
                   <span className="text-emerald-500 text-lg">✓</span>
                 ) : isCurrent ? (
                   <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                 ) : (
                   <div className="w-2 h-2 bg-slate-200 rounded-full"></div>
                 )}
              </div>
              <span className={`
                ${isComplete ? 'text-slate-400' : isCurrent ? 'text-indigo-600' : 'text-slate-300'}
              `}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};