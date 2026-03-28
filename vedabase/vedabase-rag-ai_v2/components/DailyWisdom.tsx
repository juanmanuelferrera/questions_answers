import React, { useState, useEffect } from 'react';
import { DAILY_WISDOM } from '../constants';

export const DailyWisdom: React.FC = () => {
  const [quote, setQuote] = useState(DAILY_WISDOM[0]);

  useEffect(() => {
    // Randomize quote on mount
    const random = DAILY_WISDOM[Math.floor(Math.random() * DAILY_WISDOM.length)];
    setQuote(random);
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto mb-10 text-center animate-fade-in">
      <div className="relative p-8 rounded-2xl bg-white/40 backdrop-blur-md border border-white/60 shadow-xl shadow-indigo-100/50 overflow-hidden group">
        
        {/* Decorative Quote Mark */}
        <div className="absolute top-4 left-6 text-6xl font-serif text-indigo-200 opacity-50 select-none">“</div>
        
        <div className="relative z-10">
            <p className="text-lg md:text-xl font-serif italic text-slate-700 leading-relaxed mb-4">
            {quote.text}
            </p>
            <div className="flex items-center justify-center gap-2">
                <span className="h-px w-8 bg-indigo-300/50"></span>
                <p className="text-xs font-bold uppercase tracking-widest text-indigo-900/60">
                {quote.source}
                </p>
                <span className="h-px w-8 bg-indigo-300/50"></span>
            </div>
        </div>

        {/* Shimmer Effect */}
        <div className="absolute top-0 -inset-full h-full w-1/2 z-5 block transform -skew-x-12 bg-gradient-to-r from-transparent to-white opacity-40 group-hover:animate-shine" />
      </div>
    </div>
  );
};