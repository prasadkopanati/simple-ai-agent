import os

def list_files(path: str) -> str:
    try:
        if not os.path.exists(path):
            return f"Path {path} does not exist"

        items = []
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            items.append("Directory: " + item)
        else:
            items.append("File: " + item)
        if not items:
            return "No items found"

        return f"Path {path} contains the following items:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing files {path}: {str(e)}"