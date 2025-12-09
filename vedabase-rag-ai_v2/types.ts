export interface Source {
  book: string;
  chapterVerse: string;
  sanskrit?: string;
  translation: string;
  purport?: string; // Added for the modal view
  relevance: number;
}

export interface SearchResponse {
  answer: string;
  sources: Source[];
  relatedTopics: string[];
}

export interface ConversationTurn {
  id: string;
  query: string;
  data: SearchResponse;
  timestamp: number;
}

export enum LoadingState {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR'
}

export interface SearchFilters {
  bookScope: string;
  sourceCount: number;
  wordCount: number;
}