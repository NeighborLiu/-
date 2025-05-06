import json
import os

def generate_camel_tools():
    with open('new_envs_v2.jsonl', 'r') as file:
        lines = file.readlines()
    
    toolkits = {}
    for line in lines:
        data = json.loads(line)
        toolkit_name = data.get('toolkit_name')
        description = data.get('description')
        
        if toolkit_name and description:
            if toolkit_name not in toolkits:
                toolkits[toolkit_name] = description
    
    markdown_content = ""
    for toolkit_name, description in toolkits.items():
        markdown_content += f"| {toolkit_name} | {description} |\n"
    
    with open('camel_tools.md', 'w') as file:
        file.write(markdown_content)

if __name__ == "__main__":
    generate_camel_tools()