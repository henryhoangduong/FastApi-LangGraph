import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import structlog

from core.config import Environment, settings

settings.LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_file_path() -> Path:
    env_prefix = settings.ENVIRONMENT.value
    return settings.LOG_DIR / f"{env_prefix}-{datetime.now().strftime('%Y-%m-%d')}.jsonl"


class JsonlFileHandler(logging.Handler):
    def __init__(self, level = 0):
        super().__init__(level)
        
    