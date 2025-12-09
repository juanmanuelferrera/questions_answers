import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="w-full py-8 flex flex-col items-center justify-center text-center relative z-10 animate-fade-in">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 bg-gradient-to-br from-slate-900 to-slate-800 rounded-full flex items-center justify-center shadow-xl shadow-slate-900/10 text-amber-500">
             <span className="text-xl font-serif italic">V</span>
        </div>
        
        <div>
            <h1 className="text-2xl font-serif text-slate-900 tracking-wide">
            Vedabase <span className="text-slate-400 italic">RAG</span>
            </h1>
        </div>
      </div>
    </header>
  );
};