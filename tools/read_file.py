def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            return f"File is at patj {path} and content is {content}"
    except FileNotFoundError:
        return f"File {path} not found"
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"