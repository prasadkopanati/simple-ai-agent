import os
# import sys
import logging
from typing import Dict, Any, List
from anthropic import Anthropic
from pydantic import BaseModel
# from tools.read_file import read_file
# from tools.list_files import list_files
# from tools.edit_file import edit_file


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent.log")]
)

# Suppress verbose logging from HttpCore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class AIAgent:
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.messages: List[Dict[str, Any]] = []
        self.tools: List[Tool] = []
        self._setup_tools()
        # print("Agent Tools initialized ", len(self.tools))

    def _setup_tools(self):
        self.tools = [
            Tool(
                name="read_file",
                description="Read a file from the filesystem",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="list_files",
                description="Read a directory from the filesystem",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the directory to list",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name="edit_file",
                description="Edit a file in the filesystem",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to replace",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The text to replace the old text with",
                        },
                    },
                    "required": ["path", "new_text"],
                },
            ),
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input.get("old_text", ""),
                    tool_input["new_text"],
                )
            else:
                return f"Tool {tool_name} not found"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    def _read_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                return f"File is at path {path} and content is {content}"
        except FileNotFoundError:
            return f"File {path} not found"
        except Exception as e:
            return f"Error reading file {path}: {str(e)}"

    def _list_files(self, path: str) -> str:
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

    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        try:
            if os.path.exists(path):
                if old_text:
                    # Edit existing file by replacing old_text with new_text
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                    if old_text not in content:
                        return f"Old text not found in file {path}"

                    content = content.replace(old_text, new_text)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)

                    return f"File {path} edited successfully"
                else:
                    # Do nothing; Overwrite existing file with new_text is not recommended
                    #with open(path, "w", encoding="utf-8") as f:
                    #    f.write(new_text)
                    return f"File {path} unchanged since no text provided to search and replace"
            else:
                # Create new file
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

                return f"Successfully created {path}"
        except Exception as e:
            return f"Error editing file {path}: {str(e)}"

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        logging.info(f"User input: {user_input}")

        tool_schemas = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools
        ]

        while True:
            try:
                response = self.anthropic.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    tools=tool_schemas,
                    system="You are AvacadoAgent, an AI assistant that can use tools to interact with the filesystem. Do not respond in asterisks. You operate within a terminal environment. Output only plain text without markdown formatting, as your responses are displayed directly in the terminal.",
                    messages=self.messages,
                )

                assistant_message = {"role": "assistant", "content": []}
                for content in response.content:
                    if content.type == "text":
                        assistant_message["content"].append(
                            {"type": "text", "text": content.text}
                        )
                        logging.info(f"Assistant message: {content.text}")

                    elif content.type == "tool_use":
                        assistant_message["content"].append(
                            {
                                "type": "tool_use",
                                "id": content.id,
                                "name": content.name,
                                "input": content.input,
                            }
                        )
                        logging.info(f"Assistant tool use: {content.name}, {content.input}")

                self.messages.append(assistant_message)

                tool_results = []
                for content in response.content:
                    if content.type == "tool_use":
                        result = self._execute_tool(content.name, content.input)
                        tool_results.append(
                            {
                                "tool_use_id": content.id,
                                "type": "tool_result",
                                "content": result,
                            }
                        )

                if tool_results:
                    self.messages.append({"role": "user", "content": tool_results})
                else:
                    #logging.info(f"Assistant message: {response.content[0].text[0:100] + '...' if response.content else ''}")
                    logging.info(f"Assistant message: {response.content[0].text if response.content else ''}")
                    return response.content[0].text if response.content else ""
            except Exception as e:
                return f"Error in chat: {str(e)}"


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    agent = AIAgent(api_key)
    print("Agent initialized", len(agent.tools))
    # files = agent._list_files(os.getcwd())
    # print(files)
    # print("Ai-Agent! Starting...")
    # fileContent = agent._read_file("main.py")
    # print(fileContent)
    # newFileContent = agent._edit_file("new.txt", "Hello, world! This is a test.", "New text")
    # print(newFileContent)

    print("Chatting...")
    print("================================================")
    print("Avacado Agent is ready to chat!")
    print("Type 'exit', 'quit', or 'bye' to end the chat")
    print("Type 'help' to see available commands")
    print("================================================")

    while True:
        try: 
            user_input = input("You> ").strip() 
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            if not user_input.strip():
                continue

            print("\nAssistant> ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            logging.error(f"Error in chat: {str(e)}")
            print("================================================")

if __name__ == "__main__":
    main()
