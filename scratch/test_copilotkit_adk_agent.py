import sys
import os
import uuid
import json
import asyncio

# Add project root to path
sys.path.append(os.path.abspath('.'))

from ag_ui.core import (
    RunAgentInput, UserMessage, AssistantMessage, SystemMessage, ToolMessage,
    ToolCall, FunctionCall
)
from ag_ui_adk import ADKAgent
from agents.agent import root_agent

class CopilotKitADKAgent(ADKAgent):
    async def execute(
        self,
        *,
        state: dict,
        thread_id: str,
        messages: list,
        actions: list = None,
        node_name: str = None,
        config: dict = None,
        meta_events: list = None,
        **kwargs,
    ):
        ag_ui_messages = []
        for msg in messages:
            role = msg.get("role")
            msg_id = msg.get("id", str(uuid.uuid4()))
            
            if role == "user":
                ag_ui_messages.append(
                    UserMessage(
                        id=msg_id,
                        content=msg.get("content") or "",
                        role="user"
                    )
                )
            elif role == "system":
                ag_ui_messages.append(
                    SystemMessage(
                        id=msg_id,
                        content=msg.get("content") or "",
                        role="system"
                    )
                )
            elif role == "assistant":
                if "name" in msg and "arguments" in msg:
                    tool_call_id = msg.get("id")
                    tool_name = msg.get("name")
                    arguments = msg.get("arguments")
                    if isinstance(arguments, dict):
                        arguments = json.dumps(arguments)
                    
                    tool_calls = [
                        ToolCall(
                            id=tool_call_id,
                            type="function",
                            function=FunctionCall(name=tool_name, arguments=arguments)
                        )
                    ]
                    ag_ui_messages.append(
                        AssistantMessage(
                            id=msg_id,
                            content="",
                            role="assistant",
                            tool_calls=tool_calls
                        )
                    )
                else:
                    tool_calls_list = []
                    for tc in msg.get("toolCalls") or []:
                        args = tc.get("args") or tc.get("arguments")
                        if isinstance(args, dict):
                            args = json.dumps(args)
                        tool_calls_list.append(
                            ToolCall(
                                id=tc.get("id"),
                                type="function",
                                function=FunctionCall(name=tc.get("name"), arguments=args)
                            )
                        )
                    ag_ui_messages.append(
                        AssistantMessage(
                            id=msg_id,
                            content=msg.get("content") or "",
                            role="assistant",
                            tool_calls=tool_calls_list if tool_calls_list else None
                        )
                    )
            elif role == "tool" or "actionExecutionId" in msg:
                tool_call_id = msg.get("actionExecutionId") or msg.get("id")
                result = msg.get("result") or msg.get("content") or ""
                ag_ui_messages.append(
                    ToolMessage(
                        id=msg_id,
                        content=result,
                        role="tool",
                        tool_call_id=tool_call_id
                    )
                )

        run_input = RunAgentInput(
            thread_id=thread_id,
            run_id=str(uuid.uuid4()),
            state=state or {},
            messages=ag_ui_messages,
            tools=[],
            context=[],
            forwarded_props=None,
        )

        async for event in self.run(run_input):
            encoded = event.model_dump_json(by_alias=True, exclude_none=True)
            yield encoded

async def test():
    agent = CopilotKitADKAgent(root_agent)
    agent.name = "default"
    
    # Try calling execute with a simple user message and initialized state
    messages = [{"role": "user", "content": "hi", "id": "msg-1"}]
    print("Executing agent with state...")
    async for event in agent.execute(state={"current_step": "EXTRACTING"}, thread_id="test-thread-id", messages=messages):
        print(f"Event: {event}")

if __name__ == "__main__":
    asyncio.run(test())
