import React from 'react';
import { SearchFilters } from '../types';

interface SearchInputProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
  loading: boolean;
  filters: SearchFilters;
  setFilters: React.Dispatch<React.SetStateAction<SearchFilters>>;
  onClear: () => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({ 
  query, 
  setQuery, 
  onSearch, 
  loading,
  filters,
  setFilters
}) => {
  return (
    <div className="w-full max-w-4xl mx-auto relative z-20 group">
      {/* Ambient Glow */}
      <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full opacity-20 blur-2xl group-hover:opacity-30 transition duration-1000 group-hover:blur-3xl"></div>
      
      <div className="relative flex items-center bg-white rounded-full p-3 shadow-2xl shadow-indigo-200/40 transition-all ring-1 ring-slate-100 focus-within:ring-2 focus-within:ring-indigo-100">
           
           <div className="pl-6 pr-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-8 h-8">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
           </div>

           <input
              type="text"
              className="w-full bg-transparent text-slate-900 px-2 py-4 text-2xl md:text-3xl font-serif placeholder:font-sans placeholder:text-slate-300 placeholder:font-light focus:outline-none"
              placeholder="Inquire into the Absolute Truth..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !loading && onSearch()}
              disabled={loading}
              autoFocus
           />

           <button
             onClick={onSearch}
             disabled={loading || !query.trim()}
             className={`
               hidden md:flex ml-4 px-10 py-5 rounded-full font-sans font-bold text-base tracking-wider text-white transition-all items-center gap-3
               ${loading || !query.trim() 
                 ? 'bg-slate-100 text-slate-300 cursor-not-allowed' 
                 : 'bg-slate-900 hover:bg-indigo-600 shadow-xl shadow-slate-900/20 hover:shadow-indigo-500/30 transform hover:-translate-y-0.5'
               }
             `}
           >
             {loading ? (
                <span className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-white rounded-full animate-bounce"></span>
                    Thinking
                </span>
             ) : (
                <>
                Synthesize
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
                </>
             )}
           </button>
      </div>

       {/* Mobile Button */}
       <button
             onClick={onSearch}
             disabled={loading || !query.trim()}
             className={`
               md:hidden w-full mt-6 px-6 py-5 rounded-2xl font-bold text-lg text-white transition-all shadow-lg
               ${loading || !query.trim() ? 'bg-slate-200 text-slate-400' : 'bg-slate-900'}
             `}
           >
             Search
      </button>

       {/* Elegant Minimal Filters */}
       <div className="mt-10 flex justify-center gap-10 animate-fade-in">
            <label className="flex items-center gap-3 cursor-pointer group">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 group-hover:scale-125 transition-transform shadow-sm shadow-indigo-300"></span>
                <select 
                  className="bg-transparent text-slate-500 text-base font-medium focus:outline-none cursor-pointer hover:text-indigo-600 transition-colors"
                  value={filters.bookScope}
                  onChange={(e) => setFilters(prev => ({...prev, bookScope: e.target.value}))}
                >
                  <option>All Scriptures</option>
                  <option>Bhagavad-gita</option>
                  <option>Srimad Bhagavatam</option>
                </select>
            </label>
            
            <label className="flex items-center gap-3 cursor-pointer group">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 group-hover:scale-125 transition-transform shadow-sm shadow-amber-300"></span>
                <select 
                  className="bg-transparent text-slate-500 text-base font-medium focus:outline-none cursor-pointer hover:text-amber-600 transition-colors"
                  value={filters.sourceCount}
                  onChange={(e) => setFilters(prev => ({...prev, sourceCount: Number(e.target.value)}))}
                >
                  <option value={10}>Balanced View</option>
                  <option value={20}>Deep Research</option>
                </select>
            </label>
       </div>

    </div>
  );
};