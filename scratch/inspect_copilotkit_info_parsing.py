import os

search_dirs = [
    "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/react-core/dist",
    "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/shared/dist"
]

for search_dir in search_dirs:
    if not os.path.exists(search_dir):
        continue
    print(f"Searching in {search_dir}...")
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith(('.js', '.mjs')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if "/info" in content:
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "/info" in line and ("fetch" in line or "fetchInfo" in line or "sync" in line or "agents" in line):
                                print(f"Found in {path} Line {i+1}: {line[:160]}")
                except Exception as e:
                    pass
