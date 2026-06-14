import tomllib
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
import os
from dotenv import load_dotenv

# ============================================================================
# Configuration
# ============================================================================
class DbOption(BaseModel):
    DB_NAME: str=""
    COLLECTION_NAME: str=""
    METADATA_USE: bool = False
    METADATA_VERSION: str = "1.0"    
    LOCAL_DB: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000

class IngestOption(BaseModel):
    DOC_PATHS: list[str]=[]
    CLEAN_ALG: str="traf"
    BATCH_SIZE: int=10
    ARCHIVE_PATH: str=""
    STATE_FILE_NAME: str="ingestion_state.json"

class LlmOption(BaseModel):
    MODEL_NAME: str=""
    HOST: str = "127.0.0.1"
    PORT: int = 11434

class QueryOption(BaseModel):
    RESPONSE_TYPE: str= "embeddings"
    TOTAL_RESULTS: int = 30
    CONTENT_LENGTH: int = 200
    SIMILARITY_THRESHOLD: float = 0.0

class FormatOption(BaseModel):
    ENABLE_MARKDOWN: bool = True
    ENABLE_HTML: bool = True
    ALLOWED_EXTENSIONS: list[str] = []
    FORMAT_FALLBACK: str = "traf"

class ServerOption(BaseModel):
    TRANSPORT: str = ""
    HOST: str = ""
    PORT: str = ""

class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    
    db: DbOption = DbOption()
    ingest: IngestOption = IngestOption()
    llm: LlmOption = LlmOption()
    query: QueryOption = QueryOption()
    formats: FormatOption = FormatOption()
    server: ServerOption = ServerOption()
    debug: bool = False

def get_config_path() -> Path:
    load_dotenv()
    env_profile = os.getenv("APP_ENV", "local")

    root_dir = Path(__file__).parent.parent.parent
    pyproject_config_path = root_dir/ "pyproject.toml"
    profile_config_path = root_dir / "config" / f"config_{env_profile}.toml"
    base_config_path = root_dir / "config" / "config.toml"

    target_config_path = None
    
    if pyproject_config_path.exists():
        target_config_path = pyproject_config_path
    elif profile_config_path.exists():
        target_config_path = profile_config_path
    elif base_config_path.exists():
        target_config_path = base_config_path
    else:
        raise FileNotFoundError(f"No configuration file found. Check {root_dir}/config/ and {root_dir}/pyproject.toml")

    return target_config_path

def get_appconfig() -> Optional[AppConfig]:

    config_path = get_config_path()
              
    try:
        with config_path.open("rb") as f:
            full_config = tomllib.load(f)
            
            # If using pyproject.toml, dig into the tool namespace
            if "tool" in full_config and "unity_kb_mcp" in full_config["tool"]:
                return AppConfig(**full_config["tool"]["unity_kb_mcp"])
            
            return AppConfig(**full_config)
            
    except FileNotFoundError:
        print(f"⚠️ Config file not found at: {config_path.absolute()}")
        return None
    except tomllib.TOMLDecodeError as e:
        print(f"⚠️ Error parsing TOML at {config_path}: {e}")
        return None

# Helpers for quick access
def get_db_options() -> Optional[DbOption]:
    env = get_appconfig()
    return env.db if env else None

def get_ingest_options() -> Optional[IngestOption]:
    env = get_appconfig()
    return env.ingest if env else None

def get_llm_options() -> Optional[LlmOption]:
    env = get_appconfig()
    return env.llm if env else None

def get_query_options() -> Optional[QueryOption]:
    env = get_appconfig()
    return env.query if env else None

def get_server_options() -> Optional[ServerOption]:
    env = get_appconfig()
    return env.server if env else None
