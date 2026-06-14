# Prerequisite
## Python Virtual environment
```sh
  python3 -m venv bdb_env
```

## Install Dependencies

### LLM
Have Ollama installed (https://ollama.com/)
This will be used for ingestion pipeline. (See Ingestion Pipeline)

Pull Qwen3-embedding model:
```sh
ollama pull qwen3-embedding:0.6b
```

### Python
#### main
```sh
  pip install .
```

#### dev
```sh
  pip install -e ".[dev]"
```

### Run Tests
```sh
  pytest tests/ -v
```

---
Spudmash Media [-] 2026
