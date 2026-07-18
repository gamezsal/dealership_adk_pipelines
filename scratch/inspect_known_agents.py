file_path = "c:/Users/gamez/Documents/dealership_adk_pipelines/frontend/node_modules/@copilotkit/core/dist/index.mjs"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.splitlines()
start = 985
end = 1115
for j in range(start, end):
    print(f"{j+1:4d}: {lines[j]}")
