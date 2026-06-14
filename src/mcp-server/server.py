from __future__ import annotations
import signal
import atexit
import sys
import os
import ollama
from typing import Any, Optional
from chromadb import Client, Collection
from src.core.config import get_db_options, DbOption, QueryOption, get_llm_options, LlmOption, get_server_options, ServerOption
from src.core.db import db_init, db_init_hc
from mcp.server.fastmcp import FastMCP


ENV_SERVER_HOST = os.getenv("FASTMCP_HOST", "127.0.0.1")
ENV_SERVER_PORT = os.getenv("FASTMCP_PORT", "8000")
# Initialize MCP
mcp = FastMCP("Unity-API", host=ENV_SERVER_HOST, port=int(ENV_SERVER_PORT), stateless_http=True)

# Globals
db_config: Optional[DbOption] = None
llm_config: Optional[LlmOption] = None
server_config: Optional[ServerOption] = None
db_ctx: Optional[Any] = None
collection: Optional[Collection] = None
ollama_ctx: Optional[Any] = None

@mcp.tool()
def search_unity_api(query: str) -> str:
    """
    Search the Unity API documentation. 
    """
    if not ollama_ctx:
        return "Error: Ollama not initialised"
    if not collection:
        return "Error: ChromaDB collection unavailable"

    try:
        # Generate Embedding for the query using Ollama
        # This MUST match the model used during ingestion
        response = ollama_ctx.embed(model=llm_config.MODEL_NAME, input=[query])
        query_embedding = response["embeddings"][0]

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        if not results['documents'][0]:
            return "No matching documentation found."

        # Format for the Agent
        output = [f"### Results for: {query}\n"]
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source = meta.get('source', 'Unknown')
            output.append(f"**Source File:** {source}\n{doc}\n{'-'*20}")

        return "\n".join(output)

    except Exception as e:
        return f"Error accessing Unity Docs: {str(e)}"

def _handle_shutdown(signum, frame):
    _db_cleanup()
    sys.exit(0)

def _db_cleanup():
    global db_ctx, collection
    try:
        if db_ctx:
            if hasattr(db_ctx, "close"):
                db_ctx.close()
            elif hasattr(db_ctx, "__exit__"):
                pass
        print("Database connection closed")
    except Exception as e:
        print(f"Error during DB Cleanup: {e}")

def main():
    print(f"[Server] Init")

    global db_config, llm_config, server_config, db_ctx, collection, ollama_ctx

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)
    atexit.register(_db_cleanup)

    llm_config = get_llm_options()
    if not llm_config:
        print(f"Error Loading LllmOption Configuration")

    db_config = get_db_options()
    if not db_config:
        print(f"Error Loading DbOption Configuration") 
        return

    server_config = get_server_options()
    if not server_config:
        print(f"Error Loading ServerOption Configuration")
        return

    if llm_config.HOST:
        ollama_ctx = ollama.Client(host=llm_config.HOST)

    db_ctx, collection = db_init(db_config)
    print(f"Connected to ChromaDB collection {collection.name}")

    if db_ctx and collection:
        print(f"MCP server has started on {server_config.HOST}:{server_config.PORT} using transport[{server_config.TRANSPORT}]")   
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
