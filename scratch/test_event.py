import inspect
from copilotkit.langgraph_agui_agent import LangGraphAGUIAgent

print("LangGraphAGUIAgent._handle_single_event signature:")
print(inspect.signature(LangGraphAGUIAgent._handle_single_event))
print("\nLangGraphAGUIAgent._handle_single_event source code:")
print(inspect.getsource(LangGraphAGUIAgent._handle_single_event))
