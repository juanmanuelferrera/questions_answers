import React from 'react';
import { Source } from '../types';

interface ReadingModalProps {
  source: Source | null;
  onClose: () => void;
}

export const ReadingModal: React.FC<ReadingModalProps> = ({ source, onClose }) => {
  if (!source) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal Content */}
      <div className="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-slide-up">
        
        {/* Header */}
        <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-white z-10">
          <div>
            <h3 className="font-serif text-2xl font-bold text-slate-900">{source.book}</h3>
            <p className="text-indigo-600 font-bold uppercase tracking-widest text-xs mt-1">{source.chapterVerse}</p>
          </div>
          <button 
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-slate-50 hover:bg-slate-100 flex items-center justify-center transition-colors text-slate-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-8 overflow-y-auto custom-scrollbar">
          
          {source.sanskrit && (
            <div className="mb-8 p-6 bg-amber-50 rounded-xl text-center border border-amber-100">
              <p className="font-serif italic text-xl text-slate-800 leading-loose">
                {source.sanskrit}
              </p>
            </div>
          )}

          <div className="prose prose-lg max-w-none text-slate-700">
            <h4 className="font-sans text-sm font-bold uppercase text-slate-400 mb-3 tracking-widest">Translation</h4>
            <p className="font-serif text-xl leading-relaxed text-slate-900 mb-8">
              {source.translation}
            </p>

            <h4 className="font-sans text-sm font-bold uppercase text-slate-400 mb-3 tracking-widest">Purport</h4>
            <p className="text-base leading-7 text-slate-600">
              {source.purport || "In this verse, the distinct nature of the constitutional position is described. One must understand that semantic interpretation alone is insufficient; one requires the guidance of a bona fide spiritual master to penetrate the mystery of this conclusion. The material energy is vast, yet the spiritual energy is subtler and more potent."}
              <br /><br />
              (This is simulated purport text to demonstrate the reading modal functionality. In a real implementation, this would contain the full commentary by Srila Prabhupada.)
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 py-4 bg-slate-50 border-t border-slate-100 text-right">
          <button 
            onClick={onClose}
            className="px-6 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors"
          >
            Done Reading
          </button>
        </div>
      </div>
    </div>
  );
};