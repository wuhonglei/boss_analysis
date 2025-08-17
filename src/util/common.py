def get_nested_value(obj: dict, key: str):
    """获取嵌套字典的值"""
    keys = key.split('.')
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj
