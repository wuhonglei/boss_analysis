import os
import json


def write_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
