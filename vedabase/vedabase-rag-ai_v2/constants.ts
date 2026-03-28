import { SearchFilters } from "./types";

export const DEFAULT_FILTERS: SearchFilters = {
  bookScope: 'All Books',
  sourceCount: 10,
  wordCount: 200,
};

export const SUGGESTED_SEARCHES = [
  {
    title: "Karma Yoga",
    query: "What is the science of Karma Yoga according to Gita?",
    icon: "⚖️"
  },
  {
    title: "Nature of Soul",
    query: "Explain the characteristics of the soul (Atma).",
    icon: "✨"
  },
  {
    title: "Mind Control",
    query: "How can one control the flickering mind?",
    icon: "🧠"
  },
  {
    title: "Duty (Dharma)",
    query: "What is the difference between material and spiritual dharma?",
    icon: "🛡️"
  }
];

export const SEARCH_STEPS = [
  { id: 1, label: "Parsing query semantics..." },
  { id: 2, label: "Scanning 15,000+ verses..." },
  { id: 3, label: "Cross-referencing purports..." },
  { id: 4, label: "Synthesizing final response..." }
];

export const MOCK_HISTORY = [
  "Consciousness vs Matter",
  "Modes of Material Nature",
  "Story of Dhruva Maharaja",
  "Meaning of Renunciation",
  "Krishna's Universal Form",
  "Duties of a King",
  "Process of Bhakti",
  "Origin of the Jiva"
];

export const DAILY_WISDOM = [
  {
    text: "For the soul there is neither birth nor death at any time. He has not come into being, does not come into being, and will not come into being. He is unborn, eternal, ever-existing and primeval.",
    source: "Bhagavad-gita 2.20"
  },
  {
    text: "This material nature, which is one of My energies, is working under My direction, O son of Kuntī, producing all moving and nonmoving beings.",
    source: "Bhagavad-gita 9.10"
  },
  {
    text: "The occupational activities a man performs according to his own position are only so much useless labor if they do not provoke attraction for the message of the Personality of Godhead.",
    source: "Srimad Bhagavatam 1.2.8"
  },
  {
    text: "A person who is not disturbed by the incessant flow of desires—that enter like rivers into the ocean, which is ever being filled but is always still—can alone achieve peace.",
    source: "Bhagavad-gita 2.70"
  }
];