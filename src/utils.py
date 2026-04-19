import re

import yaml


def extract_yml_path(text):
    match = re.search(r"\(([^)]+\.yml)\)", text)
    if match:
        yml_path = match.group(1)
        return yml_path
    return None


def read_yml_file(yml_path) -> dict:
    with open(yml_path, "r") as file:
        data = yaml.safe_load(file)
    return data


def extract_page_tree(text: str | None = None) -> tuple[str | None, dict | None]:
    if text:
        snapshot_path = extract_yml_path(text)
        page_tree = read_yml_file(snapshot_path)
    else:
        # invoke tool to get page tree
        snapshot_path = None
        page_tree = None

    return snapshot_path, page_tree
