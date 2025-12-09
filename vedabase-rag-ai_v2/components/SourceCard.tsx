import React from 'react';
import { Source } from '../types';

interface SourceCardProps {
  source: Source;
  onClick: () => void;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, onClick }) => {
  return (
    <div 
      onClick={onClick}
      className="group cursor-pointer bg-white rounded-xl p-4 border border-slate-100 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-300 relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-indigo-50 to-transparent rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>

      <div className="relative z-10">
        <p className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">
            {source.book}
        </p>
        <h4 className="font-serif font-bold text-slate-900 text-lg mb-2 group-hover:text-indigo-700 transition-colors">
            {source.chapterVerse}
        </h4>
        <p className="text-slate-500 text-sm leading-relaxed line-clamp-3">
            {source.translation}
        </p>
        
        <div className="mt-3 flex items-center justify-between">
            <div className={`
              text-[10px] font-bold px-2 py-0.5 rounded-full
              ${source.relevance > 90 
                ? 'bg-emerald-50 text-emerald-600' 
                : 'bg-amber-50 text-amber-600'
              }
            `}>
               {Math.floor(source.relevance)}% Match
            </div>
            <span className="text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                  <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
                </svg>
            </span>
        </div>
      </div>
    </div>
  );
};