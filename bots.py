import os
from glob import glob
import yaml
from functools import lru_cache
import datetime

bot_path = os.environ.get('BOTS_DIR', "bots")

hashes = {
    "currentdate": f"Right now it is {datetime.datetime.now().isoformat()}.",
}

def all_bots():
    return [
        {
            'path': path,
            'title': os.path.basename(path).split(".")[0].replace("-", " ").title(),
            'base': os.path.basename(path).split(".")[0],
            'tokens': [],
            'history': [],
            'css': None,
            'body': '',
            **parse_yaml_with_headers(path)
        }
        for path in sorted(glob(f"{bot_path}/*.yaml"))
    ]

def parse_yaml_with_headers(path):
    """Parse a YAML file with a header section.
    The header section is separated from the body by a line containing three dashes.
    If a body is included it will be added to the history as a system prompt
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
        if 'history' not in data:
            data['history'] = []
        if body:
            data['body'] = body
            data['history'].append({'role': 'system', 'content': body})
        return data
    except Exception as e:
        raise Exception(f"Error parsing YAML file: {path}") from e

@lru_cache
def bot_dict():
    return {b['base']: b for b in all_bots()}

def bot_base(base):
    return bot_dict()[base].copy()
