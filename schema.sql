-- Questions table
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    number TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Traditions table
CREATE TABLE traditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Responses table
CREATE TABLE responses (
    id TEXT PRIMARY KEY,
    question_id INTEGER NOT NULL,
    tradition_id INTEGER NOT NULL,
    opening TEXT NOT NULL,
    historical_development TEXT,
    key_concepts TEXT,
    core_arguments TEXT,
    counter_arguments TEXT,
    textual_foundation TEXT,
    internal_variations TEXT,
    contemporary_applications TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (tradition_id) REFERENCES traditions(id)
);

-- Embeddings table (metadata for vectors stored in Vectorize)
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    response_id TEXT NOT NULL,
    section_type TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES responses(id)
);

-- Indexes for faster queries
CREATE INDEX idx_responses_question ON responses(question_id);
CREATE INDEX idx_responses_tradition ON responses(tradition_id);
CREATE INDEX idx_embeddings_response ON embeddings(response_id);
