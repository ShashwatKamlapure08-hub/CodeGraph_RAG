import os
import re
from typing import Dict, Any
from llm_engine import ReActRepoAgent

class PatchSynthesizer:
    def __init__(self, agent: ReActRepoAgent):
        self.agent = agent

    def generate_patch(self, bug_description: str) -> Dict[str, Any]:
        """Queries the agent for a bug fix and formats the response into a unified git diff."""
        
        context = self.agent.retriever.graph_augmented_search(bug_description, top_k=2)
        
        prompt = f"""Bug / Improvement Request: {bug_description}

Instructions:
1. Explain the bug or fix.
2. Output an EXACT git diff patch inside a ```diff code block.

Example output structure:
```diff
--- a/code_parser.py
+++ b/code_parser.py
@@ -10,3 +10,3 @@
-    docstring = ast.get_docstring(node)
+    docstring = ast.get_docstring(node) or ""
```"""

        raw_response = self.agent.generate_direct_response(prompt, context)
        
        # Extract diff block
        diff_match = re.search(r"```diff\n(.*?)\n```", raw_response, re.DOTALL)
        patch_code = diff_match.group(1) if diff_match else ""

        return {
            "raw_agent_output": raw_response,
            "patch_code": patch_code,
            "has_valid_patch": bool(patch_code)
        }

    def save_patch_file(self, patch_code: str, output_path: str = "fix.patch") -> bool:
        """Saves generated patch code to a .patch file."""
        if not patch_code.strip():
            return False
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(patch_code)
        return True


if __name__ == "__main__":
    agent = ReActRepoAgent()
    synthesizer = PatchSynthesizer(agent)

    test_bug = "The CodeASTParser needs a safety fallback if docstring is missing or None."
    print("==================================================")
    print("            DAY 17 PATCH SYNTHESIS                ")
    print("==================================================")
    
    result = synthesizer.generate_patch(test_bug)
    
    print("\n--- AGENT RESPONSE ---")
    print(result["raw_agent_output"])
    
    if result["has_valid_patch"]:
        synthesizer.save_patch_file(result["patch_code"])
        print("\nPatch saved successfully to 'fix.patch'.")
