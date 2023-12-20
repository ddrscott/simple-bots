"""
This module provides a simple interface for loading bot data from YAML files in $BOTS_DIR.
"""
import os
from typing import List, Optional
from glob import glob
import yaml
from functools import lru_cache
from copy import deepcopy
from pydantic import BaseModel, Extra

bot_path = os.environ.get('BOTS_DIR', "bots")

class Bot(BaseModel, extra=Extra.allow):
    path: str
    base: str
    title: str
    messages: list = []
    body: Optional[str] = None
    model_kwargs: Optional[dict] = None

def all_bots() -> List[Bot]:
    files = [f for ext in ('*.yml', '*.yaml', '*.md') for f in glob(os.path.join(bot_path, ext))]
    return [
        Bot(**{
            'path': path,
            'base': os.path.basename(path).split(".")[0],
            'title': os.path.basename(path).split(".")[0].replace("-", " ").title(),
            'messages': [],
            'css': None,
            **parse_yaml_with_headers(path)
        }) for path in files
    ]

def parse_yaml_with_headers(path) -> dict:
    """Parse a YAML file with a header section.
    The header section is separated from the body by a line containing three dashes.
    If a body is included it will be added to the messages as a system prompt
    """
    try:
        contents = open(path).read()
        parts = contents.split('---', 1)
        header = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else None
        # Parse the YAML header
        data = yaml.safe_load(header)
        # Combine the header data with the body in a dictionary
        data = data or {}
        if 'messages' not in data:
            data['messages'] = []
        if body:
            data['body'] = body
            data['messages'].append({'role': 'system', 'content': body})
        return data
    except Exception as e:
        raise Exception(f"Error parsing YAML file: {path}") from e

@lru_cache
def bot_dict() -> dict[str, Bot]:
    return {b.base: b for b in all_bots()}

def bot_base(base) -> Bot:
    return deepcopy(bot_dict()[base])
