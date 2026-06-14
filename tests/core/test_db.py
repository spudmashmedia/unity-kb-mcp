import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.core.db import build_metadata, db_init
from src.core.config import DbOption

@pytest.fixture
def mock_dboption() -> DbOption:
    mock_config = DbOption()
    mock_config.METADATA_VERSION = "4.2"
    return mock_config

@pytest.fixture
def mock_dboption_empty() -> DbOption:
    mock_config = DbOption()
    # mock_config.METADATA_VERSION = "4.2"
    return mock_config


def test_build_metadata_when_4_2_should_be_4_2(mock_dboption):
    sut = build_metadata(mock_dboption)
    assert sut != None
    assert sut["version"] != None
    assert sut["version"] == "4.2"

def test_build_metadata_when_empty_should_be_1_0(mock_dboption_empty):
    sut = build_metadata(mock_dboption_empty)
    assert sut != None
    assert sut["version"] == "1.0"

