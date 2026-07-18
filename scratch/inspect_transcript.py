import json
import os

transcript_path = "C:/Users/gamez/.gemini/antigravity-ide/brain/418b6a29-27a6-43a5-bfe0-866440841404/.system_generated/logs/transcript_full.jsonl"

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            # Find the browser subagent's step 118 content
            content = data.get("content", "")
            if "Step 118:" in content or (data.get("step_index") == 450 and "Step 118" in content):
                print(f"Step {data.get('step_index')}:")
                print(content[:2000])
                print("="*60)
        except Exception as e:
            pass
