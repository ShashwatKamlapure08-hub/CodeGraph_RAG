import os
import json
import re
from typing import List, Dict, Any
from groq import Groq
from vector_store import CodeVectorStore
from retriever import GraphAugmentedRetriever

class ReActRepoAgent:
    # Set default model to an active model present in your API key's model list
    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing. Set it before running.")
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.vector_store = CodeVectorStore()
        self.retriever = GraphAugmentedRetriever(self.vector_store)

    def _format_context(self, context_items: List[Dict[str, Any]]) -> str:
        """Formats retrieved context snippets for agent observation."""
        formatted = ""
        for idx, item in enumerate(context_items, 1):
            formatted += f"\n[Doc {idx}] Symbol: {item['symbol_name']} | File: {item['file_path']} (Lines {item['start_line']}-{item['end_line']})\n"
            if item.get("context_dependencies"):
                formatted += f"Graph Relations: {', '.join(item['context_dependencies'])}\n"
            formatted += f"Snippet:\n{item['text']}\n"
        return formatted

    def run(self, query: str, max_turns: int = 3) -> str:
        """Executes the ReAct (Thought -> Action -> Observation) agent decision loop."""
        initial_context = self.retriever.graph_augmented_search(query, top_k=2)
        observation = self._format_context(initial_context)

        system_prompt = """You are RepoMind, an expert AST-aware ReAct code agent.
You solve software engineering queries using an iterative Thought -> Action -> Observation loop.

Available Actions:
1. Action: SEARCH[<keyword>] - Queries the code vector database for additional symbols or functions.
2. Action: FINAL_ANSWER[<solution>] - Outputs your final technical reasoning and code fix.

Rules:
- You MUST output 'Thought:' followed by your reasoning.
- You MUST then output an 'Action:' on a new line.
- Do NOT generate an Observation yourself. The system provides Observations."""

        conversation_history = f"User Query: {query}\n\nInitial Observation:\n{observation}\n"

        for turn in range(max_turns):
            prompt = f"{system_prompt}\n\nConversation Trajectory:\n{conversation_history}"

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strict ReAct software engineering agent."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=0.1,
                max_tokens=1000
            )

            agent_output = response.choices[0].message.content
            print(f"\n--- [TURN {turn + 1}] AGENT TRAJECTORY ---")
            print(agent_output)

            if "FINAL_ANSWER[" in agent_output or "Action: FINAL_ANSWER" in agent_output:
                return agent_output

            search_match = re.search(r"Action:\s*SEARCH\[(.*?)\]", agent_output, re.IGNORECASE)
            if search_match:
                search_keyword = search_match.group(1).strip()
                print(f"\n[System Tool Executing] Searching vector graph for: '{search_keyword}'")
                
                new_context = self.retriever.graph_augmented_search(search_keyword, top_k=2)
                new_observation = self._format_context(new_context)
                
                conversation_history += f"\n{agent_output}\nObservation:\n{new_observation}\n"
            else:
                conversation_history += f"\n{agent_output}\n"

        return agent_output


if __name__ == "__main__":
    agent = ReActRepoAgent()
    user_query = "How are function calls extracted across files and mapped into graph edges?"
    
    print("==================================================")
    print("              REACT AGENT EXECUTION               ")
    print("==================================================")
    final_result = agent.run(user_query)
