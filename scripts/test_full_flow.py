#!/usr/bin/env python3
import requests
import json

QUERY_WORKER = "https://vedabase-rag.joanmanelferrera-400.workers.dev"
SYNTHESIS_WORKER = "https://philosophy-rag-synthesis.joanmanelferrera-400.workers.dev"

# 1. Search
print("1. Searching...")
search_response = requests.post(QUERY_WORKER, json={
    "query": "What is the soul?",
    "topK": 3
})

print(f"Search status: {search_response.status_code}")

if search_response.status_code != 200:
    print(f"Search failed: {search_response.text}")
    exit(1)

search_data = search_response.json()
print(f"Found {len(search_data['results'])} results\n")

# 2. Synthesize
print("2. Synthesizing...")
sources = [{
    "verse": r["verse"],
    "chunkType": r["chunkType"],
    "chunkText": r["chunkText"],
    "score": r["score"]
} for r in search_data["results"]]

synthesis_response = requests.post(SYNTHESIS_WORKER, json={
    "query": "What is the soul?",
    "sources": sources,
    "wordLimit": 200
})

print(f"Synthesis status: {synthesis_response.status_code}")

if synthesis_response.status_code != 200:
    print(f"Synthesis failed: {synthesis_response.text}")
    exit(1)

synthesis_data = synthesis_response.json()
print(f"\nSynthesis:\n{synthesis_data['synthesis']}")
