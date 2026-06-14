# The Purpose of this Repository 
![why](/docs/img/why.jpg)

The majority of the repositories at Spudmash Media serve as Quickstart templates for your next software build.

## Project Objectives
- Build a reusable RAG MCP Server to assist local LLM models build Unity C# scripts whether used with an Inference Engine [LM Studio](https://lmstudio.ai/) or an Agent Harness [OpenCode](https://opencode.ai/)
- Load latest Unity API knowledge into that RAG system's knowledge base
- Also load personalised project data

## Development Workflow
This repository is developed using:
- **Multiplexer**: tmux
- **Shell**: fish
- **Editor**: Helix (via LSP)
- **Language Standard**: Python
- **Inference Engine**: Ollama & LM Studio
- **Agent Harness**: OpenCode
- **Containerisation**: Docker Desktop

## Thoughts

I had been using OpenCode with a customised LLM with 35b parameters as my personal agent and for the most part it is quite knowledgable in software architecture, coding syntax for all the standard languages.
However once we venture into the Game Development stack and 3D content creation tool building there's gaps with it's knowledge.

Two ways to solve the knowledge gap is:
- Retrain a new specialised LLM with everything Unity OR
- Create a Model Context Protocol (MCP) tool with Retrieval-Augmented Generation (RAG capabilities with all the Unity docs + anything personal project related documentation.

The RAG method is quite literally like adding a new lobe to the LLM Model and choice for this project.
Context Window is also a consideration for choosing RAG - for my system (M1 Max 64GB), a comfortable model that is still compliant is 35b which uses 20GB, which leaves enough headroom to increase the context window to 49152 tokens.

## Is It Worth the Hassle? 🧐

Most definitely worth it! The project created a generic RAG ingestion pipeline that can be cloned and reused for other knowledge bases.
Having local LLMs that can run completely offline with personalised data that will never leave your network is end goal for data sovereignty.

However in order for this MCP Tool to be useful you need more data to help the 35b model calibrate and be better at assisting with Unity API coding.

---
Spudmash Media [-] 2026

