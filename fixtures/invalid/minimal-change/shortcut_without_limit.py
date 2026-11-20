def find_first(items, key):
    # shortcut: linear scan
    return next(item for item in items if item.key == key)
