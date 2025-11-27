-- Add Vedabase tables to existing philosophy-db
-- These tables work alongside existing philosophical traditions tables

-- Books table (Bhagavad Gita, Srimad Bhagavatam, etc.)
CREATE TABLE IF NOT EXISTS vedabase_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,  -- 'bg', 'sb1', 'sb2', etc.
    name TEXT NOT NULL,          -- 'Bhagavad Gita', 'Srimad Bhagavatam Canto 1'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verses table (main verse metadata)
CREATE TABLE IF NOT EXISTS vedabase_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chapter TEXT,                -- 'Chapter 2', 'Part 1 - Chapter 3', etc.
    verse_number TEXT NOT NULL,  -- '2.13', 'TEXT 1', etc.
    sanskrit TEXT,               -- Sanskrit verse
    synonyms TEXT,               -- Word-for-word translations
    translation TEXT,            -- English translation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES vedabase_books(id)
);

-- Chunks table (for RAG - splits purports into paragraphs)
CREATE TABLE IF NOT EXISTS vedabase_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verse_id INTEGER NOT NULL,
    chunk_type TEXT NOT NULL,    -- 'verse_text' or 'purport_paragraph'
    chunk_index INTEGER,         -- For purports: paragraph number (1, 2, 3...)
    content TEXT NOT NULL,       -- The actual text content
    word_count INTEGER,          -- For tracking chunk size
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (verse_id) REFERENCES vedabase_verses(id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_vedabase_verses_book ON vedabase_verses(book_id);
CREATE INDEX IF NOT EXISTS idx_vedabase_verses_chapter ON vedabase_verses(chapter);
CREATE INDEX IF NOT EXISTS idx_vedabase_chunks_verse ON vedabase_chunks(verse_id);
CREATE INDEX IF NOT EXISTS idx_vedabase_chunks_type ON vedabase_chunks(chunk_type);

-- Insert initial books
INSERT OR IGNORE INTO vedabase_books (code, name) VALUES
    ('bg', 'Bhagavad Gita'),
    ('sb1', 'Srimad Bhagavatam Canto 1'),
    ('sb2', 'Srimad Bhagavatam Canto 2'),
    ('sb3', 'Srimad Bhagavatam Canto 3'),
    ('kb', 'Krishna Book'),
    ('cc1', 'Caitanya Caritamrita Adi-lila'),
    ('cc2', 'Caitanya Caritamrita Madhya-lila'),
    ('cc3', 'Caitanya Caritamrita Antya-lila');
