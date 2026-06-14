import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.core.config import AppConfig, DbOption, IngestOption, LlmOption, QueryOption, FormatOption, get_appconfig, get_db_options, get_llm_options, get_ingest_options, get_query_options

@pytest.fixture
def mock_pyproject_toml():
    return {
        "tool": {
            "unity_kb_mcp": {
                "db": {
                    "DB_NAME": "test_db",
                    "COLLECTION_NAME": "test_collection",
                    "METADATA_USE": False,
                    "METADATA_VERSION": "9001"
                },
                "llm": {
                    "MODEL_NAME": "rx-78"
                },
                "query": {
                    "RESPONSE_TYPE": "embeddings",
                    "TOTAL_RESULTS": 10,
                    "CONTENT_LENGTH": 9001,
                    "SIMILARITY_THRESHOLD": 0.01
                },
                "ingest": {
                    "DOC_PATHS": [
                        "/tmp/kb/1",
                        "/tmp/kb/2",
                        "/tmp/kb/3",
                    ],
                    "CLEAN_ALG": "traf",
                    "BATCH_SIZE": 4
                },
                "formats": {
                    "ENABLE_MARKDOWN": True,
                    "ENABLE_HTML": True,
                    "ALLOWED_EXTENSIONS": [
                        ".html",
                        ".md"
                    ],
                }
            }
        }        
    }

@patch.object(Path, "exists", side_effect=[False, True])
@patch("src.core.config.tomllib.load")
def test_get_env_returns_appconfig(mock_load, mock_path_exists, mock_pyproject_toml):
        mock_load.return_value = mock_pyproject_toml
        result = get_appconfig()
        assert isinstance(result, AppConfig)
        assert result.db.DB_NAME == "test_db"
        assert result.db.COLLECTION_NAME == "test_collection"
        assert result.db.METADATA_USE == False
        assert result.db.METADATA_VERSION == "9001"

@patch.object(Path, "exists", side_effect=[False, True])
@patch("src.core.config.tomllib.load")
def test_get_db_options(mock_load, mock_path_exists, mock_pyproject_toml):
        mock_load.return_value = mock_pyproject_toml
        result = get_db_options()
        assert isinstance(result, DbOption)
        assert result.DB_NAME == "test_db"
        assert result.COLLECTION_NAME == "test_collection"
        assert result.METADATA_USE == False
        assert result.METADATA_VERSION == "9001"

@patch.object(Path, "exists", side_effect=[False, True])
@patch("src.core.config.tomllib.load")
def test_get_llm_options(mock_load, mock_path_exists, mock_pyproject_toml):
        mock_load.return_value = mock_pyproject_toml
        result = get_llm_options()
        assert isinstance(result, LlmOption)
        assert result.MODEL_NAME == "rx-78"


@patch.object(Path, "exists", side_effect=[False, True])
@patch("src.core.config.tomllib.load")
def test_get_ingest_options(mock_load, mock_path_exists, mock_pyproject_toml):
        mock_load.return_value = mock_pyproject_toml
        result = get_ingest_options()
        assert isinstance(result, IngestOption)
        assert result.DOC_PATHS == [
                        "/tmp/kb/1",
                        "/tmp/kb/2",
                        "/tmp/kb/3",
                    ] 
        assert result.CLEAN_ALG == "traf" 
        assert result.BATCH_SIZE == 4


@patch.object(Path, "exists", side_effect=[False, True])
@patch("src.core.config.tomllib.load")
def test_get_query_options(mock_load, mock_path_exists, mock_pyproject_toml):
        mock_load.return_value = mock_pyproject_toml
        result = get_query_options()
        assert isinstance(result, QueryOption)
        assert result.RESPONSE_TYPE == "embeddings" 
        assert result.TOTAL_RESULTS == 10
        assert result.CONTENT_LENGTH == 9001
        assert result.SIMILARITY_THRESHOLD == 0.01 
