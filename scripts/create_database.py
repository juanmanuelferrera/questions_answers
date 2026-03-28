# create_database.py
import sqlite3

def create_database(db_path='philosophical_traditions_sample.db'):
    """Create SQLite database with complete schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Questions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        section INTEGER
    )
    """)

    # Traditions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traditions (
        id INTEGER PRIMARY KEY,
        number INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        subcategory TEXT
    )
    """)

    # Responses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY,
        question_id INTEGER NOT NULL,
        tradition_id INTEGER NOT NULL,
        full_text TEXT NOT NULL,
        opening TEXT,
        historical_development TEXT,
        key_concepts TEXT,
        core_arguments TEXT,
        counter_arguments TEXT,
        textual_foundation TEXT,
        internal_variations TEXT,
        contemporary_applications TEXT,
        word_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (tradition_id) REFERENCES traditions(id),
        UNIQUE(question_id, tradition_id)
    )
    """)

    # Embeddings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY,
        response_id INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_index INTEGER,
        section_type TEXT,
        embedding BLOB NOT NULL,
        FOREIGN KEY (response_id) REFERENCES responses(id)
    )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_response ON embeddings(response_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_question ON responses(question_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_tradition ON responses(tradition_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_both ON responses(question_id, tradition_id)")

    conn.commit()
    conn.close()
    print("✅ Database created successfully!")
    print(f"   Location: {db_path}")

if __name__ == '__main__':
    create_database()
