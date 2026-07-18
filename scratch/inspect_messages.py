from ag_ui.core import ToolCall, FunctionCall
import pprint

print("ToolCall fields:")
pprint.pprint(ToolCall.model_fields)

print("\nFunctionCall fields:")
pprint.pprint(FunctionCall.model_fields)
