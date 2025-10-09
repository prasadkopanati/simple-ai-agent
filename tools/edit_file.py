import os
def edit_file(path: str, old_text: str, new_text: str) -> str: 
    try:
        if os.path.exists(path) and old_text:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            if old_text not in content:
                return f"Old text {old_text} not found in file {path}"
            
            content = content.replace(old_text, new_text)
            with open(path, "w", encoding="utf-8")as f: 
                f.write(content)
            
            return f"File {path} edited successfully"
        else:
        # Create directory if path contains subdir 
            dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

        return f"Successfully created {path}"
    except Exception as e:
        return f"Error editing file {path}: {str(e)}"