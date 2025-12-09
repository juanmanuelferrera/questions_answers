import React, { useState, useRef, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { SearchInput } from './components/SearchInput';
import { SuggestedSearches } from './components/SuggestedSearches';
import { AnswerSection } from './components/AnswerSection';
import { SourceCard } from './components/SourceCard';
import { ThinkingProcess } from './components/ThinkingProcess';
import { ReadingModal } from './components/ReadingModal';
import { DailyWisdom } from './components/DailyWisdom';
import { searchVedabase } from './services/geminiService';
import { LoadingState, ConversationTurn, SearchFilters, Source } from './types';
import { DEFAULT_FILTERS } from './constants';

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [bottomQuery, setBottomQuery] = useState('');
  const [loadingState, setLoadingState] = useState<LoadingState>(LoadingState.IDLE);
  const [conversation, setConversation] = useState<ConversationTurn[]>([]);
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  
  // Reference to the main scrollable content area
  const mainContentRef = useRef<HTMLDivElement>(null);
  // Reference to the bottom of the list to scroll to
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSearch = async (specificQuery?: string) => {
    const textToSearch = typeof specificQuery === 'string' ? specificQuery : query;
    if (!textToSearch.trim()) return;

    if (specificQuery) {
        setQuery(specificQuery); // Update main input for consistency
        setBottomQuery('');
    }

    setLoadingState(LoadingState.LOADING);
    
    // Smooth scroll to the bottom where thinking will appear
    setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    try {
      const apiPromise = searchVedabase(textToSearch);
      // Wait at least 3 seconds to show the "Thinking" animation fully
      const minDelayPromise = new Promise(resolve => setTimeout(resolve, 3200));
      const [result] = await Promise.all([apiPromise, minDelayPromise]);
      
      const newTurn: ConversationTurn = {
        id: Date.now().toString(),
        query: textToSearch,
        data: result,
        timestamp: Date.now()
      };

      setConversation(prev => [...prev, newTurn]);
      setLoadingState(LoadingState.SUCCESS);
      
      // Scroll slightly to the new answer
      setTimeout(() => {
         messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (error) {
      console.error(error);
      setLoadingState(LoadingState.ERROR);
    }
  };

  const handleNewSearch = () => {
    setQuery('');
    setBottomQuery('');
    setConversation([]);
    setLoadingState(LoadingState.IDLE);
    if (mainContentRef.current) {
        mainContentRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleHistorySelect = (item: string) => {
    // Reset conversation and start new
    setConversation([]);
    setQuery(item);
    handleSearch(item);
  };

  // Get the latest sources to display in the sidebar
  const activeSources = conversation.length > 0 
    ? conversation[conversation.length - 1].data.sources 
    : [];

  return (
    <div className="flex h-screen bg-[#FAFAFA] text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900 overflow-hidden">
      
      {/* Persistent Left Sidebar (Desktop) */}
      <Sidebar 
        onNewSearch={handleNewSearch} 
        onHistorySelect={handleHistorySelect}
      />

      <ReadingModal 
        source={selectedSource} 
        onClose={() => setSelectedSource(null)} 
      />

      {/* Main Content Area */}
      <div 
        ref={mainContentRef}
        className="flex-1 relative overflow-y-auto overflow-x-hidden scroll-smooth"
      >
        {/* Background Ambience */}
        <div className="absolute inset-0 pointer-events-none z-0">
          {conversation.length === 0 ? (
              <>
                <div className="absolute top-[20%] left-[20%] w-[500px] h-[500px] bg-indigo-200/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
                <div className="absolute top-[20%] right-[20%] w-[500px] h-[500px] bg-amber-200/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
              </>
          ) : (
              /* Subtle background for results mode */
              <div className="fixed top-0 w-full h-32 bg-gradient-to-b from-white to-transparent pointer-events-none"></div>
          )}
        </div>

        <div className={`relative z-10 container mx-auto px-4 md:px-12 transition-all duration-700 ${conversation.length === 0 ? 'pt-12 pb-20' : 'pt-8 pb-32'}`}>
          
          {/* Mobile Header */}
          <div className="md:hidden">
            <Header />
          </div>

          {/* LANDING PAGE STATE */}
          {conversation.length === 0 && loadingState === LoadingState.IDLE && (
              <div className="flex flex-col items-center max-w-3xl mx-auto mt-4 md:mt-16">
                <DailyWisdom />
                <SearchInput 
                  query={query} 
                  setQuery={setQuery} 
                  onSearch={() => handleSearch()} 
                  loading={false}
                  filters={filters}
                  setFilters={setFilters}
                  onClear={handleNewSearch}
                />
                <SuggestedSearches onSelect={(q) => { setQuery(q); handleSearch(q); }} />
              </div>
          )}

          {/* CONVERSATION STREAM */}
          {(conversation.length > 0 || loadingState === LoadingState.LOADING) && (
              <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 mt-4">
                  
                  {/* LEFT COLUMN: MAIN STREAM */}
                  <div className="lg:col-span-8">
                      
                      {/* Mapping through history */}
                      {conversation.map((turn, index) => (
                        <div key={turn.id} className="mb-20 animate-fade-in">
                             {/* Turn Header */}
                             <div className="flex items-center gap-4 mb-8 border-b border-slate-100 pb-6">
                                <div className="w-10 h-10 bg-slate-100 text-slate-500 rounded-full flex items-center justify-center font-bold text-sm shadow-sm">
                                    Q
                                </div>
                                <h2 className="text-2xl md:text-3xl font-serif text-slate-900 leading-tight">
                                    {turn.query}
                                </h2>
                             </div>

                             <AnswerSection 
                                query={turn.query}
                                answer={turn.data.answer}
                                sources={turn.data.sources} 
                                relatedTopics={turn.data.relatedTopics}
                                onTopicClick={(topic) => handleSearch(topic)}
                             />
                        </div>
                      ))}

                      {/* Loading State Indicator */}
                      {loadingState === LoadingState.LOADING && (
                          <div className="mb-20">
                              <div className="flex items-center gap-4 mb-8 border-b border-slate-100 pb-6 opacity-50">
                                <div className="w-10 h-10 bg-slate-100 rounded-full"></div>
                                <h2 className="text-2xl font-serif text-slate-900">{query || bottomQuery}</h2>
                             </div>
                             <ThinkingProcess />
                          </div>
                      )}

                      {/* Spacer for auto-scroll */}
                      <div ref={messagesEndRef}></div>

                      {/* Follow Up Search (Sticky Bottom or Inline?) Inline is better for flow */}
                      {loadingState === LoadingState.SUCCESS && (
                          <div className="mt-8 pt-8 border-t-2 border-slate-100/50">
                              <div className="relative flex items-center bg-white rounded-2xl border border-slate-200 shadow-lg shadow-indigo-100/50 focus-within:ring-2 focus-within:ring-indigo-100 transition-all p-2">
                                  <input 
                                      type="text" 
                                      className="w-full bg-transparent px-5 py-4 text-lg text-slate-800 focus:outline-none placeholder:text-slate-400"
                                      placeholder="Ask a follow-up question..."
                                      value={bottomQuery}
                                      onChange={(e) => setBottomQuery(e.target.value)}
                                      onKeyDown={(e) => e.key === 'Enter' && handleSearch(bottomQuery)}
                                  />
                                  <button 
                                      onClick={() => handleSearch(bottomQuery)}
                                      className="mr-2 p-3 rounded-xl bg-slate-900 hover:bg-indigo-600 text-white transition-colors shadow-md"
                                  >
                                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                                      </svg>
                                  </button>
                              </div>
                              <p className="text-center text-slate-400 text-xs mt-4 uppercase tracking-widest">
                                  Vedabase AI can make mistakes. Verify with sastra.
                              </p>
                          </div>
                      )}
                  </div>

                  {/* RIGHT COLUMN: SOURCES SIDEBAR (Sticky) */}
                  <div className="lg:col-span-4 lg:border-l lg:border-slate-100 lg:pl-12 hidden lg:block">
                      <div className="sticky top-8 transition-all duration-500">
                          {activeSources.length > 0 ? (
                            <>
                              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
                                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                                  </svg>
                                  Relevant Sources
                              </h3>
                              <div className="space-y-4 max-h-[85vh] overflow-y-auto pr-2 custom-scrollbar">
                                  {activeSources.map((source, index) => (
                                      <SourceCard 
                                          key={index} 
                                          source={source} 
                                          onClick={() => setSelectedSource(source)}
                                      />
                                  ))}
                              </div>
                            </>
                          ) : (
                             <div className="h-full flex items-start justify-center pt-20">
                                <p className="text-slate-300 text-sm italic text-center px-8">
                                    Sources for your inquiry will appear here.
                                </p>
                             </div>
                          )}
                      </div>
                  </div>

              </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default App;