from .config import DbOption, get_db_options
from typing import Optional, Tuple, Any
import chromadb


# ============================================================================
# Database Initialization
# ============================================================================

def build_metadata(config: DbOption) -> Optional[dict[str, Any]]:
    """Build metadata dictionary from config."""
    metadata: dict[str, Any] = {}
    
    if config and config.METADATA_VERSION:
        metadata["version"] = str(config.METADATA_VERSION)
    
    return metadata

def db_init(config: DbOption) -> Tuple[Any, Any]:
    """Initialize ChromaDB client and collection."""
    path = config.DB_NAME
    collection_name = f"{config.COLLECTION_NAME}_{config.METADATA_VERSION}"

    if config.LOCAL_DB == True:
        db_ctx = chromadb.PersistentClient(path=path)
        collection = db_ctx.get_or_create_collection(name=collection_name)
    else:
        db_ctx = chromadb.HttpClient(host=config.HOST, port=int(config.PORT), ssl=False)
        collection = db_ctx.get_or_create_collection(name=collection_name)
    
    return db_ctx, collection

def db_init_hc(config: DbOption) -> Tuple[Any, Any]:
    """Initialize ChromaDB client and collection."""
    path = config.DB_NAME
    collection_name = f"{config.COLLECTION_NAME}_{config.METADATA_VERSION}"

    print(f"DEBUG: host:{config.HOST}, port:{config.PORT}")
    
    db_ctx = chromadb.HttpClient(host=config.HOST, port=int(config.PORT), ssl=False)
    collection = db_ctx.get_or_create_collection(name=collection_name)
    
    return db_ctx, collection

