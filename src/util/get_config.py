import json
from src.util.project_path import CONFIG_FILE

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
