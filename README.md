# unity-kb-mcp

[![Tech](https://skillicons.dev/icons?i=py,fastapi,unity,docker)](https://skillicons.dev)
Unity Knowledge Base Document Ingest + MCP Server

## Summary
An MCP Server that provides Retrieval-Augmented Generation (RAG) capabilities to surface the latest Unity API documentation (currently v6.x). It is designed specifically for local usage with:
- **Inference Engines** (LM Studio, Ollama UI etc...)
- **LLM Harnesses** (OpenCode, ClaudeCode etc...)

Docker Services Include:
- **MCP Server**: built with FastMCP library.
- **Vector Database Server**: ChromaDB instance with Unity API Knowledge Base
- **Ingest Pipeline**: Python data ingest reading HTML + Markdown documentation and writing to ChromaDB
- **LLM Inference Engine Server**: Ollama instance using Qwen3-embedding:0.6b embedding model

# Getting Started
- [Prequisite Before Starting](/docs/prerequisite.md)
- [Ingestion Pipeline](/docs/ingestion_pipeline.md)
- [MCP Server](/docs/mcp_server.md)
- [Setup Tooling](/docs/setup_tooling.md)
  
# Documentation
  
- [The Purpose of this Repository](/docs/purpose.md)
- [References](/docs/references.md)

# License
This code is distributed under the terms and conditions of the [MIT License](/LICENSE)

---
Spudmash Media [-] 2026
