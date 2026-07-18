import inspect
from ag_ui_adk.adk_agent import ADKAgent

lines, start_line = inspect.getsourcelines(ADKAgent.run)
for idx, line in enumerate(lines[:120]):
    print(f"{idx+1:3d}: {line}", end="")
