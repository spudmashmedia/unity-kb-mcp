#!/usr/bin/env python3
"""
Multi-Format Document Ingestion Pipeline for Unity API Documentation
With orphan prevention and deduplication support.
"""

import os
import re
import hashlib
from pathlib import Path
import shutil
from typing import Optional, Any, List, Tuple, Set
import json

import chromadb
from bs4 import BeautifulSoup
import trafilatura
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ollama
from tqdm import tqdm
import tomllib

from src.core.config import AppConfig, IngestOption, DbOption, get_appconfig, get_db_options, get_ingest_options, get_llm_options
from src.core.db import db_init
from src.ingest.parser import get_parser


# GLOBALS
ollama_ctx: Optional[Any] = None
config: Optional[AppConfig] = None

# ============================================================================
# File Hashing & Deduplication (NEW!)
# ============================================================================

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file content for deduplication."""
    sha256 = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()[:16]  # First 16 chars is sufficient for deduplication
    except Exception as e:
        print(f"⚠️ Hash calculation failed for {file_path}: {e}")
        return "unknown_hash"

def generate_unique_id(file_name: str, chunk_index: int, file_hash: str) -> str:
    """Generate unique ID that includes content hash."""
    return f"{file_name}_{chunk_index}_{file_hash}"

# ============================================================================
# Format Detection & File Discovery
# ============================================================================

def detect_file_format(file_path: str) -> str:
    """Detect file format based on extension and content heuristics."""
    ext = Path(file_path).suffix.lower()
    
    if ext in [".html", ".htm"]:
        return "html"
    elif ext in [".md", ".markdown"]:
        return "markdown"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sample = f.read(1024).lower()
            
            if "<html" in sample or "<head>" in sample:
                return "html"
            elif "# " in sample and not ext.startswith("."):
                return "markdown"
    except Exception:
        pass
    
    return "unknown"

def get_all_files(root_path: str) -> List[Tuple[str, str]]:
    """Recursively find all supported files across subdirectories."""
    allowed_extensions = [".html", ".htm", ".md", ".markdown"]
    files: List[Tuple[str, str]] = []
    
    for root, _, filenames in os.walk(root_path):
        for file in filenames:
            ext = Path(file).suffix.lower()
            if ext in allowed_extensions:
                full_path = os.path.join(root, file)
                fmt_type = detect_file_format(full_path)
                if fmt_type != "unknown":
                    files.append((full_path, fmt_type))
    
    return files

# ============================================================================
# Document Ingestion with Orphan Prevention (ENHANCED!)
# ============================================================================

def get_ingestion_state_file(config: dict[str, Any]) -> str:
    """Get path to state tracking file."""
    db_path = config.get("db", {}).get("DB_NAME", config.db.DB_NAME)
    return os.path.join(db_path, "ingestion_state.json")

def load_ingestion_state() -> dict[str, Any]:
    """Load previous ingestion state from disk."""   
    # Try to find the state file in any possible location
    possible_paths = [
        f"{config.db.DB_NAME}/{config.ingest.STATE_FILE_NAME}",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
    
    return {}

def save_ingestion_state(state: dict[str, Any]) -> None:
    """Save ingestion state to disk."""   
    # Save in the same directory as DB if possible
    try:
        with open(f"{config.db.DB_NAME}/{config.ingest.STATE_FILE_NAME}", "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save state file: {e}")

def archive_file(file_path: str, source_root: str, archive_root: str) -> bool:
    """Move processed file to archive safely."""
    try:
        # Calculate relative path from THIS source root (not a common ancestor)
        rel_path = os.path.relpath(file_path, source_root)
        
        # Construct destination path in archive
        dest_file = Path(archive_root) / rel_path
        
        # Ensure parent directories exist
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(file_path, str(dest_file))
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to archive {file_path}: {e}")
        return False

def clear_folder_contents(path: str) -> None:
    """Equivalent to 'rm -rf <path>/*' but safer for Docker volumes."""
    folder = Path(path)
    if not folder.exists(): 
        return
        
    for item in folder.iterdir():
        try:
            if item.is_file():
                item.unlink()  # Remove file
            elif item.is_dir():
                shutil.rmtree(item)  # Remove subfolder recursively
        except Exception as e:
            print(f"⚠️ Failed to remove {item}: {e}")

def check_for_orphans(collection: Any) -> int:
    """Check for and report orphaned chunks."""
    # Get all unique sources currently in database
    existing_sources = set()
    
    try:
        results = collection.get(include=["metadatas"])
        
        if "metadatas" in results:
            for metadata in results["metadatas"]:
                if isinstance(metadata, dict) and "source" in metadata:
                    existing_sources.add(metadata["source"])
    except Exception as e:
        print(f"⚠️ Orphan check failed: {e}")
        return 0
    
    # Count active files from config
    doc_paths = []
    try:
        doc_paths = [p for p in doc_paths if os.path.exists(p)]
    except Exception:
        pass
    
    print(f"\n🔍 Orphan Check:")
    print(f"   ├─ Existing Sources in DB: {len(existing_sources)}")
    
    return len(existing_sources)

def ingest_documents(skip_dedup: bool = False) -> None:
    """Main document ingestion pipeline with orphan prevention."""
    
    # 📚 Get list of document directories from config
    doc_paths = config.ingest.DOC_PATHS
    
    if not isinstance(doc_paths, list) or len(doc_paths) == 0:
        print(f"❌ Error: DOC_PATHS must be a non-empty array in config.toml")
        return

    # 🧠 Initialize ChromaDB (once for all paths)
    try:
        client, collection = db_init(config.db)
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return
    
    # ⚡ Pre-scan ALL source files before ingestion starts
    all_files: List[Tuple[str, str, str, str]] = []  # (file_path, format_type, file_hash, source_root)
    valid_paths = 0
    skipped_duplicate = 0
    
    print(f"\n🔍 Pre-scanning {len(doc_paths)} directories for supported formats...\n")
    
    for doc_path in doc_paths:
        if not os.path.exists(doc_path):
            print(f"⚠️ Warning: Path does not exist, skipping...")
            continue
        
        path_files = get_all_files(doc_path)
        
        # Calculate hash and detect format for each file
        for file_path, fmt_type in path_files:
            file_hash = calculate_file_hash(file_path)
            
            # Check if this exact file content already exists (deduplication)
            if not skip_dedup:
                existing_hashes = load_ingestion_state().get("file_hashes", {})
                
                if file_hash in existing_hashes:
                    print(f"   └─ Skipping duplicate: {os.path.basename(file_path)}")
                    skipped_duplicate += 1
                    continue
            
            all_files.append((file_path, fmt_type, file_hash, doc_path))
        
        valid_paths += 1
    
    # 📊 Report results
    if valid_paths == 0:
        print(f"\n❌ Error: None of the configured paths exist!")
        return
        
    html_count = sum(1 for _, fmt, _, _ in all_files if fmt == "html")
    md_count = sum(1 for _, fmt, _, _ in all_files if fmt == "markdown")
    
    print(f"📁 Found {len(all_files)} files across {valid_paths} directories:")
    print(f"   ├─ HTML:  {html_count}")
    print(f"   ├─ Markdown: {md_count}")
    print(f"   └─ Skipped Duplicates: {skipped_duplicate}\n")
    
    # 🧠 Configure text splitter (only once)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Track ingested files for state persistence
    ingested_hashes: List[str] = []
    
    # 🚀 PROCESS ALL FILES (The Speed Fix)
    for file_path, format_type, file_hash, source_root in tqdm(all_files, desc="Ingesting Docs"):
        parser = get_parser(format_type, config.ingest.CLEAN_ALG)
        
        try:
            print(f"file_path:{file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = parser.parse(f.read())

            if not content or len(content.strip()) < 5:
                print("Something went wrong")
                continue
                
            chunks = splitter.split_text(content)
            
            # 🚀 PROCESS IN BATCHES (The Speed Fix)
            for i in range(0, len(chunks), config.ingest.BATCH_SIZE):
                batch_texts = chunks[i : i + config.ingest.BATCH_SIZE]
                
                try:
                    response = ollama_ctx.embed(
                        model=config.llm.MODEL_NAME, 
                        input=batch_texts
                    )
                    embeddings = response[config.query.RESPONSE_TYPE]
                    
                    # Use hash-based unique IDs (prevents orphans!)
                    ids = [generate_unique_id(file_path, j, file_hash) for j in range(i, i + len(batch_texts))]
                    metadatas = [{
                        "source": file_path, 
                        "chunk": j,
                        "format": format_type,
                        "file_hash": file_hash,  # Store hash for verification
                        "content_length": len(content)
                    } for j in range(i, i + len(batch_texts))]
                    
                    collection.add(
                        documents=batch_texts,
                        ids=ids,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                except Exception as e:
                    print(f"❌ Batch embedding failed for {file_path}: {e}")
                
            ingested_hashes.append(file_hash)
                    
            # Archive File
            if not archive_file(file_path, source_root, config.ingest.ARCHIVE_PATH):
                print(f"⚠️ Warning: File {file_path} failed to archive but was processed.")

        except Exception as e:
            print(f"❌ Error processing {file_path} ({format_type}): {e}")

    # 💾 Save ingestion state (prevents re-processing on restart)
    save_ingestion_state({
        "last_run": str(Path(__file__).resolve()),
        "file_hashes": ingested_hashes,
        "total_files_processed": len(all_files),
        "collection_name": f"{config.db.COLLECTION_NAME}_{config.db.METADATA_VERSION}"
    })

    # Clear /data/raw folder
    for path in doc_paths:
        clear_folder_contents(path)    

    print(f"\n🎉 Ingestion Complete! {collection.count()} total records stored.")
    
    # 🔍 Check for orphans after ingestion
    check_for_orphans(collection)

# ============================================================================
# Cleanup & Maintenance Functions (NEW!)
# ============================================================================

def cleanup_orphaned_chunks(config: AppConfig) -> int:
    """Remove chunks that point to non-existent source files."""
    client, collection = db_init(config.db)

    doc_paths = config.ingest.DOC_PATHS
    
    # Build set of valid sources
    valid_sources = set()
    for path in doc_paths:
        if os.path.exists(path):
            all_files = get_all_files(path)
            for file_path, _ in all_files:
                valid_sources.add(file_path)
    
    print(f"🧹 Checking {len(valid_sources)} source files...")
    
    try:
        results = collection.get(include=["metadatas", "ids"])
        
        if "metadatas" not in results or "ids" not in results:
            return 0
        
        to_delete_ids = []
        orphan_count = 0
        
        for i, metadata in enumerate(results["metadatas"]):
            if isinstance(metadata, dict) and "source" in metadata:
                source = metadata["source"]
                
                # Check if source still exists
                if source not in valid_sources:
                    to_delete_ids.append(results["ids"][i])
                    orphan_count += 1
        
        if to_delete_ids:
            print(f"\n🗑️ Deleting {len(to_delete_ids)} orphaned records...")
            collection.delete(ids=to_delete_ids)
        
        return orphan_count
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 0

def verify_integrity() -> None:
    """Verify database integrity."""

    client, collection = db_init(config.db)

    doc_paths = config.ingest.DOC_PATHS
    
    # Build set of valid sources
    valid_sources = set()
    for path in doc_paths:
        if os.path.exists(path):
            all_files = get_all_files(path)
            for file_path, _ in all_files:
                valid_sources.add(file_path)
    
    print(f"\n🔍 Integrity Check:")
    print(f"   ├─ Valid Source Files: {len(valid_sources)}")
    
    try:
        results = collection.get(include=["metadatas"])
        
        if "metadatas" not in results or "ids" not in results:
            return
        
        existing_sources = set()
        for metadata in results["metadatas"]:
            if isinstance(metadata, dict) and "source" in metadata:
                existing_sources.add(metadata["source"])
        
        print(f"   ├─ Sources in Database: {len(existing_sources)}")
        
        # Check for missing sources
        missing = valid_sources - existing_sources
        extra = existing_sources - valid_sources
        
        if missing:
            print(f"   └─ Missing from DB: {len(missing)} (may need re-ingestion)")
        
        if extra:
            print(f"   ├─ Orphans in DB: {len(extra)}")
            
    except Exception as e:
        print(f"❌ Integrity check failed: {e}")

# ============================================================================
# Main Entry Point with Command Line Options (ENHANCED!)
# ============================================================================

def main() -> None:
    """Main entry point."""
    import sys
    global config, ollama_ctx
    
    print("\n" + "=" * 60)
    print("🚀 Starting Multi-Format Document Ingestion...")
    print("=" * 60 + "\n")
    
    config = get_appconfig()
    
    if not config:
        print(f"⚠️ No configuration found, exiting.")
        return

    if not config.llm:
        print(f"⚠️ No LLM configuration found, exiting.")

    if not config.ingest:
        print(f"⚠️ No Ingest configuration found, exiting.")

    ollama_ctx = ollama.Client(host=config.llm.HOST)
    
    # Check for command line arguments
    args = sys.argv[1:]
    
    if "--skip-dedup" in args or "-d" in args:
        skip_dedup = True
        print("⏭️  Skipping deduplication check...")
    else:
        skip_dedup = False
    
    if "--cleanup" in args or "-c" in args:
        orphan_count = cleanup_orphaned_chunks(config)
        print(f"\n✅ Cleanup complete. Removed {orphan_count} orphaned records.\n")
    
    if "--verify" in args or "-v" in args:
        verify_integrity()
        return
    
    ingest_documents(skip_dedup=skip_dedup)

if __name__ == "__main__":
    main()
