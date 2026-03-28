# RAG System Setup Instructions

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (for embeddings)
- Anthropic API key (for Claude queries)

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 3. Create the database

```bash
python3 create_database.py
```

This creates `philosophical_traditions.db` with the required schema.

### 4. Import responses

```bash
python3 parse_and_import_new_format.py
```

This parses Question 1.24 and 1.25 files and imports them into the database.

### 5. Generate embeddings

```bash
python3 generate_embeddings.py
```

This generates vector embeddings for all responses using OpenAI's text-embedding-3-small model.
**Cost**: ~$0.38 for all responses in Questions 1.24-1.25

### 6. Query the system

```bash
python3 query_rag.py "What is the nature of time?"
```

**Cost**: ~$0.03 per query (embedding + Claude API)

## File Structure

```
.
├── create_database.py              # Database schema creation
├── parse_and_import_new_format.py  # Import responses from text files
├── generate_embeddings.py          # Generate vector embeddings
├── query_rag.py                    # RAG query interface
├── requirements.txt                # Python dependencies
├── .env                            # API keys (create this)
├── philosophical_traditions.db     # SQLite database (generated)
└── question_1.2*.txt               # Source text files
```

## Usage Examples

### Basic query
```bash
python3 query_rag.py "How do different traditions understand consciousness?"
```

### With custom parameters
```python
from query_rag import query_rag_system

result = query_rag_system(
    question="What is the nature of reality?",
    top_k=5,  # Number of relevant chunks to retrieve
    traditions_filter=["Catholic", "Buddhist", "Hindu"]  # Optional filter
)

print(result['answer'])
print(result['sources'])
```

## Cost Breakdown

- **Setup (one-time)**:
  - Generate embeddings: ~$0.38 for Questions 1.24-1.25 (~370 responses)

- **Per query**:
  - Query embedding: $0.00002
  - Claude Sonnet 4 synthesis: ~$0.03
  - **Total**: ~$0.03 per query

## Troubleshooting

### Missing API keys
```
Error: ANTHROPIC_API_KEY not found
```
**Solution**: Create `.env` file with your API keys

### Import errors
```
No module named 'anthropic'
```
**Solution**: Run `pip install -r requirements.txt`

### Database not found
```
Error: no such table: responses
```
**Solution**: Run `python3 create_database.py` first
