import os

search_dir = "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/core"
query = "ProxiedCopilotRuntimeAgent"

print(f"Searching for '{query}' in {search_dir}...")
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(('.js', '.mjs')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if query in content:
                    print(f"Found in {path}")
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if query in line and ("class" in line or "=" in line):
                            print(f"  Line {i+1}: {line[:160]}")
            except Exception as e:
                pass
