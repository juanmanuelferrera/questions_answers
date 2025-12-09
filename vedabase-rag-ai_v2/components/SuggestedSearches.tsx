import React from 'react';
import { SUGGESTED_SEARCHES } from '../constants';

interface SuggestedSearchesProps {
  onSelect: (query: string) => void;
}

export const SuggestedSearches: React.FC<SuggestedSearchesProps> = ({ onSelect }) => {
  return (
    <div className="w-full max-w-3xl mx-auto mt-12 animate-fade-in delay-100">
      <div className="flex flex-wrap justify-center gap-4">
        {SUGGESTED_SEARCHES.map((item, index) => (
          <button
            key={index}
            onClick={() => onSelect(item.query)}
            className="group px-6 py-3 bg-white/60 backdrop-blur-md border border-slate-200 rounded-full hover:border-indigo-200 hover:bg-white hover:shadow-lg hover:shadow-indigo-100 transition-all duration-300 transform hover:-translate-y-1"
          >
            <span className="text-slate-600 font-medium text-base group-hover:text-indigo-600 transition-colors font-sans">
              {item.title}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};