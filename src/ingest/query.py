#!/usr/bin/env python3
"""
Blender 5.1 API Documentation Query Tool
With improved search accuracy and result filtering.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Any, List, Tuple, Dict

import chromadb
import ollama
import tomllib
from src.core.config import AppConfig, get_appconfig
from src.core.db import db_init, db_init_hc
# ============================================================================
# Query Preprocessing (FIXED - Match Document Cleaning!)
# ============================================================================

def preprocess_query(query: str) -> str:
    """Preprocess query text identically to document cleaning."""
    # Normalize whitespace but preserve structure
    lines = []
    for line in query.split('\n'):
        stripped = line.strip()
        if stripped:  # Remove empty lines
            lines.append(line)
    
    return '\n'.join(lines).strip()


def calculate_keyword_score(query: str, document_text: str) -> float:
    """Calculate keyword overlap score (0-1)."""
    query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
    doc_keywords = set(re.findall(r'\b\w+\b', document_text.lower()))
    
    if not query_keywords or not doc_keywords:
        return 0.0
    
    # Jaccard similarity for keyword overlap
    intersection = len(query_keywords & doc_keywords)
    union = len(query_keywords | doc_keywords)
    
    return intersection / union


# ============================================================================
# Search Functions (FIXED - With Threshold & Keyword Matching!)
# ============================================================================

def query_db(config, collection, query: str) -> List[Dict]:
    """Query the database with improved accuracy."""
    
    # Preprocess query identically to documents
    processed_query = preprocess_query(query)
    
    # Get embeddings for the query
    try:
        response = ollama.embed(
            model=config.llm.MODEL_NAME, 
            input=[processed_query]
        )
        query_embedding = response['embeddings'][0]
    except Exception as e:
        print(f"❌ Failed to embed query: {e}")
        return []
    
    # Get more candidates initially for filtering
    total_results = min(config.query.TOTAL_RESULTS * 2, 50)
    similarity_threshold = config.query.SIMILARITY_THRESHOLD
    content_length = config.query.CONTENT_LENGTH
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=total_results,
        include=["documents", "metadatas", "distances"]
    )
    
    final_results: List[Dict] = []
    
    if not results or len(results.get("documents", [[]])) == 0:
        print("\n❌ No matches found in database.")
        return []
    
    for i, doc in enumerate(results["documents"][0]):
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i] if "metadatas" in results and len(results["metadatas"]) > 0 else {}
        
        # Convert distance to similarity score (lower distance = higher similarity)
        similarity_score = 1.0 / (1.0 + distance) if distance >= 0 else 0.5
        
        # Calculate keyword overlap for hybrid scoring
        keyword_score = calculate_keyword_score(processed_query, doc)
        
        # Hybrid score: 70% semantic, 30% keyword matching
        final_score = 0.7 * similarity_score + 0.3 * keyword_score
        
        # Filter by threshold
        if final_score < similarity_threshold:
            continue
        
        result_entry = {
            "text": doc[:content_length] + ("..." if len(doc) > content_length else ""),
            "similarity_score": round(similarity_score, 3),
            "keyword_score": round(keyword_score, 3),
            "hybrid_score": round(final_score, 3),
            "source": metadata.get("source", "unknown"),
            "format": metadata.get("format", "unknown"),
            "chunk": metadata.get("chunk", 0)
        }
        
        final_results.append(result_entry)
    
    # Sort by hybrid score descending
    final_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    
    return final_results


def display_results(results: List[Dict], query: str) -> None:
    """Display search results in formatted output."""
    
    if not results:
        print("\n❌ No relevant matches found.")
        print(f"💡 Tip: Try more specific queries like 'bpy.ops.object.primitive_add'")
        return
    
    print(f"\n{'='*70}")
    print(f"🔍 Query: '{query}'")
    print(f"✅ Found {len(results)} relevant matches:")
    print(f"{'='*70}\n")
    
    for i, result in enumerate(results, 1):
        print(f"[{i}] Score: {result['hybrid_score']:.3f} (similarity: {result['similarity_score']:.3f}, keywords: {result['keyword_score']:.3f})")
        print(f"    Format: {result['format']} | Source: {Path(result['source']).name}")
        print(f"    Content:\n    {'─'*60}")
        
        # Split long text for readability
        content = result["text"]
        lines = content.split('\n')[:8]  # Show first 8 lines
        
        for line in lines:
            if len(line) > 70:
                print(f"    {line[:67]}...")
            else:
                print(f"    {line}")
        
        print()

def verify_integrity(config: AppConfig) -> None:
    """Verify database integrity (add this function)."""
    
    client, collection = db_init(config.db)
    
    print(f"\n🔍 Database Integrity Check:")
    print(f"   ├─ Total records in DB: {collection.count()}")
    
    results = collection.get(include=["metadatas"])
    if "metadatas" in results:
        sources = set()
        for metadata in results["metadatas"]:
            if isinstance(metadata, dict) and "source" in metadata:
                sources.add(metadata["source"])
        
        print(f"   ├─ Unique source files: {len(sources)}")
        
        # Check for your specific markdown file
        target_file = "01_scene_objects.py.md"
        matching = [s for s in sources if target_file in s]
        print(f"   └─ '{target_file}' found: {len(matching)} files")

# ============================================================================
# Main Entry Point (FIXED - With Better Query Handling!)
# ============================================================================

def main() -> None:
    """Main entry point."""
    
    config = get_appconfig()
    
    if not config:
        return
    
    # Handle --verify flag FIRST before querying
    args = sys.argv[1:]
    
    if "--verify" in args or "-v" in args:
        verify_integrity(config)  # Add this function (see below)
        return
    
    # client, collection = db_init(config.db)
    client, collection = db_init(config.db)
    
    # Get query from command line or use default for testing
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("🔍 Enter search query (or press Ctrl+D to exit):")
        try:
            query = input("> ").strip()
        except EOFError:
            return
    
    if not query:
        print("❌ No query provided.")
        return
    
    # Display results
    display_results(query_db(config, collection, query), query)

if __name__ == "__main__":
    main()
