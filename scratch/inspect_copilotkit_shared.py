import os

search_dir = "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/shared/dist"
query = "DEFAULT_AGENT_ID"

print(f"Searching for {query}...")
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(('.js', '.mjs')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if query in content:
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if query in line and "=" in line:
                            print(f"Found in {path} Line {i+1}: {line[:120]}")
            except Exception as e:
                pass
