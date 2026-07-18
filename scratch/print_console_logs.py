import json
import os

transcript_path = "C:/Users/gamez/.gemini/antigravity-ide/brain/418b6a29-27a6-43a5-bfe0-866440841404/.system_generated/logs/transcript_full.jsonl"

print_next = False
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if print_next:
                print(f"--- System Response (Step {data.get('step_index')}) ---")
                print(data.get("content")[:1000])
                print("="*60)
                print_next = False
            
            tool_calls = data.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "capture_browser_console_logs":
                    print(f"Tool call capture_browser_console_logs in Step {data.get('step_index')}")
                    print_next = True
        except Exception as e:
            pass
