import React from 'react';
import { MOCK_HISTORY } from '../constants';

interface SidebarProps {
  onNewSearch: () => void;
  onHistorySelect: (item: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNewSearch, onHistorySelect }) => {
  return (
    <aside className="hidden md:flex flex-col w-72 h-full bg-white border-r border-slate-100 flex-shrink-0 z-50">
      {/* Branding Area */}
      <div className="p-6 pb-2">
        <div 
          className="flex items-center gap-3 mb-8 cursor-pointer group" 
          onClick={onNewSearch}
        >
           <div className="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center text-white font-serif italic shadow-lg shadow-indigo-100 group-hover:scale-105 transition-transform">
             V
           </div>
           <span className="font-serif font-bold text-xl text-slate-900 tracking-tight">
             Vedabase <span className="text-indigo-500 font-sans font-normal text-xs uppercase tracking-widest ml-1">AI</span>
           </span>
        </div>

        {/* Primary CTA */}
        <button 
          onClick={onNewSearch}
          className="w-full flex items-center gap-3 px-4 py-3 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-indigo-200 transition-all group active:scale-95"
        >
          <div className="p-1.5 rounded-lg bg-slate-50 group-hover:bg-indigo-50 text-slate-500 group-hover:text-indigo-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
            </svg>
          </div>
          <span className="font-medium text-slate-700">New Inquiry</span>
        </button>
      </div>

      {/* Navigation / History */}
      <div className="flex-1 overflow-y-auto px-4 py-4 custom-scrollbar">
        
        <div className="mb-8">
            <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Today</h3>
            <div className="space-y-1">
                {MOCK_HISTORY.slice(0, 3).map((item, i) => (
                    <button 
                        key={i} 
                        onClick={() => onHistorySelect(item)}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 transition-all text-slate-600 text-sm truncate group flex items-center justify-between"
                    >
                        <span className="truncate">{item}</span>
                    </button>
                ))}
            </div>
        </div>

        <div className="mb-8">
            <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Previous 7 Days</h3>
            <div className="space-y-1">
                {MOCK_HISTORY.slice(3, 8).map((item, i) => (
                    <button 
                        key={i} 
                        onClick={() => onHistorySelect(item)}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 transition-all text-slate-600 text-sm truncate group flex items-center justify-between"
                    >
                        <span className="truncate">{item}</span>
                    </button>
                ))}
            </div>
        </div>
      </div>

      {/* Footer / User */}
      <div className="p-4 border-t border-slate-100">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors text-slate-600">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-400 to-purple-400"></div>
            <div className="flex-1 text-left">
                <p className="text-sm font-bold text-slate-900">Guest User</p>
                <p className="text-xs text-slate-400">Settings</p>
            </div>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-slate-400">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
            </svg>
        </button>
      </div>
    </aside>
  );
};