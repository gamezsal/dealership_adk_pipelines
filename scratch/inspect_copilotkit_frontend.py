import os

search_dir = "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/react-core"
query = "agent"

print(f"Searching for props containing 'agent'...")
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith('.d.ts'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "agent" in content or "agentId" in content:
                        print(f"Found in {path}")
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "agent" in line or "agentId" in line:
                                print(f"  Line {i+1}: {line[:120]}")
            except Exception as e:
                pass
