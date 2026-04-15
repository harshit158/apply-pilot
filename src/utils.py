import re
import yaml

def extract_yml_path(text):
    match = re.search(r'\(([^)]+\.yml)\)', text)
    if match:
        yml_path = match.group(1)
        return yml_path
    return None

def read_yml_file(yml_path) -> dict:
    with open(yml_path, 'r') as file:
        data = yaml.safe_load(file)
    return data