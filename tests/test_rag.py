#!/usr/bin/env python3
"""Test RAG retrieval to debug why sources are empty."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.retriever import FinanceRetriever

print("=" * 60)
print("Testing RAG Retrieval")
print("=" * 60)

# Create retriever
retriever = FinanceRetriever(top_k=5)

# Test query
query = "What is dollar cost averaging?"
print(f"\nQuery: {query}")

# Get results
results = retriever.retrieve(query)

print(f"\nResults found: {len(results)}")

for idx, result in enumerate(results, 1):
    print(f"\n--- Result {idx} ---")
    print(f"Score: {result['score']:.4f}")
    print(f"Source: {result['source']}")
    print(f"Title: {result['title']}")
    print(f"URL: {result.get('url', 'N/A')}")
    print(f"Content preview: {result['content'][:200]}...")

print("\n" + "=" * 60)
