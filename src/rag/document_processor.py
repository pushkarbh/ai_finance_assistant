"""
Document processing module for the RAG system.
Handles loading, chunking, and processing knowledge base documents.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.config import get_config


class DocumentProcessor:
    """
    Processes documents from the knowledge base for the RAG system.
    Handles loading markdown files and chunking them appropriately.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize the document processor.

        Args:
            chunk_size: Size of text chunks (default from config)
            chunk_overlap: Overlap between chunks (default from config)
        """
        config = get_config()

        self.chunk_size = chunk_size or config.rag.chunk_size
        self.chunk_overlap = chunk_overlap or config.rag.chunk_overlap
        self.knowledge_base_path = config.knowledge_base_path

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
            length_function=len
        )

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            try:
                frontmatter_str = match.group(1)
                remaining_content = match.group(2)
                metadata = yaml.safe_load(frontmatter_str) or {}
                return metadata, remaining_content
            except yaml.YAMLError:
                # If YAML parsing fails, return empty metadata
                return {}, content

        return {}, content

    def load_documents(
        self,
        directory: Optional[Path] = None
    ) -> List[Document]:
        """
        Load all markdown documents from the knowledge base.

        Args:
            directory: Directory to load from (default: knowledge_base_path)

        Returns:
            List of Document objects
        """
        if directory is None:
            directory = self.knowledge_base_path

        documents = []

        if not directory.exists():
            raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

        for file_path in sorted(directory.glob("*.md")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()

                # Try to parse YAML frontmatter
                frontmatter, content = self._parse_frontmatter(raw_content)

                # Extract title from frontmatter or first line
                if frontmatter.get("title"):
                    title = frontmatter["title"]
                else:
                    lines = content.split('\n')
                    title = lines[0].replace('#', '').strip() if lines else file_path.stem

                # Build metadata - prefer frontmatter values
                metadata = {
                    "source": frontmatter.get("source", str(file_path.name)),
                    "title": title,
                    "file_path": str(file_path),
                    "category": frontmatter.get("category", self._extract_category(file_path.stem))
                }

                # Add URL if present in frontmatter (for scraped articles)
                if frontmatter.get("url"):
                    metadata["url"] = frontmatter["url"]
                else:
                    # For local knowledge base files, create a reference link
                    # This helps users identify the source document
                    file_name = file_path.name
                    metadata["url"] = f"#knowledge-base-{file_path.stem}"
                    metadata["source_type"] = "knowledge_base"

                # Add scraped date if present
                if frontmatter.get("scraped_date"):
                    metadata["scraped_date"] = frontmatter["scraped_date"]

                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)

            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue

        return documents

    def _extract_category(self, filename: str) -> str:
        """
        Extract category from filename.

        Args:
            filename: Filename without extension

        Returns:
            Category string
        """
        # Map filename prefixes to categories
        category_map = {
            "stocks": "investing_basics",
            "rsus": "stock_compensation",
            "etfs": "investment_vehicles",
            "mutual": "investment_vehicles",
            "bonds": "fixed_income",
            "diversification": "portfolio_management",
            "retirement": "retirement_planning",
            "risk": "risk_management",
            "dollar": "investment_strategies",
            "compound": "financial_concepts",
            "market": "market_analysis",
            "emergency": "financial_planning",
            "capital": "taxation",
            "dividends": "income_investing",
            "asset": "portfolio_management",
            "financial": "financial_planning",
            "common": "education",
            "glossary": "reference",
            "reits": "investment_vehicles",
            "expense": "fund_selection",
            "investment": "account_types"
        }

        filename_lower = filename.lower()
        for key, category in category_map.items():
            if key in filename_lower:
                return category

        return "general"

    def chunk_documents(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """
        Split documents into chunks for embedding.

        Args:
            documents: List of documents to chunk

        Returns:
            List of chunked documents
        """
        chunked_docs = []

        for doc in documents:
            chunks = self._splitter.split_documents([doc])

            # Add chunk index to metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(chunks)
                chunked_docs.append(chunk)

        return chunked_docs

    def process_knowledge_base(
        self,
        directory: Optional[Path] = None
    ) -> List[Document]:
        """
        Load and process all documents from the knowledge base.

        Args:
            directory: Directory to process (default: knowledge_base_path)

        Returns:
            List of processed, chunked documents
        """
        # Load documents
        documents = self.load_documents(directory)
        print(f"Loaded {len(documents)} documents from knowledge base")

        # Chunk documents
        chunked_docs = self.chunk_documents(documents)
        print(f"Created {len(chunked_docs)} chunks")

        return chunked_docs


def load_and_process_documents(
    directory: Optional[Path] = None
) -> List[Document]:
    """
    Convenience function to load and process documents.

    Args:
        directory: Directory to process

    Returns:
        List of processed documents
    """
    processor = DocumentProcessor()
    return processor.process_knowledge_base(directory)
