#!/usr/bin/env python3
"""
Initialize the RAG system by creating the FAISS index from knowledge base documents.
Run this script before starting the application for the first time.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import VectorStoreManager
from src.rag.document_processor import load_and_process_documents


def main():
    """Initialize the RAG index."""
    print("=" * 60)
    print("AI Finance Assistant - RAG Initialization")
    print("=" * 60)

    print("\n1. Loading and processing knowledge base documents...")
    documents = load_and_process_documents()
    print(f"   Loaded {len(documents)} document chunks")

    print("\n2. Creating FAISS index...")
    manager = VectorStoreManager()
    manager.create_index(documents, save=True)

    print("\n3. Verifying index...")
    # Test query
    results = manager.similarity_search("What are stocks?", k=3)
    print(f"   Test query returned {len(results)} results")

    if results:
        print(f"   Top result score: {results[0][1]:.3f}")
        print(f"   Top result source: {results[0][0].metadata.get('source', 'unknown')}")

    print("\n" + "=" * 60)
    print("RAG initialization complete!")
    print("You can now run the application with: python run.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
