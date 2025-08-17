import os
import json


def write_json(data, file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(file_path: str, default_value: dict | list | None = None):
    if not exists_file(file_path):
        return default_value

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_text(text: str, file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def exists_file(file_path):
    return os.path.exists(file_path)
