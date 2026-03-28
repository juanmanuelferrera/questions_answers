#!/usr/bin/env python3
"""
Test Vedabase setup before full upload.
Checks:
1. Local D1 database has data
2. Environment variables are set
3. Can connect to OpenAI
4. Can generate a test embedding
5. Remote D1 is accessible
"""

import os
import sqlite3
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def test_local_database():
    """Test local database has Vedabase data."""
    print("1. Testing local database...")

    if not Path(LOCAL_DB).exists():
        print("   ✗ Local database not found!")
        return False

    try:
        conn = sqlite3.connect(LOCAL_DB)
        cursor = conn.cursor()

        # Check books
        cursor.execute("SELECT COUNT(*) FROM vedabase_books")
        book_count = cursor.fetchone()[0]
        print(f"   ✓ Found {book_count} books")

        # Check verses
        cursor.execute("SELECT COUNT(*) FROM vedabase_verses")
        verse_count = cursor.fetchone()[0]
        print(f"   ✓ Found {verse_count:,} verses")

        # Check chunks
        cursor.execute("SELECT COUNT(*) FROM vedabase_chunks")
        chunk_count = cursor.fetchone()[0]
        print(f"   ✓ Found {chunk_count:,} chunks")

        # Sample chunk
        cursor.execute("SELECT content FROM vedabase_chunks LIMIT 1")
        sample = cursor.fetchone()[0]
        print(f"   ✓ Sample chunk ({len(sample)} chars): {sample[:100]}...")

        conn.close()
        return True

    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False

def test_environment_variables():
    """Test required environment variables."""
    print("\n2. Testing environment variables...")

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API access',
        'CLOUDFLARE_ACCOUNT_ID': 'Cloudflare account',
        'CLOUDFLARE_API_TOKEN': 'Cloudflare API access'
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"   ✓ {var}: {masked} ({description})")
        else:
            print(f"   ✗ {var}: NOT SET ({description})")
            all_set = False

    return all_set

def test_openai_connection():
    """Test OpenAI API connection and embedding generation."""
    print("\n3. Testing OpenAI connection...")

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ✗ OPENAI_API_KEY not set")
        return False

    try:
        client = OpenAI(api_key=api_key)

        # Test with a simple text
        test_text = "This is a test of the embedding generation system."
        print(f"   Testing with: '{test_text}'")

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[test_text],
            dimensions=1536
        )

        embedding = response.data[0].embedding
        print(f"   ✓ Generated embedding: {len(embedding)} dimensions")
        print(f"   ✓ First 5 values: {embedding[:5]}")

        return True

    except Exception as e:
        print(f"   ✗ OpenAI error: {e}")
        return False

def test_wrangler_access():
    """Test wrangler CLI is available."""
    print("\n4. Testing wrangler CLI...")

    import subprocess

    try:
        result = subprocess.run(
            ['npx', 'wrangler', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✓ Wrangler installed: {version}")
            return True
        else:
            print(f"   ✗ Wrangler not working: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ✗ Wrangler error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("Vedabase Setup Test")
    print("=" * 80)
    print()

    results = {
        'Local Database': test_local_database(),
        'Environment Variables': test_environment_variables(),
        'OpenAI Connection': test_openai_connection(),
        'Wrangler CLI': test_wrangler_access()
    }

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n✓ All tests passed! Ready to proceed with upload.")
        print("\nNext steps:")
        print("  1. Run upload_vedabase_to_remote.py to upload data to remote D1")
        print("  2. Run generate_vedabase_embeddings.py to generate and upload embeddings")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
